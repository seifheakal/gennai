"""Phase 4: run the generated suite, classify failures, write results.json and report.html."""

import base64
import html
import json
import logging
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from gennai import GennaiError
from gennai.config import Settings
from gennai.phase2_generate import Case

log = logging.getLogger(__name__)
MESSAGE_LIMIT = 500


def classify_failure(message: str) -> str:
    """Failure class from a pytest/Playwright message. Order matters: intercepted is a timeout."""
    if "PageUnavailable" in message:
        return "page_unavailable"
    if "intercepts pointer events" in message or "ElementClickIntercepted" in message:
        return "element_intercepted"
    if "LocatorNotFound" in message:
        return "locator_not_found"
    if "TimeoutError" in message or "Timeout" in message and "exceeded" in message:
        return "timeout"
    if "AssertionError" in message:
        return "assertion"
    return "other"


def execute(out: Path, settings: Settings, cases: list[Case], headed: bool = False) -> list[dict]:
    """Run pytest on <out>/tests; return one result row per case."""
    tests, junit = out / "tests", out / "junit.xml"
    cmd = [sys.executable, "-m", "pytest", str(tests), "-c", str(tests / "pytest.ini"),
           "-p", "no:cacheprovider", f"--junitxml={junit}", "-q"]  # fmt: skip
    env = {**os.environ, "GENNAI_HEADED": "1" if headed else "0"}
    junit.unlink(missing_ok=True)
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, env=env, timeout=settings.run_timeout_s
        )
    except subprocess.TimeoutExpired as e:
        raise GennaiError(
            f"generated tests exceeded GENNAI_RUN_TIMEOUT_S={settings.run_timeout_s}"
        ) from e
    log.debug("pytest output:\n%s", proc.stdout)
    if not junit.exists():
        raise GennaiError(
            f"pytest produced no results (exit {proc.returncode}): {proc.stderr[-300:]}"
        )
    found = {tc.get("name"): tc for tc in ET.parse(junit).getroot().iter("testcase")}
    rows = [_row(c, found.get(f"test_{c.id}"), out) for c in cases]
    if not any(r["status"] in ("passed", "failed") for r in rows):
        raise GennaiError(
            f"no generated test ran (pytest exit {proc.returncode}): {proc.stdout[-300:]}"
        )
    return rows


def _row(case: Case, tc: ET.Element | None, out: Path) -> dict:
    row = {"id": case.id, "title": case.title, "technique": case.technique, "page": case.page,
           "priority": case.priority, "status": "not_run", "duration": 0.0,
           "failure_class": None, "message": "", "screenshot": None}  # fmt: skip
    if tc is None:
        return row
    row["duration"] = round(float(tc.get("time", 0)), 2)
    bad = next((c for c in tc if c.tag in ("failure", "error")), None)
    if bad is None:
        row["status"] = "skipped" if tc.find("skipped") is not None else "passed"
        return row
    message = bad.get("message") or ""
    full = message + "\n" + (bad.text or "")
    # the covering element is named deep in the call log; surface it before truncating
    culprit = next((ln.lstrip("E -") + "\n" for ln in full.splitlines() if "intercepts" in ln), "")
    row.update(status="failed", message=culprit + message[:MESSAGE_LIMIT],
               failure_class=classify_failure(full))  # fmt: skip
    shot = Path("screenshots") / f"test_{case.id}.png"
    row["screenshot"] = shot.as_posix() if (out / shot).exists() else None
    return row


def write_results(out: Path, meta: dict, rows: list[dict]) -> dict:
    """Write results.json and report.html; return the results dict."""
    failures = Counter(r["failure_class"] for r in rows if r["status"] == "failed")
    results = {**meta, "summary": {
        "passed": sum(r["status"] == "passed" for r in rows),
        "failed": sum(r["status"] == "failed" for r in rows),
        "failures_per_class": dict(failures)}, "tests": rows}  # fmt: skip
    (out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (out / "report.html").write_text(_html(out, results), encoding="utf-8")
    return results


_CSS = """body{font:14px system-ui,sans-serif;margin:24px;color:#222}
table{border-collapse:collapse;width:100%}
td,th{border:1px solid #ccc;padding:6px;vertical-align:top;text-align:left}
.passed{color:#0a7d27}.failed{color:#b3261e;font-weight:600}
img{max-width:480px;border:1px solid #ccc}code{white-space:pre-wrap}"""


def _html(out: Path, r: dict) -> str:
    esc = lambda v: html.escape(str(v))  # noqa: E731
    rows = []
    for t in r["tests"]:
        shot = ""
        if t["screenshot"]:
            data = base64.b64encode((out / t["screenshot"]).read_bytes()).decode()
            shot = (
                "<details><summary>screenshot</summary>"
                f'<img src="data:image/png;base64,{data}" alt="failure screenshot"></details>'
            )
        rows.append(
            f"<tr><td>{esc(t['id'])}</td><td>{esc(t['title'])}</td><td>{esc(t['technique'])}</td>"
            f"<td>{esc(t.get('page', ''))}</td>"
            f"<td>{t['priority']}</td><td class='{esc(t['status'])}'>{esc(t['status'])}</td>"
            f"<td>{esc(t['failure_class'] or '')}</td><td>{t['duration']}s</td>"
            f"<td><code>{esc(t['message'])}</code>{shot}</td></tr>"
        )
    s = r["summary"]
    pages = ", ".join(esc(p) for p in r.get("pages", [r["url"]]))
    v = r.get("review")
    review = (
        f"<br>Human review: {v['approved']} approved ({v['edited']} edited), "
        f"{v['rejected']} rejected" if v else ""
    )  # fmt: skip
    return (
        f"<!doctype html><html lang='en'><meta charset='utf-8'><title>GenNAI report</title>"
        f"<style>{_CSS}</style><h1>GenNAI report</h1>"
        f"<p>URL: {esc(r['url'])}<br>Started: {esc(r['started'])}"
        f" &middot; total {esc(r['total_s'])}s"
        f"<br>Pages: {esc(len(r.get('pages', [r['url']])))} &middot; {pages}"
        f"<br>Elements: {esc(r['elements'])} &middot; tests: {esc(r['tests_per_technique'])}"
        f"<br>Passed: {s['passed']} &middot; failed: {s['failed']} {esc(s['failures_per_class'])}"
        f"<br>LLM: {esc(r['llm'])}{review}<br>Phase durations: {esc(r['durations'])}</p>"
        "<table><tr><th>ID</th><th>Test</th><th>Technique</th><th>Page</th><th>Priority</th><th>Status</th>"
        f"<th>Failure class</th><th>Time</th><th>Details</th></tr>{''.join(rows)}</table></html>"
    )
