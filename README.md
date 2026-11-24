# GenNAI

GenNAI takes the URL of a web page and tests it end to end with one command:

1. It finds the interactive elements and builds locators that are checked for uniqueness.
2. It designs test cases with classic test-design techniques (equivalence partitioning, boundary values, state combinations) and prioritises them.
3. It writes a runnable pytest + Playwright suite with Page Objects.
4. It runs the suite and writes one self-contained HTML report. Failures are classified, with screenshots.

It is for developers who want a fast first pass of UI checks on a page, including invalid input and elements that something else covers, without writing the tests by hand. An optional free-tier LLM can propose extra test cases. It only returns JSON, and a deterministic gate filters that JSON before anything becomes code.

## How it works

```mermaid
flowchart LR
    U[URL] --> G{URL guard}
    G --> P1["Phase 1: explore<br/>elements + unique locators"]
    P1 --> P2["Phase 2: generate<br/>EP, BVA, state, click; prioritise"]
    P1 -. "sanitised, delimited data" .-> L[("optional LLM")]
    L -. "JSON test specs" .-> K{deterministic gate}
    K -- accepted --> P2
    K -- rejected --> X[counted in results]
    P2 --> P3["Phase 3: codegen<br/>pytest + Page Objects from fixed templates"]
    P3 --> P4["Phase 4: execute<br/>screenshots, failure classes"]
    P4 --> R[report.html + results.json]
```

| Phase | Module | What it does |
|---|---|---|
| 1 | `gennai/phase1_explore.py` | Loads the page once in Chromium (with `--max-pages N`, also up to N-1 same-origin pages it links to, breadth-first) and collects visible inputs, selects, checkboxes, buttons and links. It infers a semantic kind for each one: a text field named or labelled "email" is treated as an email field. It builds locator candidates (`data-testid`, `#id`, `[name]`, role plus accessible name, label, placeholder, text) and keeps only those that match exactly one element on its own page. Each element records the URL of its page. |
| 2 | `gennai/phase2_generate.py` | Builds the test cases (see the list below the table), removes duplicates, scores each test by element importance, required flag, form membership and technique, and keeps the top N. The cap is filled in coverage order: every element's best test, then every element's best negative test, then the rest by priority, with pages taking turns. |
| 3 | `gennai/phase3_codegen.py` | Writes `tests/` from fixed templates: `conftest.py` (browser fixtures, screenshot on failure), one Page Object per page whose fallback locator list is tried in order, and one test file per page (`test_generated.py`, `test_generated_p2.py`, ...) with one test function per case. Every value is embedded with `repr()`. Every generated file is compiled as a self-check before Phase 4 runs it. The generated folder runs with plain `pytest`. |
| 4 | `gennai/phase4_execute.py` | Runs the suite in a subprocess with a timeout and parses the JUnit XML. It classifies failures as `page_unavailable` (HTTP error on load), `login_failed`, `element_intercepted`, `locator_not_found`, `timeout`, `assertion` or `other`, then writes `results.json` and `report.html` (rendered by `gennai/report.py`). The report is one self-contained file with clickable summary cards and five tabs: **Overview** (findings with steps, error and screenshot, and what each failure class means), **Tests** (search, filter by status, technique and failure class, sort, expand a row for its steps, locators and re-run command), **Coverage** (element × technique, coloured by result; click a cell to see those tests), **Elements** (what Phase 1 found, with constraints and every locator) and **Metrics** (time per phase; LLM response time, tokens and gate counts; slowest tests). |
| - | `gennai/llm.py`, `gennai/safety.py` | Optional LLM step, prompt building, the gate and the URL guard (see below). |

Phase 2 generates these test cases:
- **Equivalence partitioning:** a valid and an invalid partition per field kind, and required fields left empty.
- **Boundary values:** each `minlength`/`maxlength` and `min`/`max` limit, tested at the limit and one step outside it.
- **State combinations:** for each form, all fields valid, then each required field left empty in turn. The check is `form.checkValidity()`.
- **Click tests:** every button and link.

### Design decisions

- **Nothing is submitted.** Assertions use what the browser itself knows: `checkValidity()`, `maxlength` truncation, and selected and checked state. Click tests use Playwright's `click(trial=True)`, which runs every actionability check, including "is another element covering it?", but never clicks. The tool can therefore run against third-party pages without writing data.
- **One browser stack.** Playwright's sync API is used throughout. The course version mixed Playwright in Phase 1 with Selenium in the generated tests.
- **The deterministic core comes first.** Without an API key the tool is fully functional and says so in its output: `llm: not used: no LLM key configured`.

### LLM safety design

The tool sends content from arbitrary websites to a model and then executes code. The controls:

1. **Page content is untrusted data.** Labels, texts, placeholders and option values are stripped of HTML comments, control characters and zero-width characters, and each is truncated to 80 characters. The payload is JSON inside `<page_data>...</page_data>`. `<` and `>` are escaped, so page text can't close the block. The system prompt says the block is data and must never be followed as instructions. A test checks that a hostile label containing `</page_data> Ignore all previous instructions...` produces exactly one closing delimiter.
2. **The model never writes code.** It may only return `{"tests": [...]}`. Each item is validated by a strict pydantic schema (`extra="forbid"`, an allow-list of actions and expectations, length limits). Phase 3 turns accepted specs into code from the same fixed templates as the algorithmic tests.
3. **A deterministic gate: the model proposes, the gate disposes.** A spec is accepted only if its element id was detected in Phase 1, its action fits that element's kind, and, for selects, its value is one of the detected options. Everything else is dropped and counted in `results.json` as `rejected_hallucinations` or `rejected_schema`.
4. **Overload and cost limits.** A hard cap applies to HTTP attempts per run (`GENNAI_LLM_MAX_CALLS`, default 3), along with caps on input characters and `max_tokens`, request timeouts, and client-side spacing below each provider's per-minute limit. A 5xx, timeout or network error moves straight to the next provider, and the chain gets one more pass after a 2 s pause. On a 429 the provider cools down first. When nothing is left, the run continues with the algorithmic tests and reports `llm: unavailable: ...`.
5. **Scope guard.** Only `http`/`https`. Hosts that resolve to an address that is not globally routable (loopback, private, link-local, carrier-grade NAT, reserved) or to a multicast address are refused unless you pass `--allow-local`. The final URL is checked again after redirects, although by then the redirect has already been requested. LLM base URLs must use `https://`, because the key is sent as a bearer token.
6. **No secrets in logs.** Prompts are logged only at `DEBUG`. API keys are excluded from `repr` and never logged, and a test asserts this.

The gaps that remain are listed in [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md).

## Quickstart

Requires Python 3.11+. Commands below are for Windows PowerShell. On macOS/Linux, use `source .venv/bin/activate` and `cp`.

```powershell
git clone https://github.com/seifheakal/gennai
cd gennai
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
```

Optional LLM step: copy `.env.example` to `.env` and set `GEMINI_API_KEY` and/or `OPENROUTER_API_KEY`. Every variable is documented in `.env.example`, and all of them have safe defaults.

```powershell
copy .env.example .env
```

Run the bundled offline demo, or any page you are allowed to test:

```powershell
python gennai.py demo
python gennai.py run https://the-internet.herokuapp.com
```

Flags: `--out DIR` (default `runs/<host>_<timestamp>/`, or `runs/<host>_<port>_<timestamp>/` when the URL has a port), `--headed` (show the browser), `--max-tests N` (default 25), `--max-pages N` (default 1, at most 20), `--review` (approve tests before they run), `--no-history` (don't record this run), `--allow-local` (`run` only), `--login` (`demo` only: test the demo's page behind a sign-in).

**Multi-page crawling.** `--max-pages N` also tests up to N-1 pages that the start page links to:

```powershell
python gennai.py demo --max-pages 2
python gennai.py run https://the-internet.herokuapp.com --max-pages 4
```

- Links are followed breadth-first from `<a href>` only, and only on the start page's origin (same scheme, host and port; this is always on). Pages are deduplicated by URL without the fragment and with the query sorted.
- Links whose URL or text looks like logout, sign-out, delete, remove, destroy or unsubscribe are never followed. Neither are links to files such as `.pdf` or `.zip`, or responses that are not HTML.
- Every crawled URL, and the URL it redirects to, passes the same local/private-address check as the start URL.
- A linked page that fails to load (HTTP error, redirect to another origin, bot challenge) is logged and skipped; only the start page's failure stops the run.
- `GENNAI_MAX_ELEMENTS` applies per page; `--max-tests` is shared by all pages. The report and `results.json` list the crawled pages and the page of each test.

**Human review.** `--review` pauses between Phase 2 and Phase 3:

```powershell
python gennai.py run https://the-internet.herokuapp.com --review
```

- GenNAI writes `test_cases.json` with `"approved": true` on every case, prints its path and waits.
- Open the file and set `"approved": false` on a case (or delete it) to drop it. You may also change a case's `title` and its step `value`s, for example to try your own input.
- Press Enter to continue. Only approved cases are turned into code and run. The summary, `results.json` (`"review"`) and the report show how many were approved, edited and rejected.
- Any other change is refused with an error naming the case: ids, targets, expectations and which elements a case touches decide the generated code, so they must stay as generated. Ctrl+C or closed input cancels the run (exit 2) before any test is generated.
- Nobody is simulated: without `--review` every generated case runs, as before.

**Pages behind a login.** Put the login page and an account in `.env`. All three are needed, or none:

```
GENNAI_LOGIN_URL=https://example.com/login
GENNAI_LOGIN_USER=...
GENNAI_LOGIN_PASSWORD=...
```

- GenNAI opens the login URL, fills the first visible password field and the first text or email field of its form, and presses Enter. Login succeeded when no password field is left; otherwise the run stops with exit 2 (`login ... failed`).
- Phase 1 explores (and crawls) with that session. Logout-looking links are never followed, so the session survives the crawl.
- The generated `conftest.py` logs in once per test session and starts every test from that session. It contains only the login URL: the user name and password are read from the environment (`GENNAI_LOGIN_USER`, `GENNAI_LOGIN_PASSWORD`), which GenNAI passes to the test run. A login that fails during the test run is reported as `login_failed`.
- The user name and password are never logged, written to an output file or sent to the LLM. Phase 1 also never reads the value of any password field.
- `python gennai.py demo --login` signs in to the demo's own test account (`demo` / `demo-pass`, shown on `demo/login.html`) and tests `demo/account.html`, which redirects to the sign-in page without a session. The demo's "session" is a cookie set by page script: it exercises the login fixture, not real security.

**Notifications.** Off unless configured in `.env`. When a run finishes, GenNAI sends a one-line summary (URL, passed, failed, failure classes, flaky count, report folder) to each configured channel:

- **Slack** (or any Slack-compatible incoming webhook): `GENNAI_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...`. It must be `https://`; `http://127.0.0.1:` and `http://localhost:` are also accepted, for local receivers.
- **Email**: `GENNAI_SMTP_HOST`, `GENNAI_SMTP_PORT` (default 587; 465 uses implicit TLS), `GENNAI_SMTP_USER`, `GENNAI_SMTP_PASSWORD`, `GENNAI_EMAIL_FROM` (default: the SMTP user) and `GENNAI_EMAIL_TO`. STARTTLS is used when the server offers it; without TLS the password is never sent and the email is not sent.
- A failed notification is a warning, not an error: the run still exits 0. The result per channel (`sent` or `failed: ...`) is in the summary and in `results.json` (`notifications`). The webhook URL and the SMTP password are never logged.

**Web UI.** `python gennai.py ui` serves a chat-style page on http://127.0.0.1:8765/ (`--port` to change it):

- Type a URL (or `demo`) and the number of pages. Each phase posts a line as it finishes, then a summary line with a link to that run's `report.html`.
- It calls the same `run_pipeline` as the CLI and uses the same `.env` settings (LLM, login, notifications), output folders and run history.
- It listens on 127.0.0.1 only and runs one test at a time. Only public URLs and `demo` are accepted (no `--allow-local`), and there is no review step (that needs a terminal).
- A run can only be started by a JSON POST from the page's own origin with the right `Host` header, so another website open in the same browser can't start one. The report is served with a Content-Security-Policy that blocks network requests.

**Run history and flaky tests.** Every run is appended as one JSON line to `runs/history/<site>.jsonl` (`demo.jsonl` for the demo). The file is only ever appended to, never rewritten:

- A test is matched across runs by what it does: the page path, the attributes of the elements it touches, its actions and values, and its expectation. Its `t01`-style id is only a priority rank and is not used, and neither is the host, so the demo's random port doesn't matter.
- A test is marked **flaky** when it both passed and failed within the last `GENNAI_FLAKY_WINDOW` runs of that site (default 5, this run included).
- The report has a "Recent runs" column (for example `✓ ✓ ✗ ✓ flaky`, with `·` where the test did not run) and a history line in its header. `results.json` has `history` and `flaky` on each test and `summary.flaky`; the terminal summary has a `history:` line.
- `GENNAI_HISTORY_DIR` moves the history folder; `--no-history` skips recording a run.

Each run writes `elements.json` (Phase 1), `test_cases.json` (Phase 2), `tests/` (Phase 3), `results.json`, `report.html` and `screenshots/` (Phase 4). The terminal shows a short summary: results, time per phase, LLM calls with average response time and tokens, and the report path.

Exit codes:
- `0`: the pipeline finished. Failed generated tests are findings, not errors.
- `2`: bad input, a refused URL, a site that is unreachable or blocks automation, or a cancelled or invalid review.
- `3`: no testable elements.

Run the tool's own tests:

```powershell
python -m pytest -q
python -m ruff check .
```

## Example output

`python gennai.py demo` serves `demo/index.html`, a small sign-up page with two planted problems, and finds both. (`demo/contact.html`, a contact form linked from it, is only tested with `--max-pages 2` or more.)

![GenNAI report for the demo page](examples/demo/report.png)

- **Submit: is clickable → `element_intercepted`.** A fixed cookie banner covers the Submit button. The report names the covering element (`<div id="cookie" ...> intercepts pointer events`) and embeds the screenshot. The course version found the same kind of bug on a real site: an ad iframe covered automationexercise.com's Subscribe button.
- **Email: invalid partition (not an email) → `assertion`.** The field is labelled "Email" but is `type="text"` with no validation, so `not-an-email` is accepted. Phase 1 inferred the email kind from the label.
- The "Load offers" button is added by script 1.5 s after load. It is still found and its test passes.

The Coverage tab shows every element against every technique. The two red cells are the two planted bugs, and clicking one lists its tests:

![Coverage tab for the demo page](examples/demo/report-coverage.png)

The Metrics tab shows time per phase, the LLM call with its response time and tokens, and what the gate accepted:

![Metrics tab for the demo page](examples/demo/report-metrics.png)

Full outputs from all three runs are in [`examples/`](examples/): reports, JSON, generated test code and screenshots. [SHOWCASE.md](SHOWCASE.md) maps each course requirement to where the tool shows it.

## Results

Measured on 2026-11-24 on Windows 11, Python 3.13, headless Chromium, with the LLM step on (`gemini-3.5-flash-lite`). These are the final runs, saved in `examples/`.

| Site | Elements | Tests (ep / bva / state / click / llm) | Passed | Failed | Failures by class | Run time |
|---|---|---|---|---|---|---|
| `demo/` (local) | 7 | 24 (8 / 7 / 3 / 2 / 4) | 22 | 2 | element_intercepted 1, assertion 1 | 21.7 s |
| automationexercise.com | 18 | 21 (3 / 0 / 0 / 17 / 1) | 20 | 1 | locator_not_found 1 | 49.0 s |
| the-internet.herokuapp.com | 40 | 25 (1 / 0 / 0 / 23 / 1) | 25 | 0 | none | 48.2 s |

Without a key, the same pages give 20 / 20 / 25 tests. On the demo that run had 18 passed with the same 2 failures.

The demo row above was measured before the demo page gained its "Contact us" and "Log out" links for multi-page crawling. Re-run without a key after that change, the single-page demo has 9 elements and 22 tests (ep 8 / bva 7 / state 3 / click 4): 20 passed, with the same 2 failures.

**Multi-page crawl** (measured 2026-11-24, same machine):

| Run | Pages crawled | Elements | Tests | Passed | Failed | Run time |
|---|---|---|---|---|---|---|
| `demo --max-pages 3`, no key | 2: `/`, `/contact.html` (`Log out` skipped; `./` and `#form` links deduplicated) | 15 | 25 (14 on `/contact.html`) | 24 | 1 (element_intercepted) | 17.6 s |
| `run https://the-internet.herokuapp.com --max-pages 4`, LLM on | 4: `/`, `/abtest`, `/accessibility_issues`, `/iframes_advanced` | 54 | 25 (10 / 3 / 9 / 3 per page) | 25 | 0 | 88.3 s |

That run used the earlier selection rule; it left the planted email bug out of the 25-test cap. The coverage-order rule (see Phase 2) keeps both planted bugs: see "Demo cap" below.

**LLM step, live.** Response time and tokens are the provider's own `usage` numbers, recorded per call in `results.json` and shown in the report.

| Site | Calls | Response time | Tokens in / out | Proposed | Accepted by the gate | Rejected (hallucination / schema) | In final suite | Passed |
|---|---|---|---|---|---|---|---|---|
| `demo/` | 1 | 1.73 s | 577 / 256 | 7 | 7 | 0 / 0 | 4 | 4 |
| automationexercise.com | 1 | 1.23 s | 1,133 / 222 | 6 | 6 | 0 / 0 | 1 | 1 |
| the-internet.herokuapp.com | 1 | 1.55 s | 2,309 / 375 | 7 | 7 | 0 / 0 | 1 | 1 |

- Accepted specs that duplicate an algorithmic test are removed, and the rest compete for the 25-test cap by priority. That is why fewer model tests reach the final suite.
- The gate rejected nothing on these three pages. That is a small sample, not evidence that the model never hallucinates. The rejection path is covered by the tests.
- Free models are often overloaded. During testing, `gemini-3.8-flash`, `gemini-3.6-flash` and the Gemma fallback (`gemma-4-31b-it`) often answered HTTP 503 ("high demand"), and one `gemini-3.5-flash-lite` call hung until the timeout. Those runs fell back cleanly to the algorithmic tests, and the report lists every failed call with its outcome. The per-call timeout is now 45 s, so a hung call costs less than a minute.

**Demo.** Both planted issues are caught on every run, with the same classes. The demo page is static, so the result is deterministic.

**automationexercise.com.** Five earlier runs that day gave 19, 20, 17, 18 and 18 passed out of 20, in that order. The failures exposed two tool bugs, both fixed and listed in the git log:
- Generated tests navigated with the 5 s action timeout. That caused 2 setup timeouts on a slow load.
- The site sometimes answers with HTTP 503 and a "heavy load (queue full)" page. Tests reported that as `locator_not_found`; they now report `page_unavailable` with the status code.

The remaining `locator_not_found`, on a "Tshirt" category link, appeared in 2 of the 5 runs, and on a "Dress" category link in the final run. The link's locators were unique during exploration but had no unique match on the test's own page load. That is real locator instability on a changing page (see [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md)). The course-era ad-iframe interception of the Subscribe button did not occur in these runs.

**the-internet.herokuapp.com.** The first run flagged the "Skip to content" link as a `timeout`. That was a false positive: the link sits off-screen until it is focused. Phase 1 now skips elements that lie entirely off-screen, and the later runs passed 25 of 25.


**Human review** (measured 2026-11-24 by driving the CLI's prompt from a script: wait for it, edit the file, send Enter):
- Demo, no key: 25 cases offered, 3 rejected, 1 step value edited, 19 approved. The rejected cases were absent from the generated code, and the edited value was in it.
- the-internet.herokuapp.com, `--max-pages 2`: 25 offered, 3 rejected, 22 run and passed. The LLM step was unavailable on that run (Gemini timed out, Gemma answered HTTP 503), so only algorithmic tests were offered.
- On the demo, the edited value turned a "length 1 (below minlength)" case into a failing `assertion`. An edited value is run as-is against the original expectation (see [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md)).

**Run history** (measured 2026-11-24, through the CLI):
- Demo, `--max-pages 2`, twice: every test was matched across the two runs (24 passed both times, 1 failed both times), 0 flaky. That is expected: the demo is deterministic.
- the-internet.herokuapp.com, `--max-pages 2`, three times: 24 tests matched in all three runs and passed each time, 0 flaky. The third run's LLM answered and added 1 new test, shown as not run in the first two. In the first two runs the LLM step was unavailable (HTTP 503 from both providers).
- No real flake showed up on these sites, so the flaky marker was checked by appending to the demo's history a run in which one passing test had failed. The next run marked exactly that test (`✓ ✓ ✗ ✓ flaky`). An integration test does the same.

**Login** (measured 2026-11-24 on the demo's sign-in page, no LLM key):
- `demo --login`: 5 elements, all from the account page behind the sign-in; 15 tests, 15 passed.
- The same through `.env`-style variables: `GENNAI_LOGIN_*` set in the environment and `run http://127.0.0.1:8931/account.html --allow-local` against a separately served `demo/`: 15 passed. The log said `logged in at http://127.0.0.1:8931/login.html` and nothing else about the account.
- The password string was in no file of either run's output folder. A wrong password stopped the run with `login ... failed: still on the login form after submitting it`.
- I did not run the login against the-internet.herokuapp.com: its `/login` takes the practice account shown on that page, and signing in to a third-party site is something to do yourself (`GENNAI_LOGIN_URL=https://the-internet.herokuapp.com/login`, then `run https://the-internet.herokuapp.com/secure`).

**Notifications** (measured 2026-11-24 with local receivers, not real Slack or a real mail server):
- A demo run with a webhook URL pointing at a local HTTP server and SMTP pointing at a local SMTP sink printed `notified: slack sent, email sent`. The receiver got the POST `{"text": "GenNAI finished http://127.0.0.1:58518/: 20 passed, 2 failed (element_intercepted 1, assertion 1), 0 flaky. Report: gennai_notify/report.html"}`, and the sink got an email with the subject `GenNAI: 20 passed, 2 failed` and the same text.
- With nothing listening on the webhook port, and an SMTP user configured against the sink (which offers no TLS), the run still exited 0 with `slack failed: URLError, email failed: SMTPException: server offers no TLS; not sending the password`. Neither the webhook path nor the password was in the output.
- Sending to a real Slack workspace or mail provider needs your own webhook or account and was not tested here.

**Demo cap** (measured 2026-11-24, after the coverage-order rule in Phase 2): `demo` three times with the LLM on (4-5 model tests in each suite): 23 passed, 2 failed (`element_intercepted`, `assertion`) every time. `demo --max-pages 2` three times: 23 passed, 2 failed each time, but the free models answered 503 on all three, so no model tests were in those suites; one earlier 2-page run on the same rule with 3 model tests also caught both. The UI's `demo` at 1 and 2 pages caught both. A unit test feeds 15 model proposals at the highest-scoring fields on two demo-like pages and checks both bugs stay in the 25; under the previous rule all four of those tests were cut.

**Web UI** (measured 2026-11-24 in a browser, LLM on):
- `demo` with 2 pages: the page showed "Phase 1: found 15 elements on 2 page(s)", then Phase 2 (25 cases, 4 from the LLM), Phase 3, Phase 4, and "25 passed, 0 failed, 0 flaky" with a working report link. That run used the previous selection rule; see "Demo cap" above for the rule that keeps both bugs.
- the-internet.herokuapp.com with 2 pages: 43 elements, 25 tests (23 click, 1 ep, 1 LLM), 25 passed.
- A test starts a real server, runs the demo through it, and checks the request guards (wrong `Host`, a non-JSON POST, a foreign `Origin`, a path-traversal report path, and a local target).

**The tool itself.**
- 88 tests pass in about 2.5 minutes. They include:
  - five end-to-end runs against the local demo: single-page, multi-page crawl, a review that rejects and edits cases, run history marking a flaky test, and a run behind the demo's login (which also checks that the password appears in no output file or log line);
  - tests that the review step refuses structural edits, including an id that would inject code into a test function name;
  - a test that feeds hostile strings through code generation and parses every generated file;
  - a test that a spec referencing a non-existent element is rejected;
  - a test that response time, tokens and failed calls are recorded;
  - a test that page text containing `<script>` is escaped in the report.
- `ruff check` and `ruff format --check` are clean.
- The code is 2,540 lines of Python in `gennai.py` and `gennai/`, plus 140 lines of CSS and JavaScript that are inlined into the report. The course version had about 11,700 lines of Python across the phase folders and the web UI.

## Course constraints and what changed for the demo

GenNAI was built for a university Generative AI course. The course restricted the model itself: no paid providers, only free-tier APIs (the brief names Gemini Free and Hugging Face as examples), open-source or local models ([`prompts/course_brief.pdf`](prompts/course_brief.pdf)). In practice that meant older and smaller models. The brief graded hallucinated locators and steps, test validity, the visibility of response time and token usage, and the speed of the exploration phase. The aim was to measure the students' engineering rather than the model.

My answer was to put the work into the harness rather than rely on the model. Test design is done by a multi-phase pipeline with deterministic techniques: equivalence partitioning, boundary values, state combinations and prioritisation. Every element reference is validated. The committed course version makes no LLM API call at all. Its plan targeted the Gemini 2.5 Flash free tier ([`prompts/project_plan.md`](prompts/project_plan.md)), and all of its test cases came from the generators. The project received the best efficiency score in the class and the highest mark.

This public version has no course restriction. An optional LLM step uses a current free-tier model through a provider chain configured in `.env`. Any OpenAI-compatible endpoint works by name (`GENNAI_LLM_PROVIDERS`, plus `<NAME>_API_KEY`, `<NAME>_MODEL`, `<NAME>_BASE_URL` and `<NAME>_RPM`). The defaults were checked against the providers' own pages on 2026-11-24:

| Role | Provider | Model | Free-tier limits | Source |
|---|---|---|---|---|
| Primary | Google Gemini API (OpenAI-compatible endpoint) | `gemini-3.5-flash-lite` | "Free of charge" on the free tier. Google no longer publishes per-model free RPM/RPD; they are shown per project in AI Studio. The client spaces calls at 10/min by default (`GEMINI_RPM`). | [pricing](https://ai.google.dev/gemini-api/docs/pricing), [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits), [OpenAI compatibility](https://ai.google.dev/gemini-api/docs/openai) |
| Fallback | Google Gemini API, same key (`GEMMA_API_KEY=${GEMINI_API_KEY}`) | `gemma-4-31b-it` | "Free of charge"; the free tier is the only tier for Gemma. Spaced at 10/min by default. | [pricing](https://ai.google.dev/gemini-api/docs/pricing), [Gemma on the Gemini API](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api) |
| Optional third | OpenRouter (own key) | `google/gemma-4-31b-it:free` | 20 requests/min. 50 requests/day, or 1,000/day after buying at least 10 credits. | [limits](https://openrouter.ai/docs/api-reference/limits), [models API](https://openrouter.ai/api/v1/models) |

`gemini-3.5-flash-lite` is listed as free of charge and was the Gemini model that answered reliably during testing. The stronger `gemini-3.8-flash`, also free, returned HTTP 503 (high demand) on every attempt. To try it, set `GEMINI_MODEL=gemini-3.8-flash`. The Gemma fallback uses the same key, so one free Google key is enough; AI Studio shows the free limits per model, and a rate-limited Gemini call falls through to Gemma. The pricing page also says free-tier content is used to improve Google's products, so do not use the LLM step on confidential pages.

## How it was built

GenNAI was built with AI coding tools under my direction. For the course version (December 2025), I wrote the specifications in [`prompts/`](prompts/): the four phases, the test-design techniques, the locator strategy and the evaluation goals. Claude Code generated most of the implementation from them. That version had grown into about 11,700 lines of Python whose phases no longer connected. Phase 1 and Phase 2 used different locator schemas. The human-in-the-loop step approved tests with `random.random()`. The saved Phase 4 results contained zero tests.

This version (November 2026) was produced with Claude Code (Opus) from [`prompts/FINALIZATION_PROMPT.md`](prompts/FINALIZATION_PROMPT.md). I set the goals: finish rather than expand, use only measured claims, add the LLM safety basics and a free-tier model. The work rebuilt the four phases into one small package, deleted the parts that were simulated or broken, and added the gated LLM step. It was planned and reviewed by Opus, most of the code was written by Sonnet subagents, and every result was run before it was accepted.

The full story, including how the work was split between models and sessions and how each claim was checked, is in [BUILT_WITH_AI.md](BUILT_WITH_AI.md). There is also a visual one-page version, [docs/how-it-was-built.html](docs/how-it-was-built.html). The algorithms behind each phase are explained in [TECHNICAL.md](TECHNICAL.md).

## Where this fits in my development

GenNAI was my first serious AI project. Since then I have built AI tooling professionally: an AI assistant for a mailbox, and a larger knowledge-base pipeline for an engineering firm. Both are private. The table lists only items I verified in their code and tests. They show how this repo's known limitations are handled in that later work.

| Limitation here | How the later work handles it |
|---|---|
| Single LLM call per run and no visible provider state | The mailbox assistant has a provider chain (Gemini free tier, then an OpenRouter free model). It throttles requests client-side, sets a cooldown from `Retry-After` on 429 and a long cooldown when the daily quota is exhausted, and retries 5xx with backoff. A status function reports each provider's cooldown and last error. Tests cover the fallback and cooldown paths. |
| Basic prompt-injection defence | The mailbox assistant sanitises the model's Markdown output with `bleach` and a tag allow-list before rendering it. A test covers this. |
| The gate checks references, not meaning | In the knowledge-base pipeline the model only appends proposals to a staging file. A script allocates ids and checks required fields, then runs the full integrity checker against a shadow copy, and applies the proposals only if it comes back clean. Dedicated tests cover the gate. |
| Small test suite | The mailbox assistant has 181 mocked test functions. They include tests that fail if any delete or move call appears in the source. |
| No resumable stages, and run history is one plain file | The knowledge-base pipeline has 15 stages with `--dry-run`, `--only` and `--from`. Records are append-only and carry their source on every row, status is computed rather than stored, and corrections are new superseding records. |
| No integrity checks over output | The knowledge-base pipeline has 34 integrity checks that run as a pipeline stage. Running them before every commit is a written rule there, not an enforced hook. |

That later work has its own open list. The mailbox assistant still lacks CSRF protection, cost and quota guardrails before large scans, structured logging and schema migrations. For the knowledge-base pipeline, config-only onboarding of a second workspace and an MCP server are still plans.

## Limitations and future work

- [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) covers real flaws: heuristic locators, a same-origin link crawl and a form-only login, shallow assertions, an unsandboxed test run, review edits that are not re-checked, basic injection defence, a reference-only hallucination gate, and thin live evidence for the LLM step.
- [FUTURE_WORK.md](FUTURE_WORK.md) covers features that were left out or removed, and what to build next.
- [DEMO_SCRIPT.md](DEMO_SCRIPT.md) is a 2-3 minute walkthrough.
- [SHOWCASE.md](SHOWCASE.md) is the longer presentation guide: what to highlight in each phase, where each course requirement shows, and answers for the likely questions.

## Responsible use

Only test sites you own or have permission to test. The two public sites above are practice sites made for test automation. The tool keeps its footprint small:
- It never submits forms. Click tests are trial clicks.
- It enters only clearly fake data, for example `test.user@example.com`.
- It loads each page once to explore (one page by default, at most 20 with `--max-pages`) and once per test (at most 25 tests by default). It never follows links that look like logout or delete.
- It refuses local and private network targets unless you pass `--allow-local`.

## License

MIT, see [LICENSE](LICENSE).
