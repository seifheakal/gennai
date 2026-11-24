"""GenNAI command line: `python gennai.py run <url>`, `demo` or `ui`."""

import argparse
import logging
import sys
from dataclasses import replace
from pathlib import Path

from gennai import GennaiError, NoTestableElements
from gennai.config import load_settings
from gennai.pipeline import run_paths, run_pipeline, serve_dir, site_name
from gennai.review import ask_in_terminal
from gennai.safety import check_url
from gennai.web import serve as serve_ui

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
            "--no-history", action="store_true",
            help="do not append this run to runs/history/<site>.jsonl (used for flaky tests)",
        )  # fmt: skip
        p.add_argument(
            "--review", action="store_true",
            help="pause after generating test cases so you can approve or edit them",
        )  # fmt: skip
        if name == "demo":
            p.add_argument(
                "--login", action="store_true",
                help="sign in to the demo's test account and test the page behind it",
            )  # fmt: skip
    ui = sub.add_parser("ui", help="open a local web page that starts runs")
    ui.add_argument("--port", type=int, default=8765, help="port on 127.0.0.1 (default 8765)")
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
    if r.get("history"):
        h = r["history"]
        print(f"  history:   run {h['runs']} of this site; {s['flaky']} flaky in the last "
              f"{h['window']} runs ({h['file']})")  # fmt: skip
    print(f"  llm:       {r['llm']}")
    if r.get("notifications"):
        print(f"  notified:  {', '.join(f'{k} {v}' for k, v in r['notifications'].items())}")
    print(f"  time:      {r['total_s']}s")
    print(f"  report:    {out / 'report.html'}")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(format="%(levelname)s: %(message)s")
    try:
        settings = load_settings()
        logging.getLogger().setLevel(settings.log_level)
        if args.command == "ui":
            serve_ui(args.port)  # each run reloads the settings
            return 0
        if args.max_tests:
            settings = replace(settings, max_tests=args.max_tests)
        review = ask_in_terminal if args.review else None
        if args.command == "run":
            check_url(args.url, args.allow_local)  # fail with exit 2 before urlparse can raise
        site = "demo" if args.command == "demo" else site_name(args.url)
        out, history = run_paths(site, settings, args.out, not args.no_history)
        if args.command == "demo":
            with serve_dir() as url:
                if args.login:  # the demo's own test account, shown on demo/login.html
                    settings = replace(settings, login_url=url + "login.html",
                                       login_user="demo", login_password="demo-pass")  # fmt: skip
                    url += "account.html"
                results = run_pipeline(
                    url, out, settings, args.headed, True, args.max_pages, review, history
                )
        else:
            results = run_pipeline(
                args.url, out, settings, args.headed, args.allow_local, args.max_pages,
                review, history,
            )  # fmt: skip
    except GennaiError as e:
        log.debug("failure details", exc_info=True)
        log.error("%s", e)
        return 3 if isinstance(e, NoTestableElements) else 2
    _summary(results, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
