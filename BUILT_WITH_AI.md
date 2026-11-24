# How GenNAI was built with AI

GenNAI was built with AI coding agents working under written rules. I set the goals, the constraints and the decisions. The agents planned, wrote the code and checked their own work against those rules. This page explains how that worked and how the results were verified. Everything here comes from the repo, its history and the session records.

A visual one-page version is in [docs/how-it-was-built.html](docs/how-it-was-built.html). The full spec the agents worked from is [prompts/FINALIZATION_PROMPT.md](prompts/FINALIZATION_PROMPT.md).

## Two versions, two lessons

| | Course version (December 2025) | This version (November 2026) |
|---|---|---|
| How it was made | I wrote phase specifications in `prompts/`, and an AI coding tool generated most of the code from them. | A written spec with hard rules, a planning model that delegated and reviewed, and proof required for every claim. |
| Size | About 11,700 lines of Python | 2,540 lines of Python with every course feature rebuilt, plus 140 lines of report CSS and JS |
| What worked | The deterministic test design: EP, BVA and state combinations. It got the best efficiency score in the class and the highest mark. | Every phase runs end to end on three sites, and every number in the README comes from a saved run. |
| What didn't | Phase 1 and Phase 2 used different locator schemas. Human review approved tests with `random.random()`. The saved Phase 4 results had zero tests. | The gaps are written down in `KNOWN_LIMITATIONS.md`. |

The lesson from the first version: an AI agent without hard rules produces a lot of plausible code that doesn't connect. Most of this version's work went into the rules.

## 1. Planning: the spec before any code

The spec was written in a separate planning chat before any code changed. These are the decisions in it:

- **Ponytail rules:** finish rather than expand, reuse before writing, and delete what doesn't work instead of faking it. Measure every claim, with before and after line counts.
  - The Ponytail plugin couldn't be installed by an agent, because plugin installs are typed by the user. The rules were applied by hand, as the spec allowed.
- **Demo first:** before any cleanup or docs, the one-command pipeline had to run end to end on the local demo, then on two public practice sites.
- **A better free model, verified:** the course allowed only free or old models. The agent had to check the providers' current docs instead of trusting memory, and record the model, the limits and the source. Calls go through `.env`, with a fallback chain.
- **LLM safety as requirements, not extras:**
  - page text is untrusted data;
  - the model returns only JSON;
  - a deterministic gate checks every reference;
  - calls and tokens are capped;
  - local addresses are refused.
- **Honest docs:** `KNOWN_LIMITATIONS.md` for real flaws and `FUTURE_WORK.md` for ideas. The README's "Where this fits in my development" section lists only items the agent verified in code.
- **Boundaries:**
  - The two reference projects were read-only: never modified or copied from, no `.env` or personal files opened, no names or data put in this repo.
  - Git: a branch per piece of work, no force-push, no history rewrites, never commit secrets.

## 2. Division of labour between models

The spec assigned roles by what each job needs:

| Role | Model | Job |
|---|---|---|
| Lead | Claude Opus | Plan, make design decisions, write briefs, review every diff, run the proof command, make tiny edits itself |
| Workers | Claude Sonnet subagents | Write the code for one brief each |
| Mechanical jobs | Claude Haiku | Deleting clutter, renames, grepping for TODOs, counting lines, the secret scan |

The rules for delegation:

- **Self-contained briefs.** Each brief states the goal, the files that subagent owns, the constraints and a **proof command** that shows the work is done.
- **No overlapping files.** No two subagents edit the same files at the same time, so independent pieces can run in parallel.
- **"Done" isn't proof.** The lead reads each diff and runs the proof command before accepting anything. A subagent saying it is done doesn't count.
- **Reference reading is delegated.** One subagent reads the reference projects and returns a short summary, so the lead's context stays small.

The showcase work (PR #3: the report, the metrics and these docs) was small enough that the lead wrote it directly and checked it with the same gates.

Later work used parallel **sessions**, each with its own git branch:

- **One session** built the six course features: multi-page crawl, human review, run history with flaky detection, login, notifications and the web UI.
- **Another session** built the report, the LLM metrics and this documentation.

When the two shared a folder, the second moved into its own git worktree, so their changes couldn't mix. They coordinated by messages:
- which files overlap;
- which pull request merges first;
- what the other branch's data looks like, so the new report already shows the crawler's pages.

## 3. Verification: how claims were checked

These gates ran throughout:

1. **Run it for real.** Every feature was run on the demo page and on public practice sites before it was accepted. The browser UI and the report were clicked through in a real browser, and their interactions were checked by script.
2. **Tests.** The suite grew with the features: 36 tests when the first version merged, 40 after the showcase PR, and 88 after the course features merged. All HTTP to LLM providers is mocked, so the tests are deterministic and free.
3. **Adversarial tests:**
   - a label that tries to break out of the prompt;
   - hostile strings pushed through code generation;
   - a model inventing an element;
   - a model adding a `code` field;
   - `<script>` in page text reaching the report.
4. **Bugs from real runs became fixes, and often tests.** Live runs found:
   - a skip link misreported as a timeout;
   - HTTP 503 pages misreported as missing locators;
   - a 5 s timeout used for page loads;
   - an inline `.env` comment silently read as an API key.

   Each was fixed, and most got a regression test. [TECHNICAL.md](TECHNICAL.md) lists which.
5. **Measured, not estimated.** The LLM numbers are the provider's own token counts and measured response times. The README tables come from saved runs in `examples/`. When a number changed, the docs changed with it.
6. **Claims checked against code.** Documentation statements were checked against the code before committing. For example, three regression tests that a draft of TECHNICAL.md named turned out not to exist, so the doc was corrected rather than the claim kept.
7. **Secrets.** The API key was pasted into `.env` by me. The agent declined to copy it from another project. It was never printed, and the files and commits were scanned for key patterns before pushing.
8. **CI.** Every pull request runs lint and the test suite on GitHub. Pull requests were merged only after CI was green.

### Was it test-driven?

Partly, and the honest answer matters more than the label:
- **Test-after:** most tests were written alongside the code or right after it, then run on every change.
- **Regression tests from live failures:** where a live run exposed a bug, the fix came with a test that would have caught it.
- **Test-first:** none. One test was checked against the old behaviour after the fact. The test-cap test fails under the old rule and passes under the new one, which proves it guards the fix.

## 4. What the human decided

The agents did the planning detail, the code and the checking. These decisions were mine:
- the framing (the course limited the model, so I engineered the harness);
- the scope ("everything the course version had, or more, never less, while keeping it minimal");
- which models to use, and getting the API key;
- the merge order and every merge;
- what to showcase, and that the claims must be measured.

## 5. Course features, rebuilt in parallel (PR #2)

The six features the course version had claimed were rebuilt by a second Claude session on its own branch, one commit per feature:
- multi-page crawl;
- human review;
- run history with flaky marking;
- login;
- notifications;
- the local web UI.

**How the work was split:** by that session's own account, it used no subagents. Each feature was small enough to write and check in one session.

**How each feature was verified:**

| Feature | Checked |
|---|---|
| Crawl, review and history | Run on the demo and on the-internet.herokuapp.com |
| Login | The demo's own test account behind a sign-in page. A wrong password stopped the run, and the password appeared in no output file or log line. |
| Notifications | Sent to a webhook receiver and a mail receiver running on this machine. Unreachable receivers, and servers without TLS, were reported without failing the run. |
| Web UI | Clicked through in a browser on the demo and on herokuapp |

**One review catch:** the first version of the multi-page test cap could leave out both planted demo bugs. The building session noted this in its own report, and the reviewing session sent it back as a must-fix before merge. The fix fills the cap in coverage order, and a unit test pins it.

**Not verified:** signing in to a third-party site, and delivery to a real Slack workspace or mail provider. Both need the owner's own accounts; the README gives the commands.
