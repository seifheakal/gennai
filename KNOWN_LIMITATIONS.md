# Known limitations

Real flaws in the current version that were too expensive or risky to fix within this project. Ideas for new features are in [FUTURE_WORK.md](FUTURE_WORK.md).

1. **Heuristic locators.**
   - **What:** each element gets candidates from `data-testid`, `id`, `name`, role plus accessible name, label, placeholder and text. Phase 1 keeps only candidates that match exactly one element at exploration time.
   - **Impact:** a locator can stop being unique on a later page load. On automationexercise.com a category link that was unique during exploration matched no unique element when the test ran (`locator_not_found`).
   - **Why left:** stable locators on pages you don't control need DOM-diffing or repair logic.
   - **Needed for production:** re-validation on each run, locator scoring across several loads, and human-approved repair.

2. **Simple crawl, simple login.**
   - **What:** by default the tool tests only the URL it is given. `--max-pages N` follows plain `<a href>` links on the same origin, breadth-first, up to 20 pages. Login (`GENNAI_LOGIN_*`) only handles a single form with one text or email field and one password field, submitted with Enter: no multi-step logins, SSO, MFA or CAPTCHA, and no login through a button that isn't a form submit. It was verified only on the bundled demo's script-based sign-in page. The crawler also does not follow links created by clicks or forms (single-page-app routing, buttons that navigate), or pages listed only in a sitemap. Links are skipped by a word list (logout, delete, remove, ...), so a harmless "Add/Remove" page is skipped too and a destructive link with an unusual name is not. Pages are deduplicated by URL, so `/` and `/index.html` count as two pages. The 25-test cap is shared by all pages, so with many pages some get only their highest-priority tests.
   - **Impact:** pages behind a more complex login, or reachable only through script navigation, are not tested. On a large site the first N pages in link order are tested, not the most important ones.
   - **Why left:** each login style needs its own handling; smarter scoping needs a model of which pages matter.
   - **Needed for production:** configurable login steps and selectors, credentials from a secret store instead of `.env`, an explicit allow/deny list of paths, and per-page test budgets.

3. **Shallow assertions.**
   - **What:** the generated tests check what the browser itself knows: HTML5 constraint validation (`checkValidity()`), `maxlength` truncation, selected and checked state, and whether an element can receive a click (`click(trial=True)`, which clicks nothing). Forms are never submitted.
   - **Impact:** server-side validation and business logic are not tested. This is deliberate, so third-party sites get no writes.
   - **Why left:** submitting forms on sites you don't own is unsafe.
   - **Needed for production:** an opt-in "owned site" mode with real submissions and response checks.

4. **Hidden structures are not discovered.**
   - **What:** elements inside iframes and shadow DOM are not collected. Off-screen elements, such as skip links that only appear on focus, are skipped on purpose. Fields with a `pattern` attribute get no valid-value or boundary tests, because valid data can't be derived from a regex without risking false failures.
   - **Impact:** coverage on component-heavy sites is lower than the element count suggests.
   - **Why left:** each needs its own traversal or data-generation logic.

5. **Small evaluation.**
   - **What:** the measured results in the README come from three sites: the bundled demo and two public practice sites.
   - **Impact:** the numbers show the tool works end to end. They are not a benchmark of detection quality.
   - **Why left:** project scope.
   - **Needed for production:** a labelled set of pages with known defects, and precision/recall per failure class.

6. **Third-party pages are not deterministic.**
   - **What:** ads, carousels and A/B content change between loads, and busy servers sometimes shed load. The course-era run on automationexercise.com caught an ad iframe covering the Subscribe button. The runs for this version did not see that overlay, but they did get HTTP 503 "queue full" pages on some test loads (reported as `page_unavailable`).
   - **Impact:** results on public sites vary between runs. Run history marks a test flaky when it both passed and failed within the last few runs (see item 16), which shows inconsistency but cannot say why.
   - **Why left:** telling flake from a real change needs repeated runs against a page known not to change.

7. **The test run is not sandboxed.**
   - **What:** generated tests run as a normal `pytest` subprocess with the user's permissions and network access. Code comes only from fixed templates with every value embedded via `repr()`, so page content and model output can't inject Python. The browser still executes the target site's JavaScript (inside Chromium's sandbox).
   - **Impact:** a bug in the templates would run with full user rights.
   - **Why left:** containerising the run adds setup that the demo doesn't need.
   - **Needed for production:** run the generated suite in a container with no access to the host filesystem.

8. **Basic prompt-injection defence.**
   - **What:** page text is sanitised (comments, control and zero-width characters removed, every field truncated) and placed in a delimited data block. The model is told that this block is data. The model can only return JSON, which a deterministic gate checks. There is no injection classifier, and nothing checks whether the model leaks its prompt.
   - **Impact:** a hostile page can still steer the model toward plausible but wrong tests within the allowed actions. It can't add new elements, actions or code.
   - **Why left:** a classifier and red-team evaluation are a project of their own.

9. **The hallucination gate checks references, not meaning.**
   - **What:** a model-proposed test is accepted only if its element id exists, its action is allowed for that element kind, and a select value is one of the detected options. Whether the model's expectation ("this value should be invalid") is correct is not checked.
   - **Impact:** a wrong expectation shows up as a false `assertion` failure.
   - **Needed for production:** check expectations against the field's own constraints deterministically. `--review` lets a person reject such tests before they run, but it is opt-in.

10. **Cost controls are per run only.**
    - **What:** there is a hard cap on LLM calls per run (`GENNAI_LLM_MAX_CALLS`), plus input and output token caps, timeouts, client-side spacing and fallback on 429.
    - **Impact:** there are no per-user quotas, token accounting or cost reporting.
    - **Why left:** the tool is a single-user CLI.

11. **Local-target guard.**
    - **What:** the CLI refuses non-http(s) URLs, and hosts that resolve to an address that is not globally routable or is multicast, unless `--allow-local` is given. Phase 1 re-checks the final URL after redirects.
    - **Impact:** a redirect to a local address has already been requested by the time it is refused. The guard does not protect against DNS rebinding. Subresource requests made by the page are not filtered, and the generated tests navigate again without a fresh check.
    - **Needed for production:** pin the resolved IP for the run and route the browser through a filtering proxy.

12. **Free models are often overloaded, and the LLM evidence is thin.**
    - **What:** during live testing, `gemini-3.8-flash`, `gemini-3.6-flash` and `gemma-4-31b-it` often answered HTTP 503 ("high demand"). The default is therefore `gemini-3.5-flash-lite`. The Gemma fallback never returned a full answer live. Its `<thought>` reasoning prefix is stripped by the gate, but that is tested only with a mocked response. Google does not publish per-model free-tier limits (they appear per project in AI Studio), so the default spacing of 10 requests per minute is a conservative guess.
    - **Impact:** on a busy day the LLM step may add nothing, and the run says so. The live measurement covers 3 pages and 19 proposed specs, with 0 rejected, which is too small to estimate a hallucination rate.

13. **Free-tier data use.**
    - **What:** with an LLM key configured, element labels and texts from the tested page are sent to the provider. Google's pricing page says free-tier content is used to improve its products.
    - **Impact:** do not point the LLM step at confidential or internal pages. The tool runs fully offline without a key.

14. **The course's model constraint shaped the design.**
    - **What:** the course allowed only free-tier, open-source or local models. The course version committed no LLM API call at all. Test design was done entirely by the deterministic generators: equivalence partitioning, boundary values and state combinations.
    - **Impact:** the deterministic core is still the main source of tests. The model is an optional add-on that proposes extra cases and passes through the same gate.

15. **Review edits are not re-checked.**
    - **What:** with `--review` a person may change a case's title and step values. The edited value runs against the case's original expectation. Nothing checks that the two still agree, so a value edited on a "below minlength" case makes it fail with `assertion` (seen on the demo). The review is a pause in one terminal session: there is no way to stop after Phase 2 and resume later, and the file is not locked while you edit it.
    - **Impact:** a careless edit produces a false failure. A review cannot be handed to someone else to do later.
    - **Why left:** recomputing expectations needs the same semantic check the LLM gate lacks (item 9). Resuming needs the staged pipeline in FUTURE_WORK.
    - **Needed for production:** recompute or confirm the expectation for edited values, and a `--from codegen` resume that reads an approved `test_cases.json`.

16. **"Flaky" means inconsistent, not proven flake.**
    - **What:** a test is flaky if it both passed and failed within the last `GENNAI_FLAKY_WINDOW` runs (default 5). A real regression followed by a fix inside that window is marked flaky too. Tests are matched by page path, element attributes, actions, values and expectation, so if a label or button text changes, the test counts as a new one and its history starts over. The history file grows by one line per run and is never trimmed. Two runs of the same site at the same time are not coordinated: both append, and neither sees the other's result.
    - **Impact:** treat "flaky" as "look at this test's recent runs", not as a verdict. Its evidence is only as long as the window.
    - **Why left:** the history is one append-only file on purpose, so it stays easy to inspect.
    - **Needed for production:** a minimum number of runs before judging, retries inside a run to confirm flake, file locking or a database for concurrent runs, and rotation of old records.

17. **Notifications are one-shot.**
    - **What:** one Slack-compatible webhook and one email recipient list, one attempt each with a 15 s timeout, no retry and no queue. Sending was verified against local receivers only. The message names the run folder, not a link, because the report is a local file.
    - **Impact:** a notification lost to a network error is reported in the run summary but not resent.
    - **Why left:** the tool is a single-user CLI; a retry queue needs a long-running process.
    - **Needed for production:** retries with backoff, a hosted report to link to, and per-channel message formatting.

18. **The web UI is a local single-user page.**
    - **What:** one run at a time, progress by polling once a second, run messages kept in memory (gone when the server stops; the output folders stay). No review step, no `--allow-local`, no login form of its own (it uses `.env`), and no authentication: anyone who can reach 127.0.0.1 on that machine can start a run.
    - **Impact:** fine for one person on their own machine; not something to expose on a network.
    - **Why left:** a shared service needs user accounts, a job queue and persistent run records.
    - **Needed for production:** authentication, a queue with per-user limits, and runs stored with the history.
