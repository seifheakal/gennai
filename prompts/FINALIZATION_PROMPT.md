> Used with Claude Code (Opus) to finalize this project in November 2026. Reference-project details were removed from this copy.

# TASK: Finish GenNAI into a clean, minimal, working, demo-ready repo

You are taking over a university project and turning it into a runnable portfolio piece I will show to an employer (a "Software Developer – AI & Automation" role). Work autonomously end to end. Do not stop to ask me questions unless truly blocked; make sensible decisions and report them at the end. Verify everything by actually running it. Never claim something works unless you ran it and saw it work.

## OPERATING PRINCIPLES (these override everything below)

**Use Ponytail.** Before doing anything else, install and enable the Ponytail plugin for Claude Code and work under it for the whole task:

```
/plugin marketplace add DietrichGebert/ponytail
/plugin install <plugin name shown by the marketplace, see the README "Install" section>
```

Source: https://github.com/DietrichGebert/ponytail . Read its README "Install" section for the exact second command. If the plugin cannot be installed, read `skills/ponytail/SKILL.md` from that repo and apply it manually as your working rules, and tell me. Run `/ponytail-review` on your own changes before finishing and `/ponytail-audit` once on the final repo, and fix what they flag.

What that means in practice:
- **Finish, don't expand.** This repo was already built. The goal is a clean, minimal, WORKING version of what already exists. Do NOT add features, modules, abstractions, config systems, dashboards, flags or docs that did not exist before unless strictly required for the one-command demo, the `.env` configuration, or the LLM safety basics in section 3c. When in doubt, leave it out and list it in `FUTURE_WORK.md`.
- **Reuse before writing.** Read the existing code first and trace how data really flows. Prefer fixing, reusing and deleting over adding. Before writing new code, check whether the repo, the standard library or an already-used dependency already does it.
- **Delete aggressively.** Dead code, duplicate docs, debug scripts, scratch outputs, overlapping `*_COMPLETE.md` / `*_FINAL_SUMMARY.md` files and unused layers go. Fewer files and fewer lines is a success metric. Report before/after file and line counts (measured, not estimated).
- **Small honest surface.** If an existing layer or feature doesn't work and can't be fixed cheaply, remove it and say so, rather than keep a broken or fake one.
- **Never cut** input validation, error handling, security or accessibility. Keep one small test for any logic with branching or parsing.
- **Every claim must be measured.** No marketing words, no emojis in docs.

**Save tokens: you (Opus) lead and review, subagents do the bulk work.**
- You plan, make the design decisions, write precise briefs, and review. Delegate the coding and mechanical work to subagents via the Agent tool with `model: "sonnet"` (use `haiku` for trivial mechanical jobs such as deleting clutter, renaming `promts/` to `prompts/`, grepping for TODOs, line counts, running the secret scan). Do not write large amounts of code yourself.
- Each brief must be self-contained: the goal, the files/area it owns, the constraints from this spec that matter (Ponytail rules, `.env` config, no secrets, no copying from the reference projects), and what "done" looks like including the command that proves it. Give one subagent one set of files; never let two edit the same files at once. Run independent pieces in parallel (e.g. demo site, `.env`/LLM client, tests, docs), but keep the critical path sequential: first the working one-command pipeline, then everything that builds on it.
- You verify, not trust: after each subagent returns, read its diff and actually run the command that proves the result before accepting it. Send fixes back to the same subagent. Never report something as done because a subagent said so.
- Subagents may read the reference projects only if the brief says so, with the same read-only and no-secrets rules. Keep reading of those to one subagent that returns a short summary, so the details don't flood your context.
- Don't over-delegate: a tiny edit is cheaper to do yourself than to brief.

Sections 3 to 5 are a ceiling, not a to-do list. Implement the smallest version that satisfies each item, and skip anything marked optional unless it already exists in the repo and works. Must-haves, in priority order:
1. A working one-command pipeline on any URL, and a local demo site that deterministically shows a caught issue. **This is the first priority: get it working before anything else.**
2. `.env`-based configuration with a better free model (3a, 3b).
3. LLM safety basics (3c).
4. A short README with real measured results.
5. Cleanup, `KNOWN_LIMITATIONS.md`, `FUTURE_WORK.md`.
6. A few tests of the tool itself.

## 0. Context

- Repo: https://github.com/seifheakal/gennai (branch `main`). The working folder is given in the starter message. Work only there; do not modify any other copy.
- Project: an AI-driven automated web testing tool for developers. Intended pipeline (verify what really exists, see section 2):
  - Phase 1: element detection on a web page and locator generation
  - Phase 2: test case generation (Equivalence Partitioning, Boundary Value Analysis, State Combination Testing, prioritisation, human-in-the-loop feedback)
  - Phase 3: executable test code generation (pytest with Selenium/Playwright, Page Objects)
  - Phase 4: execution, results collection, analysis, history, report
  - Also in the repo: `web_ui/`, `promts/`, `test_failures/` (screenshots), `phase4_output/`.
- Built for a university Generative AI course, written almost entirely with AI coding tools (Claude Code), directed by me (Seif).
- GenNAI was my first serious AI project. I am now much more experienced; two later private projects show how I would do it today.

Reference projects were consulted privately (read-only, for patterns and to verify claims); their paths, names and confidential-handling rules are omitted from this copy.

## 1. Framing (must appear clearly in the README)

The correct story, which I (Seif) am telling you directly:
- The university course restricted which LLMs we could use through the API: only certain older / smaller models. The restriction was on the model itself. It was the course's way of measuring the students' engineering ability rather than the model's.
- Because the model was weak, I deliberately designed and engineered the harness around it (the multi-phase pipeline, validation, techniques like EP/BVA/state-combination, the human-in-the-loop feedback loop) to get better results than the raw model would. The project achieved the best efficiency score in the class and the highest mark.
- So: the limitation is the old/restricted LLM, not the approach and not the engineering. For this public demo there is no such restriction, so the tool uses a better, currently available model.

Add a short README section "Course constraints and what changed for the demo" that says this plainly and professionally: what the constraint was, that the harness was the engineering answer to it, the result (best efficiency score, highest mark; factual, no embellishing numbers you can't find), and that the demo uses a stronger model via a configurable provider. Not defensive or apologetic.

Do not invent specifics. Look in the repo (READMEs, `promts/`, docs, code) for the exact models and the grading/efficiency metric actually used, and quote only what you can support; keep the rest general.

## 2. Known problems from a review of the repo (fix all)

1. **Inflated, unsupported claims** in `phase4/COMPLETE_PROJECT_FINAL.md` and similar docs: "100% passing", "0% hallucinations", "Championship A+", "19,880+ lines", "98.5% confidence", "zero false positives", "85.6% coverage". The doc's own table totals about 10,800 lines. Delete these docs rather than rewrite them; put only measured numbers in the new README. If a metric can't be reproduced by a short script in the repo, drop the claim.
2. **Empty results**: `phase4_output/results/result_*.json` contain `"total": 0`. Delete them (real run output goes only under `examples/`).
3. **Clutter**: `__pycache__/`, `debug_*.py` scripts, a stray `--output-dir` folder, committed `.db` files, scratch HTML reports, duplicate docs. Delete them. Add a proper `.gitignore`.
4. **Hardcoded local Windows paths** (e.g. `C:\Users\seift\Downloads\...`) in committed JSON and probably code. Make all paths relative or arguments.
5. **No root README, no single entry point, no one-command way to run it.**
6. **The only real run was tiny**: `phase3/phase3_outputs_real/test_results_with_ids.txt` shows 8 generated tests against automationexercise.com: 7 passed, 1 failed (test_008, `ElementClickInterceptedException`, an ad iframe covered the Subscribe button). That failure is a genuine finding and the demo story. Keep the idea; make the tool classify it as "element intercepted". Auto-handling it (scroll into view, JS click) is optional and only if cheap.
7. **Docs vs reality**: the docs describe phases (e.g. `phase1_main.py`, a REST API, WebSocket, Slack/email, multi-language and multi-CI generation) that may not exist or work. Check each phase folder, run what exists, and keep only what works. The README must describe only what is really in the repo.

## 3. Main goal: ONE command that runs the pipeline on ANY website

A single entry point, e.g. `python gennai.py run <url>`, that:

1. Takes a public URL, with only the flags that are really needed (`--out`, `--headed`, and `--max-tests` if trivial).
2. Phase 1: loads the page (use whichever of Playwright or Selenium the existing code already uses; only migrate if clearly simpler), detects interactive elements (inputs, buttons, links, selects), generates locators with fallbacks.
3. Phase 2: generates test cases from those elements using the existing EP / BVA / state-combination generators and prioritises them. First check how the existing code calls an LLM (which API and model, where). Route that call through ONE small provider-agnostic client configured only by `.env` (see 3a). If no key is configured, the pipeline still runs using the algorithmic generators only and says clearly in the output that no LLM was used.
4. Phase 3: generates runnable pytest code with Page Objects. The generated code must run without manual edits.
5. Phase 4: runs the generated tests, takes a screenshot on failure, classifies failures (locator not found, element intercepted, timeout, assertion), and writes one self-contained HTML report plus JSON results. SQLite history, flaky reruns and parallel runs are optional: keep them only if they already exist and work.
6. Prints a short terminal summary and the path to the report.

Requirements:
- Works on Windows 11 with Python 3.11+, and stays cross-platform.
- Small pinned `requirements.txt`; document the browser install command (e.g. `python -m playwright install chromium`).
- Robust: timeouts everywhere; a clear error (not a crash) for unreachable or bot-blocked sites and pages with no testable elements.
- Safe: no destructive actions, no real personal data, clearly fake test data, low request rate. For sites the user owns or has permission to test; say so in the README.
- Keep the existing 4-phase structure where it is sound. Refactor only as needed. Fix bugs you find.
- A small test suite of the tool itself: a few unit tests (generators, locators, failure classifier, the LLM safety checks in 3c) and one integration test against the local demo site served by Python's `http.server`, so it needs no internet. All must pass.
- A minimal GitHub Actions workflow that runs lint and tests (optional if it adds more than ~15 lines).

## 3a. Better model for the demo (free tier) and configuration

The original project was limited to old models by the course. For the demo, use a stronger model on a free tier.
- The best source is the provider-chain notes in one of my later private projects (at the time of writing: Gemini 3.1 Flash-Lite on the Google AI Studio free tier as primary, and an OpenRouter free model as fallback, with the request-per-minute and per-day limits noted there). Read them.
- Then **verify against the providers' official docs today**: current model names, whether a newer or stronger free model exists, and the current free limits. Do not trust the numbers in my old notes or your memory. Pick the best currently available free model, keep a second provider as fallback, and report model, limits and source links in the README.
- Follow the same design as that `llm_client.py` but keep it SMALL (one file): provider chosen by `.env`, timeouts, limited retries on transient errors, client-side request spacing under the per-minute limit, cooldown/fallback on 429 or exhausted daily quota, clear error when keys are missing. Do not copy my file; write a minimal version for this repo. Do not add more providers than needed.
- A before/after comparison (old restricted model vs new model on the same site) is optional.

## 3b. Engineering standards (make it look like a professional engineer built it, without bloat)

- **Configuration**: all secrets and settings via environment variables loaded from `.env` (e.g. `python-dotenv`). Commit a `.env.example` listing every variable with a placeholder and a one-line comment. `.env` is in `.gitignore`. Validate settings at startup and fail fast with a clear message naming the missing variable (never print the secret). Nothing hardcoded: no keys, URLs, paths or model names in code. Anything not set in `.env` must either have a safe documented default or produce a clear error, never a crash or a silent wrong behaviour.
- **Code quality**: clear module boundaries, type hints on public functions, short docstrings where non-obvious, no dead code, consistent formatting. Minimal `pyproject.toml` with `ruff` lint and format config, run clean. `logging` instead of `print` outside the CLI summary. `pathlib` for paths. Specific exceptions, no bare `except`.
- **Reproducibility**: pinned dependencies, one install command, one run command, works from a fresh clone.
- **Tests and CI**: as in section 3.
- **Git hygiene**: small logical commits with clear messages.
- **Security**: no secrets in the tree; secret scan before finishing.
- Proportionate: a small repo with a few well-organised files, not a framework.

## 3c. LLM safety basics (implement the smallest version; write the rest up honestly)

The tool sends content from arbitrary websites to an LLM and then turns the result into test code that gets executed. That is an injection and overload risk. Do these, minimally:
1. **Treat page content as untrusted data.** Put page text and element data in a clearly delimited data block in the prompt and tell the model that it is data and must never be followed as instructions. Strip or neutralise obviously hostile content (hidden text, HTML comments, very long strings) and truncate every page field to a fixed size.
2. **The LLM never writes executable code directly.** It may only return structured JSON (test case specs) which is validated against a strict schema. Phase 3 turns validated specs into code from fixed templates. Reject or drop anything that does not parse or does not match the schema.
3. **Deterministic gate (the pattern from my knowledge-base project: the model proposes, a deterministic check disposes).** Every test case must reference only elements that Phase 1 actually detected and only values from an allow-list of action types. Anything referencing a non-existent element, or an unknown action, is dropped and counted in the report as a rejected hallucination. This also gives a real, measurable hallucination number for the README.
4. **Overload and cost protection**: a hard cap on LLM calls per run, a cap on input size and on `max_output_tokens`, timeouts, client-side rate spacing and backoff (3a), and a clean stop with a clear message when the quota is hit (fall back to the algorithmic generators).
5. **SSRF and scope guard for the CLI**: by default refuse URLs that resolve to localhost, private or link-local ranges, and non-http(s) schemes; allow them only with an explicit `--allow-local` flag (the local demo uses it).
6. Log what was sent to the LLM at debug level only, without secrets.

Anything in this area that you judge too expensive to do properly (e.g. a stronger injection classifier, sandboxing the test run, per-user quotas, auditing for the model leaking its prompt) goes into `KNOWN_LIMITATIONS.md`, not into the code.

## 4. Demo

- `demo/` with one small local HTML site: a form with validation, a button that gets covered by an overlay, and one dynamically loaded element. It works offline and deterministically shows at least one real caught issue.
- Run the full pipeline on the local demo and on https://automationexercise.com and https://the-internet.herokuapp.com (practice sites). Save the real HTML report, JSON and failure screenshots under `examples/`.
- `DEMO_SCRIPT.md`: a 2–3 minute plain-English walkthrough I can follow while screen-recording and doing a voice note: what to run, what to point at, what to say. Cover the problem it solves, how it was built, which AI tools were used (Claude Code for most of the implementation), and what I'd improve next. Keep it short.

## 5. README (root, short)

- One paragraph: what it is and the problem it solves.
- Pipeline diagram in Mermaid only (no exported images).
- Quickstart: install, `.env` setup (point to `.env.example`), the one command, where output appears.
- Example output: one real report screenshot and the real caught issue.
- Short architecture overview of the phases and key design decisions, including the LLM safety design (3c).
- "Results": a table of numbers you actually measured (sites tested, tests generated, pass/fail, failures by class, rejected hallucinations, run time).
- "Course constraints and what changed for the demo" per section 1, plus which free model is used and its limits with the source link.
- "How it was built": built with AI coding tools (Claude Code) under my direction; what I decided versus what the tool generated; the prompts are in `prompts/`.
- **"Where this fits in my development"**: a short, honest, generic section (no client names, no data, no confidential details). GenNAI was my first serious AI project. Since then I built AI tooling professionally (an AI mailbox assistant, and a larger knowledge-base pipeline for an engineering firm). Say, based only on what you VERIFIED in the reference projects, which of this repo's known limitations are already addressed there and how, in a small table: limitation, how the later work handles it. Likely candidates to verify (do not state any you did not confirm in the code or tests): provider fallback chain with throttling and cooldowns; sanitising LLM output before rendering (bleach); strict schemas and a deterministic validation gate between the model and the data; a large mocked test suite; enforced safety guarantees backed by tests; staged, resumable pipeline with `--dry-run`/`--only`/`--from`; immutable provenance-tracked records; integrity checks run before every commit. Also be honest about what the later work itself still lists as not done (its own `FEATURE_WORK.md` / `FUTURE_PLAN.md`), but only briefly. No bragging, no numbers you can't back.
- Limitations and links to `KNOWN_LIMITATIONS.md` and `FUTURE_WORK.md`.
- Responsible use note.

## 6. Cleanup, structure, prompts folder and the three docs

- Rename `promts/` to `prompts/` and update every reference.
- **Add THIS prompt to the repo**: save the full text of this task (including the Ponytail principles) as `prompts/FINALIZATION_PROMPT.md`, with a one-line header saying it was used with Claude Code (Opus) to finalize the project. Remove the "Reference projects" file paths and the confidential-handling details from that saved copy, replacing the block with one line saying reference projects were consulted privately. Reference it from the README "How it was built" section. Also add a short `prompts/README.md` index (one line per prompt file, what it was used for). Read the existing prompt files first so the index is accurate; do not rewrite or invent them.
- Simple structure, e.g.: `gennai/` package (phase subpackages), `gennai.py` entry point, `tests/`, `demo/`, `examples/`, `prompts/`. Don't create folders that would stay empty.
- Remove hardcoded paths, secrets, large binaries, `__pycache__` and `.db` files from git. Run a secret scan (grep for keys, tokens, emails, passwords) before finishing and report what it found.
- Add an MIT LICENSE if none exists.
- **`KNOWN_LIMITATIONS.md`** (repo root): the candid list of real flaws that are too expensive or risky to fix now. For each: what it is, impact, why it was left (honestly: time limits of the university project, or cost/risk of the fix), and what would be needed before production. Start from these and add what you find as you work: weak or heuristic locator strategy; no login/auth flows; single-page only; small evaluation; test run is not sandboxed; injection defence is basic (3c); no per-user quotas or cost tracking; hallucination check only validates references, not semantics; the original course-imposed model constraint and its effect on design; anything from 3c you did not implement. Keep it short and factual, a clean list, not an apology.
- **`FUTURE_WORK.md`** (repo root): additional features and ideas, separate from limitations. One line each: what, where it would go, why it was left out. Include everything you skipped under the Ponytail rules, every `TODO`/`FIXME`/stub/empty file you find anywhere in the repo (grep for `TODO`, `FIXME`, `XXX`, `NotImplemented`, `pass  #` stubs; then remove them from the code so the doc is the single path forward), and seed it with these ideas from my later projects, after reading the reference projects and keeping only the ones that genuinely fit (add your own better ones too):
  - evidence-grade run records: every failure linked to a screenshot, DOM snapshot and the locator provenance; append-only run history with status computed at render time, never stored;
  - integrity checks over run output (a `validate` command) that run in CI and before commit;
  - a staged, resumable pipeline (`--dry-run`, `--only <stage>`, `--from <stage>`);
  - deterministic core plus a thin LLM layer, so the tool is fully useful with no model and the model only adds enrichment;
  - the LLM proposes, a deterministic gate disposes: extend it from element references to expected-value semantics;
  - provider fallback chain with live quota/cooldown status and cost tracking;
  - flaky-test detection and reconciling real regressions versus flake across runs;
  - self-healing locators using the LLM, with human approval;
  - multi-page crawling and authenticated flows;
  - exposing the tool as an MCP server / Claude Code slash command (`/run-gennai <url>`);
  - a generated architecture map of the repo;
  - structured logging, error tracking, and schema migrations if history storage is kept.
- Git: do NOT rewrite history or force-push. Work on a new branch `finalize-demo` with clean, logical commits. When the demo is verified working, push that branch to `origin` (`git push -u origin finalize-demo`) and do not touch `main`. I will review and merge it myself. Never commit secrets.

## 7. Verification (show evidence in your final report)

- Fresh virtualenv, install from `requirements.txt` only, run the one command on the local demo: passes end to end. Do this FIRST, before cleanup.
- Same on automationexercise.com and the-internet.herokuapp.com (or explain precisely how a site blocks automation).
- The tool's own test suite passes (paste the summary line), including a test that a hostile string in page content is not treated as an instruction and that a spec referencing a non-existent element is rejected.
- The overlay / intercepted-click case: show it caught and classified correctly.
- Run once with no API key to show the offline fallback works and says so.
- If history or flaky detection was kept, show two runs working. If it was removed, say so.
- Every README claim maps to something you measured or verified in code. The "Where this fits in my development" table contains only items you verified. List any claims you removed.
- No absolute local paths, no secrets, no content from the reference projects in the tree.
- Re-read this task once at the end and check each section against what you did; list anything you skipped and why.

## 8. Final report

Give me: (1) what changed, by commit; (2) before/after file and line counts; (3) exact commands to run the demo; (4) the measured results table; (5) which free model and limits you chose, with sources; (6) anything still weak or unverified, stated plainly; (7) a suggested 3-sentence repo description and a 3-sentence CV description. Keep it concise and honest. Prefer fewer, solid features over many half-working ones.
