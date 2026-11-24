# Demo script (2 to 3 minutes)

Before recording: install once (see README Quickstart), close other windows, and open a terminal in the repo folder. No API key is needed. With a free Gemini key in `.env`, the model's extra tests show up as `llm` rows.

## 1. The problem (20 s)

Show the README top paragraph.

Say: "Writing UI tests by hand is slow, and the first tests people write rarely cover invalid input or elements that are covered by something else. GenNAI takes a URL and does the whole loop: it finds the interactive elements, designs test cases with classic test-design techniques, writes runnable pytest code and runs it, then gives you a report with screenshots."

## 2. Run it (40 s)

Run:

```powershell
python gennai.py demo --headed
```

Point at the browser window while it runs. Then point at the terminal summary. With the key our run showed 7 elements, 25 tests (6 from the model; the number varies with the model's answer), 23 passed and 2 failed. Without it, 20 tests, 18 passed and 2 failed.

Say: "`demo` serves a small local sign-up page and runs the same pipeline as `run <url>`. The page has two planted problems, and the tool found both."

## 3. The findings (40 s)

Open the `report.html` path printed at the end. Expand the two failed rows.

- **Submit: is clickable** is classified as `element_intercepted`. The screenshot shows the cookie banner covering the Submit button. Say: "This is the same kind of bug the course version found on a real site, where an ad iframe covered a Subscribe button. The click is a trial click, so nothing is actually submitted."
- **Email: invalid partition** is classified as `assertion`. Say: "The field is labelled Email but accepts `not-an-email`. The tool inferred from the label that it is an email field and used an equivalence-partitioning test to catch it."

Optionally open `examples/automationexercise/report.html` to show a run on a public practice site.

## 4. How it was built (40 s)

Show the README "How it works" diagram and `prompts/`.

Say: "It was a university Generative AI course project. The course allowed only free-tier, open-source or local models, so I put the work into the harness: deterministic test design with equivalence partitioning, boundary values and state combinations, plus validation. I directed the implementation and used Claude Code to write most of the code. The prompts are in the `prompts` folder. For this version there's an optional free-tier LLM step. The model can only return JSON test specs, and a deterministic gate drops anything that references an element the page doesn't have. The code itself always comes from fixed templates."

## 5. What I'd improve next (20 s)

Show `KNOWN_LIMITATIONS.md` and `FUTURE_WORK.md`.

Say: "The honest gaps are written down. Locators are heuristic, the run isn't sandboxed, and the gate checks references but not meaning. Next I'd extend the gate to check whether the model's expected result follows from the field's constraints, add run history to separate flaky tests from real regressions, and add a human review step before tests run."
