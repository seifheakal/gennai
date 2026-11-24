"""Phase 4 report: one self-contained HTML file with tabs, filters and embedded screenshots.

Every page-derived value is escaped. The inline script only switches tabs, filters and sorts;
without it every section is shown one after the other.
"""

import base64
import html
import json
from pathlib import Path
from urllib.parse import urlparse

from gennai.phase2_generate import _name as element_name

TECHNIQUES = {
    "ep": "Equivalence partitioning",
    "bva": "Boundary values",
    "state": "State combinations",
    "click": "Click checks",
    "llm": "Model-proposed, gated",
}
FAILURE_CLASSES = {
    "element_intercepted": "Another element covers this one, so a real user could not click it.",
    "assertion": "The page did not behave as expected, for example it accepted invalid input.",
    "locator_not_found": "No locator matched exactly one element when the test ran. "
    "The page changed between loads.",
    "timeout": "An action did not finish within the time limit.",
    "page_unavailable": "The page answered with an HTTP error when the test loaded it. "
    "The site was down or overloaded; this says nothing about the element.",
    "login_failed": "Signing in with GENNAI_LOGIN_* failed when the test run started, so the "
    "test could not reach the page as a signed-in user.",
    "other": "Any other error. See the message.",
}
EXPECT_TEXT = {
    "valid": "the field reports valid (checkValidity)",
    "invalid": "the field reports invalid (checkValidity)",
    "max_length": "the value is cut to maxlength {limit}",
    "selected": "the option is selected",
    "checked": "the box is checked",
    "clickable": "a trial click passes: visible, enabled, not covered (nothing is clicked)",
    "form_valid": "the whole form reports valid",
    "form_invalid": "the whole form reports invalid",
}
MARK = {"passed": "\u2713", "failed": "\u2717", None: "\u00b7"}  # check, cross, dot
VERBS = {"fill": "type {v} into", "select": "select {v} in", "check": "check"}


def esc(v: object) -> str:
    return html.escape(str(v))


def _load(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def _short(url: str) -> str:
    parts = urlparse(url)
    return (parts.path or "/") + (f"?{parts.query}" if parts.query else "")


class _Report:
    def __init__(self, out: Path, r: dict) -> None:
        self.out, self.r = out, r
        self.tests: list[dict] = r["tests"]
        self.elements = _load(out / "elements.json")
        self.cases = {c.get("id"): c for c in _load(out / "test_cases.json")}
        self.by_el = {e["id"]: e for e in self.elements}
        self.llm: dict = r.get("llm_stats") or {}
        self.pages: list[str] = r.get("pages") or [r["url"]]
        self.multi = len(self.pages) > 1
        self.cover: dict[str, dict[str, list[str]]] = {}
        for t in self.tests:
            for eid in self.touched(t):
                self.cover.setdefault(eid, {}).setdefault(t["technique"], []).append(t["status"])
        self.covered = sum(e["id"] in self.cover for e in self.elements)

    def touched(self, t: dict) -> list[str]:
        c = self.cases.get(t["id"])
        return list(dict.fromkeys([c["target"], *(s["element"] for s in c["steps"])])) if c else []

    def label(self, eid: str) -> str:
        return f"{element_name(self.by_el[eid])} ({eid})" if eid in self.by_el else eid

    def steps(self, t: dict) -> str:
        c = self.cases.get(t["id"])
        if not c:
            return ""
        items = ["open the page" + (f" {_short(c['page'])}" if c.get("page") else "")]
        items += [
            f"{VERBS[s['action']].format(v=repr(s['value']))} {self.label(s['element'])}"
            for s in c["steps"]
        ]
        expect = EXPECT_TEXT[c["expect"]].format(limit=c.get("limit"))
        items.append(f"expect on {self.label(c['target'])}: {expect}")
        return "<ol class='steps'>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ol>"

    # header and cards

    def header(self) -> str:
        s, failed = self.r["summary"], self.r["summary"]["failed"]
        verdict = (
            f"<span class='pill bad'>{failed} finding{'s' * (failed != 1)}</span>"
            if failed
            else "<span class='pill ok'>all tests passed</span>"
        )
        pct = f"{100 * self.covered // len(self.elements)}%" if self.elements else "n/a"
        cards = [("Elements", self.r["elements"], "elements", "")]
        if self.multi:
            cards.append(("Pages", len(self.pages), "elements", ""))
        cards += [
            ("Tests", len(self.tests), "tests", "all"),
            ("Passed", s["passed"], "tests", "passed"),
            ("Failed", failed, "tests", "failed"),
            ("Elements covered", pct, "coverage", ""),
            ("Run time", f"{self.r['total_s']} s", "metrics", ""),
        ]
        if self.r.get("history"):
            cards.insert(4, ("Flaky", s.get("flaky", 0), "tests", ""))
        if self.llm.get("avg_response_s") is not None:
            tokens = f"{self.llm['prompt_tokens']} / {self.llm['completion_tokens']}"
            cards += [
                ("LLM avg response", f"{self.llm['avg_response_s']} s", "metrics", ""),
                ("LLM tokens in / out", tokens, "metrics", ""),
            ]
        buttons = "".join(
            f"<button class='card{' bad' if k == 'Failed' and v else ''}' data-go='{go}' "
            f"data-status='{st}'><span>{esc(k)}</span><b>{esc(v)}</b></button>"
            for k, v, go, st in cards
        )
        tabs = [("overview", "Overview"), ("tests", f"Tests ({len(self.tests)})"),
                ("coverage", "Coverage"), ("elements", f"Elements ({len(self.elements)})"),
                ("metrics", "Metrics")]  # fmt: skip
        nav = "".join(f"<a href='#{k}' data-tab='{k}' role='tab'>{v}</a>" for k, v in tabs)
        return (
            f"<header><h1>GenNAI report {verdict}</h1><div class='muted'>{esc(self.r['url'])}"
            f" &middot; started {esc(self.r['started'])} &middot; LLM: {esc(self.r['llm'])}"
            f"{self.extra()}</div><div class='cards'>{buttons}</div>"
            f"<nav class='tabs' role='tablist'>{nav}</nav>"
            "</header>"
        )

    def extra(self) -> str:
        """Review and run-history facts for the header line, when those features were used."""
        out, v, h = "", self.r.get("review"), self.r.get("history")
        if v:
            out += (f" &middot; review: {v['approved']} approved ({v['edited']} edited), "
                    f"{v['rejected']} rejected")  # fmt: skip
        if h:
            out += (f" &middot; run {h['runs']} of this site; flaky = passed and failed within "
                    f"the last {h['window']} runs")  # fmt: skip
        return out

    # overview: findings, failure classes, techniques

    def overview(self) -> str:
        failed = [t for t in self.tests if t["status"] == "failed"]
        parts = [f"<h2>Findings ({len(failed)})</h2>"]
        if not failed:
            parts.append("<p class='muted'>Every generated test passed.</p>")
        for t in failed:
            msg = t["message"] or ""
            first = msg.splitlines()[0] if msg else ""
            shot = ""
            if t["screenshot"]:
                data = base64.b64encode((self.out / t["screenshot"]).read_bytes()).decode()
                shot = (
                    f"<img class='shot' id='shot-{esc(t['id'])}' src='data:image/png;base64,{data}'"
                    " alt='screenshot at the moment of failure' title='Click to enlarge'>"
                )
            cls = t["failure_class"] or "other"
            parts.append(
                f"<article class='finding' id='f-{esc(t['id'])}'><div class='info'><div>"
                f"<b>{esc(t['title'])}</b> "
                f"<span class='badge'>{esc(cls)}</span> "
                f"<a href='#tests' data-open='{esc(t['id'])}'>"
                f"{esc(t['id'])} &middot; {esc(TECHNIQUES.get(t['technique'], t['technique']))}"
                f"</a></div><p class='why'>{esc(FAILURE_CLASSES.get(cls, ''))}</p>{self.steps(t)}"
                f"<p><code>{esc(first)}</code></p><details><summary>Full error</summary>"
                f"<pre>{esc(msg)}</pre></details></div>{shot}</article>"
            )
        counts = self.r["summary"]["failures_per_class"]
        rows = "".join(
            f"<tr class='{'' if counts.get(k) else 'muted'}'><td><span class='badge'>{k}</span>"
            f"</td><td>{counts.get(k, 0)}</td><td>{esc(v)}</td></tr>"
            for k, v in FAILURE_CLASSES.items()
        )
        parts.append(
            "<h2>Failure classes</h2><div class='wrap'><table><thead><tr><th>Class</th>"
            f"<th>Tests</th><th>Meaning</th></tr></thead><tbody>{rows}</tbody></table></div>"
        )
        parts.append("<h2>Tests per technique</h2><div class='wrap'><table><tbody>")
        for k, name in TECHNIQUES.items():
            got = [t for t in self.tests if t["technique"] == k]
            ok, bad = (sum(t["status"] == s for t in got) for s in ("passed", "failed"))
            n = len(got) or 1
            parts.append(
                f"<tr><td>{esc(name)}</td><td>{len(got)}</td><td class='muted'>{ok} passed, "
                f"{bad} failed</td><td style='width:45%'><div class='stack'>"
                f"<i class='ok' style='width:{100 * ok / n:.0f}%'></i>"
                f"<i class='bad' style='width:{100 * bad / n:.0f}%'></i></div></td></tr>"
            )
        parts.append("</tbody></table></div>")
        return "".join(parts)

    # tests: filters, sortable table, expandable details

    def _chips(self, name: str, options: list[tuple[str, str, int]]) -> str:
        total = sum(n for _, _, n in options)
        buttons = f"<button data-v='all'>All ({total})</button>" + "".join(
            f"<button data-v='{esc(v)}'>{esc(text)} ({n})</button>" for v, text, n in options if n
        )
        return f"<div class='chips' data-filter='{name}'>{buttons}</div>"

    def tests_tab(self) -> str:
        count = lambda key, v: sum(t.get(key) == v for t in self.tests)  # noqa: E731
        bars = [
            self._chips("status", [(s, s.replace("_", " "), count("status", s))
                                   for s in ("passed", "failed", "skipped", "not_run")]),
            self._chips("tech", [(k, k, count("technique", k)) for k in TECHNIQUES]),
        ]  # fmt: skip
        if any(t["failure_class"] for t in self.tests):
            bars.append(
                self._chips("cls", [(k, k, count("failure_class", k)) for k in FAILURE_CLASSES])
            )
        if self.multi:
            bars.append(self._chips("page", [(p, _short(p), count("page", p)) for p in self.pages]))
        toolbar = (
            "<div class='toolbar'><input type='search' id='q' "
            "placeholder='Search title, element or value' aria-label='Search tests'>"
            "<span id='active-el' class='pill' hidden>element: <span></span> "
            "<button aria-label='Remove element filter'>&times;</button></span>"
            "<button id='expand'>Expand all</button><button id='reset'>Clear filters</button>"
            f"<span id='count' class='muted'></span></div>{''.join(bars)}"
        )
        head = (
            "<th data-sort='id'>ID</th><th data-sort='title'>Test</th>"
            "<th data-sort='tech'>Technique</th><th class='hide-sm'>Elements</th>"
            + ("<th data-sort='page'>Page</th>" if self.multi else "")
            + "<th data-sort='priority' class='hide-sm'>Priority</th>"
            "<th data-sort='status'>Status</th><th data-sort='time'>Time</th>"
        )
        cols = 8 if self.multi else 7
        bodies = []
        for t in self.tests:
            els = self.touched(t)
            c = self.cases.get(t["id"]) or {}
            search = " ".join(
                [
                    t["title"],
                    t["technique"],
                    t["status"],
                    t["failure_class"] or "",
                    "flaky" if t.get("flaky") else "",
                ]
                + [self.label(e) for e in els]
                + [s.get("value", "") for s in c.get("steps", [])]
            ).lower()
            target = self.by_el.get(c.get("target", ""), {})
            locs = "".join(
                f"<li><code>{esc(k)} {esc(v)}</code></li>" for k, v in target.get("locators", [])
            )
            detail = (
                f"{self.steps(t)}<p class='muted'>Locators for {esc(self.label(c['target']))}, "
                f"tried in order:</p><ol>{locs}</ol>"
                if c
                else ""
            )
            if t["status"] == "failed":
                detail += (
                    f"<p><span class='badge'>{esc(t['failure_class'])}</span> "
                    f"<a href='#f-{esc(t['id'])}' data-go='overview'>see the finding</a></p>"
                    f"<pre>{esc(t['message'])}</pre><div class='shot-slot' data-shot='"
                    f"{esc(t['id'])}'></div>"
                )
            detail += (
                "<p class='muted'>Re-run from the run folder: <code>python -m pytest tests -c "
                f"tests/pytest.ini -k test_{esc(t['id'])}</code></p>"
            )
            status = esc(t["status"]) + (
                f" <span class='badge'>{esc(t['failure_class'])}</span>"
                if t["failure_class"]
                else ""
            )
            if "history" in t:  # recent runs, oldest first
                marks = " ".join(MARK.get(x, "?") for x in t["history"])
                status += f" <span class='muted' title='recent runs, oldest first'>{marks}</span>"
                status += " <span class='badge'>flaky</span>" if t["flaky"] else ""
            page_cell = f"<td>{esc(_short(t.get('page', '')))}</td>" if self.multi else ""
            bodies.append(
                f"<tbody class='t' data-id='{esc(t['id'])}' data-title='{esc(t['title'].lower())}' "
                f"data-tech='{esc(t['technique'])}' data-status='{esc(t['status'])}' "
                f"data-cls='{esc(t['failure_class'] or '')}' data-page='{esc(t.get('page', ''))}' "
                f"data-els='{esc(' '.join(els))}' data-priority='{t['priority']}' "
                f"data-time='{t['duration']}' data-q='{esc(search)}'><tr class='main'>"
                "<td class='id'><button class='toggle' aria-expanded='false' "
                f"aria-label='Show details'>&#9656;</button> {esc(t['id'])}</td>"
                f"<td>{esc(t['title'])}</td><td>{esc(t['technique'])}</td>"
                f"<td class='muted hide-sm'>{esc(', '.join(els))}</td>{page_cell}"
                f"<td class='hide-sm'>{t['priority']}</td>"
                f"<td class='{esc(t['status'])}'>{status}</td>"
                f"<td>{t['duration']} s</td></tr><tr class='detail' hidden><td colspan='{cols}'>"
                f"{detail}</td></tr></tbody>"
            )
        return (
            f"<h2>Tests</h2>{toolbar}<div class='wrap'><table class='tests'><thead><tr>{head}"
            f"</tr></thead>{''.join(bodies)}</table></div>"
        )

    # coverage: element x technique matrix

    def coverage(self) -> str:
        if not self.elements:
            return "<h2>Coverage</h2><p class='muted'>No elements were recorded.</p>"
        rows = ""
        for e in self.elements:
            got_all = self.cover.get(e["id"], {})
            cells, state = "", "none" if not got_all else "ok"
            for tech in TECHNIQUES:
                got = got_all.get(tech, [])
                bad = got.count("failed")
                attrs = f"data-el='{esc(e['id'])}' data-tech='{tech}' tabindex='0'"
                if not got:
                    cells += "<td class='none'>-</td>"
                elif bad:
                    state = "bad"
                    cells += f"<td class='bad' {attrs}>&#10007; {bad}/{len(got)}</td>"
                else:
                    cells += f"<td class='ok' {attrs}>&#10003; {len(got)}</td>"
            total = sum(len(v) for v in got_all.values())
            total_cell = total or "<span class='pill bad'>no test</span>"
            page = f"<td>{esc(_short(e.get('page', '')))}</td>" if self.multi else ""
            rows += (
                f"<tr class='cov' data-state='{state}'><td>{esc(e['id'])}</td><td><a href='#tests'"
                f" data-el='{esc(e['id'])}'>{esc(element_name(e))}</a></td><td>{esc(e['kind'])}"
                f"</td>{page}{cells}<td>{total_cell}</td></tr>"
            )
        n = len(self.elements)
        chips = (
            "<div class='chips' data-cov><button data-v='all' class='on'>All elements</button>"
            "<button data-v='bad'>With failures</button><button data-v='none'>Not covered"
            "</button></div>"
        )
        head = "".join(f"<th title='{esc(v)}'>{k}</th>" for k, v in TECHNIQUES.items())
        return (
            f"<h2>Coverage</h2><p class='muted'>{self.covered} of {n} elements have at least "
            "one test. A cell counts the tests that touch the element with that technique; "
            "click a cell or an element to see those tests.</p>"
            f"{chips}<div class='wrap'><table class='matrix'><thead><tr><th>ID</th>"
            f"<th>Element</th><th>Kind</th>{'<th>Page</th>' if self.multi else ''}{head}"
            f"<th>Tests</th></tr></thead><tbody>{rows}</tbody></table></div>"
        )

    # elements: what Phase 1 found

    def elements_tab(self) -> str:
        kinds: dict[str, int] = {}
        for e in self.elements:
            kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
        chips = "".join(
            f"<button data-v='{esc(k)}'>{esc(k)} ({n})</button>" for k, n in sorted(kinds.items())
        )
        all_btn = "<button data-v='all' class='on'>All</button>"
        chips = f"<div class='chips' data-kind>{all_btn}{chips}</div>"
        rows = ""
        for e in self.elements:
            facts = []
            if e.get("required"):
                facts.append("required")
            for lo, hi, word in (("minlength", "maxlength", "length"), ("min", "max", "range")):
                if e.get(lo) or e.get(hi):
                    facts.append(f"{word} {e.get(lo) or '…'}-{e.get(hi) or '…'}")
            if e.get("pattern"):
                facts.append("pattern")
            if e.get("options"):
                facts.append(f"{len(e['options'])} options")
            if e.get("form", -1) >= 0:
                facts.append(f"form {e['form'] + 1}")
            locs = "".join(
                f"<li><code>{esc(k)} {esc(v)}</code></li>" for k, v in e.get("locators", [])
            )
            html_tag = esc(e["tag"]) + (f"[type={esc(e['type'])}]" if e.get("type") else "")
            n = sum(len(v) for v in self.cover.get(e["id"], {}).values())
            page = f"<td>{esc(_short(e.get('page', '')))}</td>" if self.multi else ""
            rows += (
                f"<tr class='el' data-kind='{esc(e['kind'])}' data-q='"
                f"{esc((element_name(e) + ' ' + e['id'] + ' ' + e['kind']).lower())}'>"
                f"<td>{esc(e['id'])}</td><td>{esc(element_name(e))}</td><td>{esc(e['kind'])}</td>"
                f"<td><code>{html_tag}</code></td>{page}<td>{esc(', '.join(facts)) or '-'}</td>"
                f"<td><ol class='locs'>{locs}</ol></td><td><a href='#tests' "
                f"data-el='{esc(e['id'])}'>{n}</a></td></tr>"
            )
        return (
            "<h2>Elements</h2><p class='muted'>What Phase 1 found. Every locator listed "
            "matched exactly one element when the page was explored; tests try them in order."
            f"</p><div class='toolbar'><input type='search' id='eq' placeholder='Search elements' "
            f"aria-label='Search elements'></div>{chips}<div class='wrap'><table><thead><tr>"
            "<th>ID</th><th>Element</th><th>Kind</th><th>HTML</th>"
            f"{'<th>Page</th>' if self.multi else ''}<th>Constraints</th><th>Locators</th>"
            f"<th>Tests</th></tr></thead><tbody>{rows}</tbody></table></div>"
        )

    # metrics: phase timings, LLM calls, slowest tests

    def metrics(self) -> str:
        durations = self.r.get("durations") or {}
        longest = max(durations.values(), default=0) or 1
        rows = "".join(
            f"<tr><td>{esc(k)}</td><td>{v} s</td><td style='width:60%'><div class='bar' "
            f"style='width:{100 * v / longest:.0f}%'></div></td></tr>"
            for k, v in durations.items()
        )
        parts = [
            "<h2>Time per phase</h2><div class='wrap'><table><tbody>"
            f"{rows}<tr><td><b>total</b></td><td><b>{self.r['total_s']} s</b></td><td></td>"
            "</tr></tbody></table></div>",
            f"<h2>LLM step</h2><p>{esc(self.r['llm'])}</p>",
        ]
        if "proposed" in self.llm:
            gate = [("Proposed", "proposed"), ("Accepted", "accepted"),
                    ("Rejected: hallucination", "rejected_hallucinations"),
                    ("Rejected: schema", "rejected_schema")]  # fmt: skip
            parts.append(
                "<div class='cards small'>"
                + "".join(
                    f"<div class='card'><span>{k}</span><b>{self.llm[v]}</b></div>" for k, v in gate
                )
                + "</div><p class='muted'>The model only returns JSON. A spec is accepted only if "
                "its element exists, its action fits the element and a select value is a real "
                "option.</p>"
            )
        if self.llm.get("attempts"):
            calls = "".join(
                f"<tr><td>{i}</td><td>{esc(a['provider'])}/{esc(a['model'])}</td>"
                f"<td>{esc(a.get('outcome', ''))}</td><td>{esc(a.get('seconds', ''))} s</td>"
                f"<td>{esc(a.get('prompt_tokens', '-'))} / {esc(a.get('completion_tokens', '-'))}"
                "</td></tr>"
                for i, a in enumerate(self.llm["attempts"], 1)
            )
            parts.append(
                "<div class='wrap'><table><thead><tr><th>Call</th><th>Model</th><th>Outcome</th>"
                f"<th>Response time</th><th>Tokens in / out</th></tr></thead><tbody>{calls}"
                "</tbody></table></div>"
            )
        slow = sorted(self.tests, key=lambda t: -t["duration"])[:5]
        rows = "".join(
            f"<tr><td>{esc(t['id'])}</td><td>{esc(t['title'])}</td><td>{t['duration']} s</td></tr>"
            for t in slow
        )
        parts.append(
            f"<h2>Slowest tests</h2><div class='wrap'><table><tbody>{rows}</tbody></table></div>"
        )
        return "".join(parts)


def _asset(name: str) -> str:
    """Inline a stylesheet or script that ships next to this module."""
    return (Path(__file__).parent / name).read_text(encoding="utf-8")


def render(out: Path, r: dict) -> str:
    """The full report as one HTML string."""
    rep = _Report(out, r)
    sections = [("overview", rep.overview()), ("tests", rep.tests_tab()),
                ("coverage", rep.coverage()), ("elements", rep.elements_tab()),
                ("metrics", rep.metrics())]  # fmt: skip
    body = "".join(f"<section data-tab='{k}' role='tabpanel'>{v}</section>" for k, v in sections)
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>GenNAI report</title><style>{_asset('report.css')}</style></head><body>"
        f"{rep.header()}"
        f"<main>{body}</main><script>{_asset('report.js')}</script></body></html>"
    )
