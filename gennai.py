"""GenNAI command line: `python gennai.py run <url>` or `python gennai.py demo`."""

import argparse
import logging
import re
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from gennai import GennaiError, NoTestableElements
from gennai.config import load_settings
from gennai.pipeline import run_pipeline, serve_dir
from gennai.review import ask_in_terminal
from gennai.safety import check_url

log = logging.getLogger("gennai")
MAX_PAGES = 20  # keeps a crawl polite and the run under the pytest timeout


def _positive(text: str) -> int:
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def _max_pages(text: str) -> int:
    value = _positive(text)
    if value > MAX_PAGES:
        raise argparse.ArgumentTypeError(f"must be at most {MAX_PAGES}")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gennai", description="AI-assisted web test generation")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "demo"):
        p = sub.add_parser(name, help="test a URL" if name == "run" else "test the bundled demo")
        if name == "run":
            p.add_argument("url")
            p.add_argument("--allow-local", action="store_true", help="allow local/private hosts")
        p.add_argument(
            "--max-pages", type=_max_pages, default=1,
            help=f"crawl up to N same-origin pages linked from the start page, breadth-first "
            f"(default 1 = only the start page, max {MAX_PAGES})",
        )  # fmt: skip
        p.add_argument("--out", type=Path, help="output dir (default runs/<host>_<timestamp>)")
        p.add_argument("--headed", action="store_true", help="show the browser")
        p.add_argument("--max-tests", type=_positive, help="cap on generated tests")
        p.add_argument(
            "--review", action="store_true",
            help="pause after generating test cases so you can approve or edit them",
        )  # fmt: skip
    return parser


def _summary(r: dict, out: Path) -> None:
    s = r["summary"]
    failures = ", ".join(f"{k}={v}" for k, v in s["failures_per_class"].items()) or "none"
    print("\nGenNAI summary")
    print(f"  url:       {r['url']}")
    print(f"  pages:     {len(r['pages'])} ({', '.join(r['pages'])})")
    print(f"  elements:  {r['elements']}")
    print(f"  tests:     {', '.join(f'{k}={v}' for k, v in r['tests_per_technique'].items())}")
    if r.get("review"):
        v = r["review"]
        print(f"  review:    {v['approved']} approved ({v['edited']} edited), "
              f"{v['rejected']} rejected")  # fmt: skip
    print(f"  results:   {s['passed']} passed, {s['failed']} failed")
    print(f"  failures:  {failures}")
    print(f"  llm:       {r['llm']}")
    print(f"  time:      {r['total_s']}s")
    print(f"  report:    {out / 'report.html'}")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(format="%(levelname)s: %(message)s")
    try:
        settings = load_settings()
        logging.getLogger().setLevel(settings.log_level)
        if args.max_tests:
            settings = replace(settings, max_tests=args.max_tests)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        review = ask_in_terminal if args.review else None
        if args.command == "demo":
            with serve_dir() as url:
                out = (args.out or Path("runs") / f"demo_{stamp}").resolve()
                results = run_pipeline(
                    url, out, settings, args.headed, True, args.max_pages, review
                )
        else:
            check_url(args.url, args.allow_local)  # fail with exit 2 before urlparse can raise
            host = re.sub(r"[^\w.-]", "_", urlparse(args.url).hostname or "site")
            out = (args.out or Path("runs") / f"{host}_{stamp}").resolve()
            results = run_pipeline(
                args.url, out, settings, args.headed, args.allow_local, args.max_pages, review
            )
    except GennaiError as e:
        log.debug("failure details", exc_info=True)
        log.error("%s", e)
        return 3 if isinstance(e, NoTestableElements) else 2
    _summary(results, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
