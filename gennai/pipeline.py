"""Orchestrates the four phases and serves the offline demo site."""

import functools
import json
import logging
import re
import threading
import time
from collections import Counter
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from gennai import GennaiError, NoTestableElements
from gennai.config import Settings
from gennai.llm import propose_cases
from gennai.notify import notify
from gennai.phase1_explore import explore
from gennai.phase2_generate import generate
from gennai.phase3_codegen import write_project
from gennai.phase4_execute import case_key, execute, write_results
from gennai.review import load_reviewed, write_for_review
from gennai.safety import check_url

log = logging.getLogger(__name__)
DEMO_DIR = Path(__file__).resolve().parent.parent / "demo"


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A002
        pass


def site_name(url: str) -> str:
    """Folder-safe site name: the host, plus the port if one is given."""
    parts = urlparse(url)
    name = (parts.hostname or "site") + (f"_{parts.port}" if parts.port else "")
    return re.sub(r"[^\w.-]", "_", name)


def run_paths(
    site: str, settings: Settings, out: Path | None = None, history: bool = True,
    runs: Path = Path("runs"),
) -> tuple[Path, Path | None]:  # fmt: skip
    """(output folder, history file) for a run: runs/<site>_<timestamp>, history/<site>.jsonl."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = (out or runs / f"{site}_{stamp}").resolve()
    return out, Path(settings.history_dir, f"{site}.jsonl").resolve() if history else None


@contextmanager
def serve_dir(directory: Path = DEMO_DIR) -> Iterator[str]:
    """Serve a directory on 127.0.0.1 (free port) in a background thread; yield its URL."""
    handler = functools.partial(_QuietHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        server.server_close()


def run_pipeline(
    url: str, out: Path, settings: Settings, headed: bool = False, allow_local: bool = False,
    max_pages: int = 1, review: Callable[[Path], None] | None = None,
    history: Path | None = None, progress: Callable[[str], None] | None = None,
) -> dict:  # fmt: skip
    """Explore, generate, write and run tests; return the results dict (also on disk).

    With `review`, the cases are written for a person to approve and `review(path)` is called;
    it must block until they are done. Only approved cases are generated and run.
    With `history`, the run is appended to that JSONL file and flaky tests are marked.
    `progress` (used by the web UI) receives one short line as each phase finishes.
    """
    say = progress or (lambda text: None)
    started = datetime.now().isoformat(timespec="seconds")
    t0 = last = time.perf_counter()
    durations: dict[str, float] = {}

    def lap(phase: str) -> None:
        nonlocal last
        now = time.perf_counter()
        durations[phase] = round(now - last, 2)
        last = now

    url = check_url(url, allow_local)
    out.mkdir(parents=True, exist_ok=True)
    say(f"Exploring {url}" + (f" and up to {max_pages - 1} linked pages" if max_pages > 1 else ""))
    elements, pages = explore(url, settings, headed, allow_local, max_pages)
    (out / "elements.json").write_text(json.dumps(elements, indent=2), encoding="utf-8")
    lap("explore")
    say(f"Phase 1: found {len(elements)} elements on {len(pages)} page(s)")
    extra_cases, llm = propose_cases(url, elements, settings)
    if settings.llm_providers:
        lap("llm")
    cases = generate(elements, settings.max_tests, extra_cases)
    if not cases:
        raise NoTestableElements(f"no testable elements found at {url}")
    cases_file = out / "test_cases.json"
    review_stats = None
    if review is None:
        cases_file.write_text(
            json.dumps([c.model_dump() for c in cases], indent=2), encoding="utf-8"
        )
    lap("generate")
    techniques = ", ".join(f"{k} {v}" for k, v in Counter(c.technique for c in cases).items())
    say(f"Phase 2: generated {len(cases)} test cases ({techniques}); LLM: {llm['status']}")
    if review is not None:
        write_for_review(cases_file, cases)
        review(cases_file)
        cases, review_stats = load_reviewed(cases_file, cases)
        lap("review")  # time spent waiting for the person
        if not cases:
            raise GennaiError("the review rejected every test case; nothing to run")
    write_project(url, elements, cases, out, settings)
    lap("codegen")
    say("Phase 3: wrote the pytest suite; running it now")
    rows = execute(out, settings, cases, headed)
    by_id = {e["id"]: e for e in elements}
    for row, case in zip(rows, cases, strict=True):
        row["key"] = case_key(case, by_id)
    lap("execute")
    say(f"Phase 4: ran {sum(r['status'] in ('passed', 'failed') for r in rows)} tests")
    meta = {
        "url": url,
        "started": started,
        "finished": datetime.now().isoformat(timespec="seconds"),
        "total_s": round(time.perf_counter() - t0, 1),
        "durations": durations,
        "pages": pages,
        "elements": len(elements),
        "tests_per_technique": dict(Counter(c.technique for c in cases)),
        "llm": llm["status"],
        "llm_stats": llm,
        "review": review_stats,
    }
    results = write_results(out, meta, rows, history, settings.flaky_window)
    results["notifications"] = notify(settings, results, out)  # {} when none is configured
    if results["notifications"]:
        (out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results
