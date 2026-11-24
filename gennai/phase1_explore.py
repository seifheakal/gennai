"""Phase 1: load the page once and collect interactive elements with unique locators."""

import logging
import re
import time
from collections import deque
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, sync_playwright

from gennai import GennaiError
from gennai.config import Settings
from gennai.safety import check_url

log = logging.getLogger(__name__)

_JS = """() => {
  const trim = s => (s || '').replace(/\\s+/g, ' ').trim().slice(0, 80);
  const vis = e => {
    const r = e.getBoundingClientRect(), s = getComputedStyle(e);
    // off-screen elements (e.g. skip links shown only on focus) are not clickable as they are
    return r.width > 0 && r.height > 0 && r.right > 0 && r.bottom > 0 &&
      s.visibility !== 'hidden' && s.display !== 'none';
  };
  const labelOf = e => {
    const l = e.labels && e.labels[0];
    if (!l) return '';
    const c = l.cloneNode(true);
    c.querySelectorAll('input,select,textarea,button').forEach(x => x.remove());
    return trim(c.textContent);
  };
  const forms = Array.from(document.forms);
  const out = [];
  const sel = 'input:not([type=hidden]),textarea,select,button,a[href],[role=button]';
  document.querySelectorAll(sel).forEach(e => {
    if (e.disabled || !vis(e)) return;
    const tag = e.tagName.toLowerCase();
    const field = ['input', 'textarea', 'select'].includes(tag);
    const attr = n => e.getAttribute(n);
    out.push({
      tag, type: (attr('type') || (tag === 'input' ? 'text' : '')).toLowerCase(),
      dom_id: e.id || null, name: attr('name'), placeholder: attr('placeholder'),
      aria_label: attr('aria-label'), label: field ? labelOf(e) : '',
      text: trim(tag === 'input' ? e.value : field ? '' : (e.innerText || e.textContent)),
      required: e.required === true, minlength: attr('minlength'), maxlength: attr('maxlength'),
      min: attr('min'), max: attr('max'), pattern: attr('pattern'),
      testid: attr('data-testid'), role: attr('role'),
      form: forms.indexOf(e.form || e.closest('form')),
      options: tag === 'select'
        ? Array.from(e.options).map(o => ({value: o.value, text: trim(o.text)})) : null,
    });
  });
  return out;
}"""

_TYPE_KIND = {
    "email": "email", "number": "number", "tel": "phone", "password": "password",
    "checkbox": "checkbox", "radio": "radio", "text": "text", "search": "text",
    "submit": "button", "button": "button", "reset": "button", "image": "button",
}  # fmt: skip
_NAME_HINTS = (("email", "email"), ("e-mail", "email"), ("phone", "phone"),
               ("mobile", "phone"), ("password", "password"))  # fmt: skip
_ROLE = {
    "button": "button", "link": "link", "checkbox": "checkbox", "radio": "radio",
    "select": "combobox", "number": "spinbutton", "email": "textbox", "phone": "textbox",
    "text": "textbox",
}  # fmt: skip
_BLOCKED_TITLES = ("just a moment", "attention required")
_LINKS_JS = """() => Array.from(document.querySelectorAll('a[href]')).map(a => ({
  href: a.href, text: (a.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 80)}))"""
# crawling only reads pages, but following these could still change state on the site
_RISKY = re.compile(r"log[-_ ]?out|sign[-_ ]?out|delete|remove|destroy|unsubscribe", re.I)
_NON_HTML = (
    ".pdf", ".zip", ".gz", ".tar", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
    ".mp3", ".mp4", ".csv", ".json", ".xml", ".txt", ".doc", ".docx", ".xls", ".xlsx", ".exe",
)  # fmt: skip


def infer_kind(a: dict) -> str:
    """Semantic kind from tag, type, name, id and label ('other' = not testable)."""
    if a["tag"] == "select":
        return "select"
    if a["tag"] == "textarea":
        return "text"
    if a["tag"] == "button" or a.get("role") == "button":
        return "button"
    if a["tag"] == "a":
        return "link"
    kind = _TYPE_KIND.get(a["type"], "other")
    if kind == "text":
        hay = " ".join(filter(None, [a.get("name"), a.get("dom_id"), a.get("label")])).lower()
        kind = next((k for word, k in _NAME_HINTS if word in hay), kind)
    return kind


def _css_ident(s: str) -> str:
    s = re.sub(r"([^\w-])", r"\\\1", s)
    return re.sub(r"^(\d)", lambda m: f"\\3{m.group(1)} ", s)


def candidate_locators(a: dict) -> list[tuple[str, str]]:
    """Ordered (strategy, value): testid, #id, name, role+name, label, placeholder, text."""
    kind = a.get("kind") or infer_kind(a)
    clickable = kind in ("button", "link")
    out: list[tuple[str, str]] = []
    if a.get("testid"):
        out.append(("testid", a["testid"]))
    if a.get("dom_id"):
        out.append(("css", "#" + _css_ident(a["dom_id"])))
    if a.get("name"):
        esc = a["name"].replace("\\", "\\\\").replace('"', '\\"')
        out.append(("css", f'{a["tag"]}[name="{esc}"]'))
    name = a.get("aria_label") or (a.get("text") if clickable else a.get("label"))
    if _ROLE.get(kind) and name:
        out.append((f"role:{_ROLE[kind]}", name))
    if a.get("label") and not clickable:
        out.append(("label", a["label"]))
    if a.get("placeholder"):
        out.append(("placeholder", a["placeholder"]))
    if clickable and a.get("text"):
        out.append(("text", a["text"]))
    return out


def locate(page, strategy, value):
    """Playwright locator for one (strategy, value) candidate. Also embedded in generated tests."""
    if strategy == "testid":
        return page.get_by_test_id(value)
    if strategy == "css":
        return page.locator(value)
    if strategy.startswith("role:"):
        return page.get_by_role(strategy[5:], name=value, exact=True)
    if strategy == "label":
        return page.get_by_label(value, exact=True)
    if strategy == "placeholder":
        return page.get_by_placeholder(value, exact=True)
    return page.get_by_text(value, exact=True)


def _first_line(e: Exception) -> str:
    return (str(e).strip().splitlines() or [type(e).__name__])[0]


def _settle(page: Page, settle_ms: int) -> None:
    start = time.monotonic()
    try:
        page.wait_for_load_state("networkidle", timeout=settle_ms)
    except PlaywrightError:
        log.debug("network did not go idle within %d ms", settle_ms)
    page.wait_for_timeout(max(0, settle_ms - int((time.monotonic() - start) * 1000)))


def normalize_url(url: str) -> str:
    """Dedupe key for a page: lowercase scheme and host, no fragment, sorted query, '/' path."""
    p = urlsplit(url)
    query = urlencode(sorted(parse_qsl(p.query, keep_blank_values=True)))
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or "/", query, ""))


def _origin(url: str) -> tuple:
    p = urlsplit(url)
    scheme = p.scheme.lower()
    return scheme, p.hostname, p.port or {"http": 80, "https": 443}.get(scheme)


def skip_reason(href: str, text: str, origin: tuple) -> str | None:
    """Why a link is not crawled (None = crawl it): other origin, destructive-looking, not HTML."""
    p = urlsplit(href)
    if p.scheme.lower() not in ("http", "https"):
        return "not http(s)"
    if _origin(href) != origin:
        return "other origin"
    if _RISKY.search(p.path + "?" + p.query) or _RISKY.search(text or ""):
        return "looks like logout/delete"
    if p.path.lower().endswith(_NON_HTML):
        return "not an HTML page"
    return None


def explore(
    url: str, settings: Settings, headed: bool = False, allow_local: bool = False,
    max_pages: int = 1,
) -> tuple[list[dict], list[str]]:  # fmt: skip
    """Explore `url` and, breadth-first, up to max_pages - 1 same-origin pages it links to.

    Returns (elements, pages). Each element has a unique locator on its own page and a "page"
    key with that page's URL. Only the first page's errors are fatal; a failing linked page is
    logged and skipped.
    """
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=not headed)
        except PlaywrightError as e:
            raise GennaiError(
                f"could not launch Chromium ({_first_line(e)}); "
                "run: python -m playwright install chromium"
            ) from e
        try:
            page = browser.new_page()
            page.set_default_timeout(settings.page_timeout_ms)
            elements: list[dict] = []
            pages: list[str] = []
            origin: tuple = ()
            queue, seen = deque([url]), {normalize_url(url)}
            while queue and len(pages) < max_pages:
                target = queue.popleft()
                try:
                    _load(page, target, settings, allow_local, origin)
                    found = _pick_unique(
                        page, page.evaluate(_JS), settings.max_elements, len(elements)
                    )
                    links = page.evaluate(_LINKS_JS) if max_pages > 1 else []
                except (GennaiError, PlaywrightError) as e:
                    if not pages:
                        if isinstance(e, GennaiError):
                            raise
                        raise GennaiError(
                            f"browser error while exploring {url}: {_first_line(e)}"
                        ) from e
                    log.warning("skipping linked page %s: %s", target, _first_line(e))
                    continue
                if not pages:
                    origin = _origin(page.url)  # after redirects, e.g. http -> https
                for el in found:
                    el["page"] = target
                elements += found
                pages.append(target)
                for link in links:
                    key = normalize_url(link["href"])
                    reason = skip_reason(link["href"], link["text"], origin)
                    if reason is None and key not in seen:
                        seen.add(key)
                        queue.append(key)
                    elif reason is not None:
                        log.debug("not crawling %s: %s", link["href"], reason)
            log.info("explored %d page(s): %s", len(pages), ", ".join(pages))
            return elements, pages
        finally:
            browser.close()


def _load(page: Page, url: str, settings: Settings, allow_local: bool, origin: tuple) -> None:
    """Open one page and check it; `origin` is empty for the first page, set for linked ones."""
    check_url(url, allow_local)
    try:
        resp = page.goto(url, wait_until="load", timeout=settings.page_timeout_ms)
    except PlaywrightError as e:
        raise GennaiError(f"could not reach {url}: {_first_line(e)}") from e
    check_url(page.url, allow_local)  # a redirect must not reach a local target
    if origin and _origin(page.url) != origin:
        raise GennaiError(f"redirected to another origin ({page.url})")
    if resp is not None and resp.status >= 400:
        hint = "server overloaded or down" if resp.status >= 500 else "it may block bots"
        raise GennaiError(f"site returned HTTP {resp.status} ({hint})")
    if origin and resp is not None and "html" not in resp.headers.get("content-type", "html"):
        raise GennaiError(f"not an HTML page ({resp.headers['content-type']})")
    if any(t in page.title().lower() for t in _BLOCKED_TITLES):
        raise GennaiError(f"bot challenge detected at {url}; cannot test this site")
    _settle(page, settings.settle_ms)


def _count(page: Page, candidate: tuple[str, str]) -> int:
    try:
        return locate(page, *candidate).count()
    except PlaywrightError:  # e.g. an id with characters the selector engine rejects
        return 0


def _pick_unique(page: Page, raw: list[dict], limit: int, offset: int = 0) -> list[dict]:
    """Order fields, buttons, links; keep elements with a unique locator until limit.

    Ids continue after `offset` so they stay unique across crawled pages."""
    for a in raw:
        a["kind"] = infer_kind(a)
    rank = {"button": 1, "link": 2}
    raw.sort(key=lambda a: rank.get(a["kind"], 0))  # stable: DOM order within a group
    elements: list[dict] = []
    for a in raw:
        if len(elements) >= limit:
            break
        unique = [c for c in candidate_locators(a) if _count(page, c) == 1]
        if unique:
            elements.append({"id": f"e{offset + len(elements) + 1:02d}", **a, "locators": unique})
        else:
            log.info("skipping %s %r: no unique locator", a["tag"], a["label"] or a["text"])
    return elements
