# Future work

Features and ideas that were left out on purpose, one line each: what, where it would go, and why it was left out. Real flaws in what exists are in [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md).

## Removed from the course version, since rebuilt

Rebuilt since, and described in the README: multi-page crawling (`--max-pages`), login with credentials from `.env` (`GENNAI_LOGIN_*`), Slack and email notifications (`GENNAI_SLACK_WEBHOOK_URL`, `GENNAI_SMTP_*`), a local web chat UI (`python gennai.py ui`), human review of generated tests (`--review`), and run history with flaky-test marking (`runs/history/<site>.jsonl`). The course's reviewer was simulated with `random.random()`; the rebuilt one waits for a person. The course's SQLite history never stored a non-empty result; the rebuilt one is an append-only JSONL file. The course's notifications only logged "sent"; the rebuilt ones send and report each channel's result. The course's Flask UI ran the old phases by changing directories and copying files; the rebuilt one is a small standard-library server that calls `run_pipeline`.

## Ideas to build next

- **Evidence-grade run records**: link every failure to its screenshot, a DOM snapshot and the provenance of the locator that was used (`gennai/phase4_execute.py`). Left out to keep the report one self-contained file.
- **`validate` command**: integrity checks over run output (every failed test has a class, every screenshot exists, counts add up), run in CI and before commit. Not needed for a single-user demo.
- **Staged, resumable pipeline**: `--dry-run`, `--only <phase>`, `--from <phase>` in `gennai.py`. Each phase already writes its output (`elements.json`, `test_cases.json`, `tests/`, `results.json`), so this is mostly CLI wiring. Left out because a full run takes under a minute and a half on the tested sites.
- **Semantic gate for model output**: extend the deterministic gate from "element and action exist" to "the expected result follows from the field's constraints" (for example, recompute `valid`/`invalid` for a proposed value with the field's `type`, `min`, `max`, `minlength` and `maxlength`) (`gennai/safety.py`). This is the main hallucination risk that is still open.
- **Valid data for `pattern` fields**: let the model propose a value and accept it only if Python's `re.fullmatch` agrees with the field's `pattern` (`gennai/safety.py`). This fits the same "model proposes, deterministic check disposes" design.
- **Provider status across runs**: response time and token usage per call are now recorded and shown in the report. Still missing are each provider's cooldown state and last error carried across runs, and trends over time (`gennai/llm.py`). Left out because each run is independent and makes at most a few calls.
- **Self-healing locators**: when every candidate fails, ask the model for a new locator from the current DOM. Validate it for uniqueness and keep it only after a person approves it (`gennai/phase3_codegen.py`).
- **Optional overlay handling**: a retry mode that dismisses a covering element (cookie banner, ad) and reports both results. It was left out because the covered element is the finding.
- **Shadow DOM and iframe discovery** in Phase 1's element collection script (`gennai/phase1_explore.py`).
- **Sandboxed test execution**: run the generated suite in a container with no host filesystem access (`gennai/phase4_execute.py`).
- **MCP server or Claude Code slash command**: expose `run` as a tool (for example `/run-gennai <url>`) so an agent can test a page it just changed.
- **Generated architecture map**: a small script that draws the module and data-flow diagram from the code so it can't drift from the README.
- **Structured logging and error tracking**: JSON logs with a run id that matches the run's line in the history file.
