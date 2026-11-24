"""Phase 1: load the page once and collect interactive elements with unique locators."""

import logging
import re
import time

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


def explore(url: str, settings: Settings, headed: bool = False, allow_local: bool = False) -> list:
    """Return elements (dicts with id, kind, attributes, locators); each has a unique locator."""
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
            try:
                resp = page.goto(url, wait_until="load", timeout=settings.page_timeout_ms)
            except PlaywrightError as e:
                raise GennaiError(f"could not reach {url}: {_first_line(e)}") from e
            check_url(page.url, allow_local)  # a redirect must not reach a local target
            if resp is not None and resp.status >= 400:
                raise GennaiError(
                    f"site returned HTTP {resp.status} (it may block automated browsers)"
                )
            if any(t in page.title().lower() for t in _BLOCKED_TITLES):
                raise GennaiError(f"bot challenge detected at {url}; cannot test this site")
            _settle(page, settings.settle_ms)
            return _pick_unique(page, page.evaluate(_JS), settings.max_elements)
        except PlaywrightError as e:
            raise GennaiError(f"browser error while exploring {url}: {_first_line(e)}") from e
        finally:
            browser.close()


def _count(page: Page, candidate: tuple[str, str]) -> int:
    try:
        return locate(page, *candidate).count()
    except PlaywrightError:  # e.g. an id with characters the selector engine rejects
        return 0


def _pick_unique(page: Page, raw: list[dict], limit: int) -> list[dict]:
    """Order fields, buttons, links; keep elements with a unique locator until limit."""
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
            elements.append({"id": f"e{len(elements) + 1:02d}", **a, "locators": unique})
        else:
            log.info("skipping %s %r: no unique locator", a["tag"], a["label"] or a["text"])
    return elements
