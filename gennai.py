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
from gennai.safety import check_url

log = logging.getLogger("gennai")


def _positive(text: str) -> int:
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gennai", description="AI-assisted web test generation")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "demo"):
        p = sub.add_parser(name, help="test a URL" if name == "run" else "test the bundled demo")
        if name == "run":
            p.add_argument("url")
            p.add_argument("--allow-local", action="store_true", help="allow local/private hosts")
        p.add_argument("--out", type=Path, help="output dir (default runs/<host>_<timestamp>)")
        p.add_argument("--headed", action="store_true", help="show the browser")
        p.add_argument("--max-tests", type=_positive, help="cap on generated tests")
    return parser


def _summary(r: dict, out: Path) -> None:
    s = r["summary"]
    failures = ", ".join(f"{k}={v}" for k, v in s["failures_per_class"].items()) or "none"
    print("\nGenNAI summary")
    print(f"  url:       {r['url']}")
    print(f"  elements:  {r['elements']}")
    print(f"  tests:     {', '.join(f'{k}={v}' for k, v in r['tests_per_technique'].items())}")
    print(f"  results:   {s['passed']} passed, {s['failed']} failed")
    print(f"  failures:  {failures}")
    print(f"  llm:       {r['llm']}")
    m = r.get("llm_stats") or {}
    if m.get("avg_response_s") is not None:
        print(f"  llm calls: {m['calls']}, avg response {m['avg_response_s']}s, "
              f"tokens {m['prompt_tokens']} in / {m['completion_tokens']} out")  # fmt: skip
    print(f"  phases:    {', '.join(f'{k} {v}s' for k, v in r['durations'].items())}")
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
        if args.command == "demo":
            with serve_dir() as url:
                out = (args.out or Path("runs") / f"demo_{stamp}").resolve()
                results = run_pipeline(url, out, settings, args.headed, allow_local=True)
        else:
            check_url(args.url, args.allow_local)  # fail with exit 2 before urlparse can raise
            host = re.sub(r"[^\w.-]", "_", urlparse(args.url).hostname or "site")
            out = (args.out or Path("runs") / f"{host}_{stamp}").resolve()
            results = run_pipeline(args.url, out, settings, args.headed, args.allow_local)
    except GennaiError as e:
        log.debug("failure details", exc_info=True)
        log.error("%s", e)
        return 3 if isinstance(e, NoTestableElements) else 2
    _summary(results, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
