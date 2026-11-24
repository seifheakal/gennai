"""Orchestrates the four phases and serves the offline demo site."""

import functools
import json
import logging
import threading
import time
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from gennai import NoTestableElements
from gennai.config import Settings
from gennai.llm import propose_cases
from gennai.phase1_explore import explore
from gennai.phase2_generate import generate
from gennai.phase3_codegen import write_project
from gennai.phase4_execute import execute, write_results
from gennai.safety import check_url

log = logging.getLogger(__name__)
DEMO_DIR = Path(__file__).resolve().parent.parent / "demo"


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A002
        pass


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
    max_pages: int = 1,
) -> dict:  # fmt: skip
    """Explore, generate, write and run tests; return the results dict (also on disk)."""
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
    elements, pages = explore(url, settings, headed, allow_local, max_pages)
    (out / "elements.json").write_text(json.dumps(elements, indent=2), encoding="utf-8")
    lap("explore")
    extra_cases, llm = propose_cases(url, elements, settings)
    cases = generate(elements, settings.max_tests, extra_cases)
    if not cases:
        raise NoTestableElements(f"no testable elements found at {url}")
    (out / "test_cases.json").write_text(
        json.dumps([c.model_dump() for c in cases], indent=2), encoding="utf-8"
    )
    lap("generate")
    write_project(url, elements, cases, out, settings)
    lap("codegen")
    rows = execute(out, settings, cases, headed)
    lap("execute")
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
    }
    return write_results(out, meta, rows)
