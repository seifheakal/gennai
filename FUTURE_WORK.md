# Future work

Features and ideas that were left out on purpose, one line each: what, where it would go, and why it was left out. Real flaws in what exists are in [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md).

## Removed from the course version (did not work or was simulated)

- **Human review of generated tests**: a step between Phase 2 and Phase 3 where a person approves or rejects test cases before they run (`gennai/pipeline.py`). The course version simulated reviewer feedback with `random.random()`, so it was removed rather than kept fake.
- **Web chat UI**: a browser interface over the same pipeline. The course's Flask UI ran the old phases by changing directories and copying files between them, and it broke once the phases were rebuilt.
- **Run history and flaky-test detection**: an append-only record of runs, with status computed at render time, to tell real regressions from flake across runs (`gennai/phase4_execute.py`). The course version's SQLite history never stored a non-empty result.
- **Notifications**: Slack or email when a run finishes. The course version's functions only logged "sent" and sent nothing.
- **Multi-page crawling and authenticated flows**: a crawl scope and login fixtures in Phase 1. The course crawler did not produce usable output, and auth needs secret handling.

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
- **Structured logging and error tracking**: JSON logs with a run id. Only worth it if run history is added.
