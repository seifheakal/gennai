# Showcase guide

How to present GenNAI: what to run, what to point at in each phase, and how each course requirement shows up.

- For a 2-3 minute version, use [DEMO_SCRIPT.md](DEMO_SCRIPT.md).
- This guide is for a 10-minute demo or a code defence.
- Every number here comes from the saved runs in [`examples/`](examples/) (2026-11-24, Windows 11, Python 3.13, `gemini-3.5-flash-lite` on the free tier).

## Before you start

1. Install once (README Quickstart). Put a free Gemini key in `.env` if you want the LLM step. Without a key everything else still runs.
2. Run `python -m pytest -q` once. It warms up Chromium and shows 40 passing tests if anyone asks.
3. Open the three saved reports in browser tabs as a backup: `examples/demo/report.html`, `examples/the-internet/report.html` and `examples/automationexercise/report.html`. If the network or the free model is slow on the day, show those instead.
4. Have a terminal open in the repo folder, with a font large enough to read.

## The pitch (one sentence)

"You give GenNAI a URL. It finds the interactive elements, designs test cases with classic test-design techniques, writes a runnable pytest + Playwright suite, runs it and hands you one report with the findings, screenshots, metrics and coverage."

## Run order (about 10 minutes)

| Step | Command or file | Show | Time |
|---|---|---|---|
| 1 | `python gennai.py demo --headed` | The browser window opening the page, then the terminal summary | 1 min |
| 2 | The `report.html` path printed at the end | The report tour below | 3 min |
| 3 | `python gennai.py run https://the-internet.herokuapp.com --headed` | The same pipeline on a public site: 40 elements, 25 tests | 1.5 min |
| 4 | `runs\<run>\tests\test_generated.py` and `tests\pages\*.py` | The generated code and the Page Object | 1.5 min |
| 5 | `gennai/safety.py` and `tests/test_llm.py` | The gate and the hostile-input tests | 1.5 min |
| 6 | `KNOWN_LIMITATIONS.md` | What is missing, said plainly | 1 min |

The terminal summary from step 1 looks like this. The numbers vary a little with the model's answer.

```
GenNAI summary
  elements:  7
  tests:     state=3, bva=7, llm=4, ep=8, click=2
  results:   22 passed, 2 failed
  failures:  element_intercepted=1, assertion=1
  llm:       used: gemini/gemini-3.5-flash-lite
  llm calls: 1, avg response 1.73s, tokens 577 in / 256 out
  phases:    explore 4.3s, llm 1.73s, generate 0.0s, codegen 0.02s, execute 15.62s
  time:      21.7s
```

## Report tour (3 minutes)

The report is one HTML file with no server and no internet needed. It opens in any browser, works in light and dark mode, and can be emailed as it is.

1. **The top.** A red "2 findings" badge, then the cards: elements, tests, passed, failed, coverage, run time, LLM response time and tokens. Every card is clickable.
2. **Overview tab.** The two findings, each with:
   - a one-line meaning of its failure class;
   - its steps;
   - the first line of the error, with the full error one click away;
   - the screenshot. Click it to enlarge.

   Point at the cookie banner in the first screenshot. Below the findings are the failure classes with their meanings, and a pass/fail bar per technique.
3. **Click the "Failed" card.** You land on the Tests tab, filtered to the two failed tests. Then:
   - Click **Clear filters**.
   - Type `email` in the search box.
   - Click the `state` chip to show how the filters combine. That leaves the 3 form-level tests that fill the Email field.
   - Click a row to expand it. It shows the steps, the locators tried in order, and the command to re-run only that test.
4. **Coverage tab.** Every element against every technique. Click the red `ep` cell on the Email row: the Tests tab opens with exactly the 2 tests that touch Email with equivalence partitioning, one of them failed. The "Not covered" chip shows any element the 25-test cap left out.
5. **Elements tab.** What Phase 1 saw:
   - kind and HTML type (Email is `input[type=text]`, but its kind is `email`);
   - constraints (`required, length 2-30`, `range 18-120`);
   - every locator, in the order the tests try them.
6. **Metrics tab.** Time per phase as bars, the gate counts, every LLM call with its outcome, response time and tokens, and the slowest tests.

## What to highlight in each phase

### Phase 1: Explore (`gennai/phase1_explore.py`, output `elements.json`)

What happens: Chromium loads the page once and waits 2 s, so that elements added late by script appear too. It collects the visible inputs, selects, checkboxes, buttons and links.

Highlights:
- **No hallucinated locators, by construction.** Each element gets up to 7 locator candidates (`data-testid`, `#id`, `[name]`, role plus accessible name, label, placeholder, text). Only candidates that match exactly one element on the live page are kept. The report's Elements tab lists every kept locator in the order the tests try them.
- **It infers what a field means, not only its HTML type.** The demo's Email field is `type="text"`. Phase 1 still marks it as `email` from its label, and that is why Phase 2 could catch the planted bug.
- **It finds dynamic content.** The demo's "Load offers" button is added 1.5 s after load. It is found and tested.
- **It skips what a user can't see.** Off-screen elements, like a skip link that only appears on focus, are left out. That removed a false positive on the-internet.herokuapp.com.

Number to quote: explore took 4.3 s on the demo (7 elements), 5.8 s on the-internet (40 elements) and 9.4 s on automationexercise.com (18 elements). The course graded explore speed.

### The LLM step (`gennai/llm.py`, `gennai/safety.py`)

What happens: the element list goes to a free-tier model, which may propose extra test cases.

Highlights:
- **Free tier only.** The chain is Gemini `gemini-3.5-flash-lite`, then Gemma on the same free key, then an optional OpenRouter free model. With no key the tool says `llm: not used` and still runs fully.
- **The model never writes code.** It returns JSON specs only. A deterministic gate accepts a spec only if the element exists, the action fits the element, and a select value is a real option. Everything else is counted as `rejected_hallucinations` or `rejected_schema`.
- **Page text is treated as untrusted data.** It is cleaned, truncated and fenced in a `<page_data>` block that page text can't close.
- **It fails safely.** On a 503, a timeout or a 429 it moves to the next provider, then falls back to the algorithmic tests. The report lists every attempt and its outcome.

Numbers to quote: in the final runs the model proposed 20 specs on 3 pages, and the gate accepted all 20. Calls took 1.23-1.73 s and used 577-2,309 tokens in and 222-375 out. Say that 20 specs are too few to claim a hallucination rate. The rejection path is proven by the tests instead.

### Phase 2: Design (`gennai/phase2_generate.py`, output `test_cases.json`)

What happens: test cases come from classic techniques:
- **Equivalence partitioning:** a valid and an invalid value per field kind, and required fields left empty.
- **Boundary values:** each `minlength`/`maxlength` and `min`/`max` limit, tested at the limit and one step outside it.
- **State combinations:** a whole form valid, then each required field left empty in turn.
- **Click checks:** every button and link.

The model's specs join the same list. Duplicates are removed, each case gets a priority score, and the top 25 are kept.

Highlights:
- **Coverage is visible.** The report's Coverage tab has one row per element and one column per technique. Green cells passed; red cells show failed out of total, and clicking a cell lists those tests. On the demo, all 7 elements are covered, and the two red cells are the two planted bugs.
- **Priorities are explainable.** The score is element importance plus whether the field is required, whether it is in a form, and the technique's weight. Sort the Tests tab by Priority to show the order.
- **Nothing is submitted.** Assertions use what the browser knows: `checkValidity()`, `maxlength` truncation, and checked or selected state. That makes the tool safe to run on sites you don't own.

### Phase 3: Code generation (`gennai/phase3_codegen.py`, output `tests/`)

What happens: the cases are written as a pytest + Playwright project with a Page Object.

Highlights:
- **Fixed templates, with values embedded via `repr()`.** Neither page text nor model output can inject Python. A test feeds a hostile label through codegen and parses every generated file.
- **Self-check before running.** Every generated file is compiled before Phase 4 starts, so a template bug stops the run with a clear message instead of a confusing pytest error.
- **Self-healing at run time, within limits.** Each element method in the Page Object tries its locator candidates in order and uses the first one that is unique on the current page.
- **The output stands on its own.** `runs\<run>\tests` runs with plain `pytest`, without GenNAI installed.

### Phase 4: Verification (`gennai/phase4_execute.py`, output `report.html` and `results.json`)

What happens: the suite runs in a subprocess and the JUnit results are parsed. Failures are classified as `page_unavailable`, `element_intercepted`, `locator_not_found`, `timeout`, `assertion` or `other`.

Highlights:
- **Evidence for every finding.** Each failed test shows its step-by-step plan, the error, and a screenshot taken at the moment of failure. The cookie-banner screenshot shows exactly what covers the Submit button, and the message names the covering `<div id="cookie">`.
- **Failure classes say what kind of problem it is.** `element_intercepted` is a UX bug. `assertion` is a validation bug. `page_unavailable` means the site was down, which is not a test failure.
- **One self-contained file.** Screenshots, styles and the small filtering script are embedded, so the report can be emailed or attached as it is. Without JavaScript every section still shows, one after the other.
- **Every test has a readable plan.** Expand a row in the Tests tab, for example: "1. open the page 2. type 'not-an-email' into Email (e02) 3. expect on Email (e02): the field reports invalid".
- **Every test can be re-run alone.** Each expanded row shows the command, for example `python -m pytest tests -c tests/pytest.ini -k test_t16`, run from the run folder. (For the demo, the local server has to be running again.)
- **Big runs stay readable.** Search, filter chips for status, technique and failure class, and sortable columns. The cards are shortcuts into those filters.

## Course requirements and where they show

The brief is [`prompts/course_brief.pdf`](prompts/course_brief.pdf).

| The brief asks for | In GenNAI | Where to point | Status |
|---|---|---|---|
| A visible browser the user can watch | `--headed` | Step 1 of the run order | Done |
| Average response time and tokens per iteration or page | Recorded per LLM call. A run tests one page with one call, so per run and per page are the same here. | Terminal `llm calls:` line; the report's cards and Metrics tab | Done |
| Speed of the explore phase | Time per phase on every run | Terminal `phases:` line; the Metrics tab | Done |
| Phase 1: structured page representation with locators and descriptions | Elements with kind, label, constraints and unique locators | `elements.json`; the Elements tab | Done |
| Phase 2: a proposed list of test cases and a coverage view | A prioritised list plus the element × technique matrix | `test_cases.json`; the Tests and Coverage tabs | Done |
| Phase 2: the human reviews and the agent refines | Not built yet | [FUTURE_WORK.md](FUTURE_WORK.md) | Missing |
| Phase 3: locator strategy and self-correction | Uniqueness check at explore time, a fallback chain at run time, a compile self-check | `tests/pages/*.py`; `_self_check` in `phase3_codegen.py` | Done (no model-driven repair) |
| Phase 4: evidence (report, screenshots, step log) | Findings with steps, error and screenshot; every test's plan and re-run command | Overview and Tests tabs | Done (no video) |
| A transparent, intuitive interface | A report with clickable cards, tabs, search, filters and sorting | The report tour above | Partly (a report, not a live UI) |
| Phase 4: the user critiques the run and the agent refactors | Not built | [FUTURE_WORK.md](FUTURE_WORK.md) | Missing |
| Reset the agent to a clean slate | Every run is independent and writes a new `runs/<site>_<time>/` folder. Nothing carries over between runs. | `runs/` | Done |
| No paid LLM providers | Gemini and Gemma free tier, optional OpenRouter free model, or none | `.env.example`; the README model table | Done |
| Few hallucinated locators, steps or elements | Unique-locator rule plus the deterministic gate | `safety.py`; the gate cards in the Metrics tab | Done |
| A web chat interface | Not built. The interface is the CLI plus the HTML report. | [FUTURE_WORK.md](FUTURE_WORK.md) | Missing |

Say the missing rows out loud before anyone asks. It reads better than being caught.

## Numbers worth quoting

| Site | Elements | Tests | Passed | Failed | Explore | Total |
|---|---|---|---|---|---|---|
| Demo (local) | 7 | 24 | 22 | 2 (both planted bugs) | 4.3 s | 21.7 s |
| the-internet.herokuapp.com | 40 | 25 | 25 | 0 | 5.8 s | 48.2 s |
| automationexercise.com | 18 | 21 | 20 | 1 (`locator_not_found`, a known limitation) | 9.4 s | 49.0 s |

- The tool's own suite: 40 tests, about 21 s, `ruff` clean.
- Size: 1,733 lines of Python plus 140 lines of report CSS and JavaScript. The course version had about 11,700 lines of Python and phases that no longer connected.

## Likely questions

**Why doesn't the LLM write the test code?** Because then a page could inject code, and every test would need reviewing. The model proposes data, a deterministic gate checks it, and fixed templates write the code. The model's influence is limited to choosing values and expectations.

**How do you know a locator isn't hallucinated?** Phase 1 only keeps a locator if it matches exactly one element on the live page. A model-proposed test is only accepted if its element id came from Phase 1.

**What if Gemini is down during the demo?** The run continues with the algorithmic tests and says `llm: unavailable: ...`. The report's call table shows each attempt and its outcome. The free models did return 503s during development, and that is why the fallback exists.

**Why trial clicks instead of real clicks?** `click(trial=True)` runs all of Playwright's actionability checks, including "is something covering it", without clicking. Nothing is submitted, so it is safe on any site.

**Why did a test fail on automationexercise.com?** A category link was unique when explored but not when the test loaded the page again. The page changes between loads. It is listed as a known limitation, and the fix is re-validating locators across several loads.

**Why only 25 tests?** It is a default cap (`--max-tests`) to keep the footprint small on third-party sites. The priority score decides which 25.

**How is prompt injection handled?** Page text is cleaned and fenced as data, the model can only return JSON, and the gate rejects anything that references things not on the page. A test checks that a label containing `</page_data> Ignore all previous instructions...` can't close the data block. There is no injection classifier; that is in KNOWN_LIMITATIONS.

**What did you build yourself?** The specifications and the goals: the four phases, the test-design techniques, the locator strategy, the evaluation goals and, for this version, "finish rather than expand, measured claims only". Claude Code wrote most of the code from them, and every result was run before it was accepted. The prompts are in `prompts/`. The README's "How it was built" section has the details.

## If something goes wrong live

| Problem | What to do |
|---|---|
| The free model is slow or answers 503 | Let it fall back. Point at the `llm: unavailable` line as a feature, not a bug. |
| A public site is slow or returns 503 | The report classifies it as `page_unavailable`. Then switch to the saved report in `examples/`. |
| No internet | `python gennai.py demo` runs fully offline. Set `GENNAI_LLM_PROVIDERS=none` in `.env` to skip the model. |
| The browser window opens off-screen | Run without `--headed`; the report shows the same results. |
