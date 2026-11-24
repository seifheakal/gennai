# QUICK START: Phase 1 Prompt Template for Claude

**Use this EXACT template when giving Claude the Phase 1 assignment.**

---

## Copy & Paste This Into Claude Chat

```
I'm building a championship-level Web-Based Testing Agent, and I need your help building Phase 1: Exploration & Knowledge Acquisition.

## THE ASSIGNMENT

Build a **production-ready Phase 1 engine** that:
1. Takes any website URL as input
2. Discovers ALL interactive elements (buttons, inputs, forms, links, etc.)
3. Generates 5 locator strategies for each element (getByRole > getByLabel > getByTestId > CSS > XPath)
4. Builds a state graph showing how the page changes as users interact
5. Validates everything to ensure ZERO hallucinated elements
6. Outputs structured JSON for Phase 2 to consume

## WHAT MAKES THIS HARD

✅ **Accuracy First**: Missing an element is OK. Hallucinating one is FAILURE.
✅ **No Paid APIs**: Use only Playwright + free LLM if needed
✅ **Production Quality**: Phase 2 depends on this output being perfect
✅ **Efficiency**: Use accessibility tree (10x smaller) not full DOM
✅ **Validation**: Every element must be confirmed to actually exist

## WHAT I'M PROVIDING

I've saved a detailed specification document here: `phase1_claude_prompt.md`

Please read the full document carefully, then ask me any clarifying questions before you start coding.

## KEY DETAILS

**Core Architecture**:
- Layer 1: Parse Playwright accessibility tree
- Layer 2: Take strategic screenshots for validation
- Layer 3: Build state graph through systematic exploration

**Output Format**: Specific JSON schema (in the document)

**Success Metrics**:
- 85%+ element coverage
- 0% hallucinated elements
- 100% elements have 5 locator strategies
- <2 minutes exploration time
- Accessibility tree 10x smaller than full DOM

**Timeline**: 1 week

## MY REQUEST

1. Read the full `phase1_claude_prompt.md` document
2. Ask me clarifying questions if anything is unclear
3. Once you understand the spec, propose your implementation approach
4. Then build it iteratively with testing at each layer

Questions before you read the spec?
```

---

## Key Points Claude Should Understand

**Before sending the prompt, make sure Claude knows:**

1. **This is NOT a casual request** - It's a championship-level project
2. **Accuracy > Speed** - Missing elements is better than false positives
3. **Everything must be validated** - No guessing, no hallucinations
4. **Phase 2 depends on this** - If Phase 1 fails, everything downstream breaks
5. **The specification is detailed** - It has examples, output formats, everything
6. **Ask questions first** - Better to clarify than build wrong thing

---

## Expected Claude Response (Good vs Bad)

### ✅ GOOD Response (Claude understood the scope)
```
"I've reviewed phase1_claude_prompt.md carefully. I understand this is a 
complex, multi-layer system that MUST achieve zero hallucinations while 
maintaining 85%+ coverage. 

Before I propose an implementation, I have a few clarifying questions:

1. What's the target environment for testing? (Local dev, cloud, specific URLs?)
2. Should I include authentication/session handling?
3. Do you have sample websites to test against?
4. Should screenshots be stored as files or embedded base64?

Here's my proposed approach...
[Clear technical plan with concrete steps]"
```

### ❌ BAD Response (Claude misunderstood)
```
"I'll build a quick web scraper that finds elements and generates tests.
Should be pretty straightforward, I'll have it done tomorrow."
```

If you get a bad response, share the full prompt document and ask Claude to re-read carefully.

---

## How to Use This Prompt

### Step 1: Send to Claude
Copy the template above into Claude chat, including the reference to `phase1_claude_prompt.md`

### Step 2: Claude Reads the Spec
Claude should carefully read the document and ask clarifying questions.

### Step 3: Claude Proposes Approach
Claude proposes concrete implementation plan (module structure, algorithms, testing strategy)

### Step 4: You Approve or Adjust
Review the approach, give feedback, clarify any points

### Step 5: Claude Builds Iteratively
- Build one module
- Test it
- Show you results
- Move to next module

### Step 6: Integration & Polish
- Wire modules together
- End-to-end testing
- Generate sample outputs
- Document everything

---

## What to Watch For

**Good Signs** (Claude understands):
✅ Claude asks clarifying questions about scope
✅ Claude proposes modular architecture
✅ Claude emphasizes validation/testing
✅ Claude mentions specific algorithms (Go-Browse approach)
✅ Claude talks about error handling
✅ Claude asks about test environment

**Red Flags** (Claude missed something):
❌ Claude jumps to coding without clarification
❌ Claude treats this as "just web scraping"
❌ Claude doesn't emphasize validation/accuracy
❌ Claude doesn't mention testing strategy
❌ Claude's timeline is unrealistic (24 hours for complex project)
❌ Claude doesn't reference the spec document

---

## If Claude Gets Stuck

**Common Issues & Solutions**:

**"Where do I start?"**
→ Have Claude start with accessibility tree parsing first (Layer 1)

**"How do I validate locators?"**
→ Reference the "Multi-Layered Validation" section in the prompt

**"Should I use regex for CSS selectors?"**
→ No - use Playwright's built-in locator methods

**"What if authentication is needed?"**
→ Document the limitation, propose workaround (provide logged-in cookie)

**"How long should this take?"**
→ Remind Claude: 1 week timeline, can iterate with you daily

---

## Documentation to Share with Claude

When giving this prompt to Claude, also share:

1. **`project_plan.md`** (complete project context)
2. **`phase1_claude_prompt.md`** (the detailed spec - THIS FILE)
3. **`IMPLEMENTATION_GUIDE.md`** (phase-by-phase breakdown)

All are in `/workspace/` directory.

---

## Success = Clean Handoff to Phase 2

The ultimate success metric: When Phase 1 is done, Phase 2 should be able to:

```python
# Phase 2 can do this:
phase1_output = json.load(open("phase1_output.json"))

for element in phase1_output["interactive_elements"]:
    element_id = element["element_id"]
    locators = element["locators"]  # Has all 5 strategies
    confidence = element["locator_confidence"]
    # ... use this to generate test cases
```

If Phase 2 can easily consume Phase 1 output, Phase 1 succeeded.

---

## Approval Checklist Before Phase 2

Before Phase 1 is considered "done", verify:

- [ ] Claude has read full specification
- [ ] Claude proposed implementation approach (and you approved it)
- [ ] Phase 1 successfully explores sample website
- [ ] JSON output matches schema exactly
- [ ] All elements have 5 locator strategies
- [ ] Zero hallucinated elements (manually verified)
- [ ] Coverage is 85%+ on test page
- [ ] Exploration completes in <2 minutes
- [ ] All code is documented + tested
- [ ] Sample output ready for Phase 2
- [ ] README explains how to use it

---

## Final Tip

**When you give this to Claude, emphasize**:

> "I'm not looking for quick code. I'm looking for championship-level architecture 
> that's accurate, well-validated, and production-ready. Take the time to do it right.
> Ask questions. Propose approach. Build iteratively. Test thoroughly.
> We'd rather have this in 1 week done right than 3 days done wrong."

This mindset shift makes a huge difference in Claude's output quality.

---

**Ready to send this to Claude? Use the template above!** 🚀

