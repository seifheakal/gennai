# PHASE 1 EXECUTION PROMPT FOR CLAUDE

**Objective**: Build a production-ready Phase 1 engine (Exploration & Knowledge Acquisition) for the Web-Based Testing Agent

**Timeline**: 1 week of focused development

**Success Criteria**: 
- ✅ All interactive elements discovered with 85%+ coverage
- ✅ 5 locator strategies per element (no hallucinations)
- ✅ State graph accurately represents page flow
- ✅ JSON output ready for Phase 2
- ✅ Zero false positives (validation prevents hallucinated elements)

---

## CONTEXT: What You're Building

You are Claude, an expert AI architect helping build Phase 1 of a championship-level testing agent. Claude (the LLM being used) will receive exploration results from Phase 1 and use them to generate tests in later phases.

**Your job in Phase 1**: Build the system that feeds Claude with accurate, comprehensive data about web pages.

---

## PHASE 1 ARCHITECTURE (Your Spec)

### Core Objective
Agent ingests a URL and builds a comprehensive understanding of page structure, elements, and interactivity without hallucination.

### Three-Layer Approach (IMPLEMENT ALL THREE)

**Layer 1: Playwright Accessibility Tree (Primary)**
- Use `page.accessibility.snapshot()` (or `ariaSnapshot()` if available)
- Output: Semantic HTML structure as JSON
- Benefit: 10-50K tokens vs 100K+ for full DOM
- Captures: roles, relationships, labels, accessibility info

**Layer 2: Selective Screenshots (Validation)**
- Take strategic screenshots at exploration checkpoints
- Use for: Visual validation, dynamic content verification
- Store: Base64 or reference paths
- Don't overdo it: Strategic, not comprehensive

**Layer 3: Graph-Based Exploration (Systematic)**
- Inspired by Go-Browse (beat GPT-4o-mini on WebArena)
- Build state graph as you explore
- Track: node states, edges (actions), visited states
- Strategy: Form → Buttons → Inputs → Navigation → Links
- Avoid: Redundant clicks, infinite loops

### Output Format (MUST MATCH THIS)

```json
{
  "page_url": "https://example.com",
  "exploration_timestamp": "2025-12-19T08:00:00Z",
  "total_states_discovered": 5,
  "total_elements": 42,
  "coverage_percentage": 0.87,
  
  "exploration_graph": {
    "nodes": [
      {
        "state_id": "state_1",
        "label": "Login Page - Initial Load",
        "url": "https://example.com/login",
        "screenshot": "screenshots/state_1.png",
        "aria_snapshot": {...}
      },
      {
        "state_id": "state_2",
        "label": "After Username Entry",
        "url": "https://example.com/login",
        "screenshot": "screenshots/state_2.png",
        "aria_snapshot": {...}
      }
    ],
    "edges": [
      {
        "from": "state_1",
        "to": "state_2",
        "action": "fill_input",
        "element_id": "username_field",
        "description": "User enters valid username",
        "timestamp": 1.2
      }
    ]
  },
  
  "interactive_elements": [
    {
      "element_id": "login_button_001",
      "type": "button",
      "label": "Sign In",
      "aria_role": "button",
      "aria_label": "Sign in to account",
      "visible": true,
      "enabled": true,
      
      "locators": {
        "priority_1_role": "button[name='Sign In']",           // HIGHEST - Use this first
        "priority_2_label": "label[for='login_btn']",         // High - Accessible
        "priority_3_testid": "data-testid='sign-in-button'",  // Medium - Dev-friendly
        "priority_4_css": ".login-form .btn-primary",         // Medium - Generic
        "priority_5_xpath": "//button[@aria-label='Sign in to account']"  // AVOID if possible
      },
      
      "locator_confidence": {
        "priority_1_role": 0.98,                  // VERY RELIABLE
        "priority_2_label": 0.92,
        "priority_3_testid": 0.95,
        "priority_4_css": 0.78,                   // LESS RELIABLE
        "priority_5_xpath": 0.65                  // FRAGILE
      },
      
      "accessibility_info": {
        "role": "button",
        "accessible": true,
        "keyboard_accessible": true,
        "screen_reader_friendly": true
      },
      
      "interactions": [
        "clickable",
        "keyboard_accessible",
        "focusable"
      ],
      
      "states": [
        {
          "state_id": "state_1",
          "visible": true,
          "enabled": true,
          "aria_pressed": "false"
        },
        {
          "state_id": "state_2",
          "visible": true,
          "enabled": false,
          "aria_pressed": "false"
        }
      ],
      
      "validation_evidence": {
        "screenshot_confirmed": true,
        "aria_confirmed": true,
        "manually_inspected": true
      }
    },
    // ... more elements
  ],
  
  "validation_checkpoints": [
    {
      "checkpoint_id": "verify_login_form",
      "description": "Verify login form is present and interactive",
      "passed": true,
      "evidence": {
        "elements_found": ["username_input", "password_input", "login_button"],
        "all_accessible": true,
        "all_visible": true
      }
    }
  ],
  
  "exploration_statistics": {
    "total_time_seconds": 45,
    "screenshots_taken": 8,
    "tokens_used_accessibility_tree": 28000,
    "tokens_estimate_full_dom": 120000,
    "efficiency_ratio": 4.3,
    "elements_with_multiple_locators": 42,
    "elements_with_fallback_xpath": 3,
    "hallucinated_elements": 0,
    "false_positives": 0
  },
  
  "quality_metrics": {
    "coverage_percentage": 0.87,
    "accessibility_compliance": 0.94,
    "locator_reliability_avg": 0.92,
    "validation_pass_rate": 0.97,
    "ready_for_phase2": true
  },
  
  "notes": {
    "challenges": ["Dynamic search results required waiting", "Infinite scroll detected"],
    "recommendations": ["Search feature needs special handling in Phase 2", "Infinite scroll: test with fixed result set"],
    "next_phase_hints": ["48 elements ready for test case generation", "5 major workflows identified"]
  }
}
```

---

## IMPLEMENTATION REQUIREMENTS

### Must Implement (Non-Negotiable)

1. **Playwright Integration**
   - Initialize browser with: `Chromium`, `Firefox`, and optionally `Safari`
   - Use: `page.accessibility.snapshot()` or `getAccessibilityTree()` 
   - Error handling: Timeout, navigation failures, auth required
   - Browser state tracking: Maintain context throughout exploration

2. **Element Discovery & Locator Generation**
   - Extract ALL interactive elements (buttons, inputs, links, selects, textareas, etc.)
   - Generate FIVE locator strategies per element (in priority order)
   - Validate uniqueness: Each locator appears exactly once on page
   - Calculate confidence scores (0-1) for each locator type
   - NO hallucinated elements (validate existence before adding)

3. **Multi-Layered Validation**
   ```
   Layer A: Accessibility Tree Parsing
     └─ Extract semantic structure + ARIA attributes
   
   Layer B: Screenshot Verification
     └─ Capture element regions, confirm visibility
   
   Layer C: Interactive Verification
     └─ Try to interact (hover, focus, click test) without side effects
   
   Layer D: Uniqueness Validation
     └─ Confirm each locator finds exactly one element (not 0, not 2+)
   
   Layer E: False Positive Detection
     └─ Is this a real interactive element or UI artifact?
   ```

4. **Graph-Based State Tracking**
   - Initialize graph with root state (page load)
   - Explore systematically: forms → buttons → inputs → links
   - Build edges: track actions (click, fill, select, etc.)
   - Track timestamps for each action
   - Avoid infinite loops: Check before re-visiting states
   - Maintain visited states set

5. **Smart Exploration Strategy**
   - **Priority Order** (explore in this sequence):
     1. Forms (high signal, contained exploration)
     2. Buttons with actions (navigate, submit)
     3. Text inputs and selects
     4. Navigation elements
     5. Links (could lead anywhere, do last)
   
   - **Depth Control**: Set max states (e.g., 20 states before stopping)
   - **Coverage Target**: Stop when 85%+ elements discovered
   - **Timeout Protection**: 2-minute max per page

6. **Zero Hallucination Guarantee**
   - Every element in output MUST be confirmed to exist
   - Every locator MUST be verified as unique
   - Screenshot evidence for all elements
   - Confidence scores reflect actual validation results
   - If unsure, mark as "unconfirmed" NOT "confident guess"

7. **Configuration System**
   ```python
   EXPLORATION_CONFIG = {
       "accuracy_mode": True,                # All validation layers
       "validation_level": "strict",         # strict | moderate | minimal
       "coverage_threshold": 0.85,           # Stop at 85% coverage
       "max_states": 20,                     # Max state graph nodes
       "exploration_depth": "dynamic",       # Adjust based on findings
       "screenshot_validation": True,        # Capture evidence
       "locator_strategies": 5,              # Generate 5 strategies
       "timeout_seconds": 120,               # 2-minute max
       "take_screenshots": True,             # For validation
       "validate_accessibility": True,       # Check ARIA
       "test_interactions": True,            # Try hover/focus (no side effects)
       "generate_locator_confidence": True,  # Score each locator
   }
   ```

### Code Quality Standards

- ✅ **Error Handling**: Graceful degradation (don't crash)
- ✅ **Async/Await**: Use async throughout (Playwright is async)
- ✅ **Type Hints**: Full type annotations
- ✅ **Docstrings**: Clear documentation
- ✅ **Logging**: DEBUG, INFO, WARNING levels
- ✅ **No Browser Storage**: Never use localStorage/sessionStorage
- ✅ **Resource Cleanup**: Proper browser/context/page closing

---

## PHASE 1 ENGINE STRUCTURE

### Recommended Module Layout

```
phase1/
├── __init__.py
├── config.py                    # Configuration management
├── explorer.py                  # Main exploration engine
├── accessibility_parser.py       # Parse ARIA trees
├── element_extractor.py          # Find interactive elements
├── locator_generator.py          # Generate 5 locator strategies
├── state_graph.py                # Build state graph
├── validator.py                  # Multi-layer validation
├── screenshot_handler.py         # Screenshot capture + storage
├── utils.py                      # Helpers (waits, retries, etc.)
└── output_formatter.py           # Generate JSON output
```

### Entry Point Function

```python
async def explore_page(url: str, config: dict = None) -> dict:
    """
    Main entry point for Phase 1 exploration.
    
    Args:
        url: Target page URL
        config: Exploration configuration (uses defaults if None)
    
    Returns:
        dict: Structured exploration output matching JSON schema above
    
    Raises:
        ExplorationTimeout: If exploration exceeds time limit
        NavigationError: If page fails to load
    """
    # Implementation here
```

---

## SPECIFIC INSTRUCTIONS FOR CLAUDE

### When Implementing Phase 1:

1. **Ask Clarifying Questions FIRST** (before coding):
   - What's your local test setup? (Any specific URLs to test against?)
   - Do you want Playwright to run headless or headed (visible)?
   - Should I generate sample test data for demonstration?
   - Any specific web frameworks you're targeting? (React, Vue, Angular, plain HTML?)

2. **Start with a Minimal Viable Product (MVP)**:
   - Get ONE page explored successfully
   - Ensure output matches JSON schema exactly
   - Validate all elements have 5 locator strategies
   - THEN: Build configuration flexibility

3. **Build in Layers**:
   - **Layer 1**: Parse accessibility tree (get ARIA data)
   - **Layer 2**: Extract elements (buttons, inputs, links)
   - **Layer 3**: Generate locators (5 strategies each)
   - **Layer 4**: Validate locators (uniqueness + confidence)
   - **Layer 5**: Build state graph (exploration flow)
   
   Test each layer independently before integrating.

4. **Validation is Not Optional**:
   - EVERY element must pass validation before output
   - EVERY locator must be tested for uniqueness
   - Screenshots MUST confirm visibility
   - Calculate real confidence scores (not guesses)
   - If something fails validation, EXCLUDE it (don't hallucinate)

5. **Error Handling Strategy**:
   - Timeout during exploration? → Return what we found so far + warning
   - Can't generate locator? → Include fallback + low confidence score
   - Element not found on re-validation? → Don't include it
   - Page requires auth? → Report this, don't hang

6. **Testing Your Implementation**:
   - Test against: Simple HTML page → Complex React SPA → Real website
   - Verify JSON output is valid
   - Run Phase 2 against Phase 1 output to see if it works
   - Compare performance metrics (time, tokens, coverage)

7. **Documentation Requirements**:
   - Docstring for every function
   - Clear examples of JSON output
   - Explain locator strategy selection
   - Document all configuration options
   - Add troubleshooting guide

---

## DELIVERABLES FOR PHASE 1

### Code Deliverables
1. ✅ **`explorer.py`** (Main engine) - 400-600 lines
2. ✅ **`config.py`** (Configuration) - 50-100 lines
3. ✅ **`validator.py`** (Multi-layer validation) - 200-300 lines
4. ✅ **`locator_generator.py`** (5 strategies) - 150-200 lines
5. ✅ **Supporting modules** (parser, formatter, utils, etc.) - 600-800 lines
6. ✅ **`requirements.txt`** (Dependencies) - Minimal + Playwright only
7. ✅ **`README.md`** (How to run Phase 1)

### Documentation Deliverables
1. ✅ **Architecture diagram** (how modules connect)
2. ✅ **Example JSON output** (from real website)
3. ✅ **Configuration guide** (all options explained)
4. ✅ **Troubleshooting guide** (common issues + fixes)
5. ✅ **Performance benchmarks** (time + tokens on sample sites)

### Test Deliverables
1. ✅ **Unit tests** (for each module)
2. ✅ **Integration test** (full exploration end-to-end)
3. ✅ **Validation tests** (confirm JSON schema + no hallucinations)
4. ✅ **Sample output** (from 2-3 different websites)

---

## SUCCESS CRITERIA (How We Know It Works)

✅ **Coverage**: 85%+ of interactive elements discovered (measured vs manual inspection)
✅ **Accuracy**: 0% hallucinated elements (all in output verified to exist)
✅ **Locators**: 100% of elements have 5 unique locator strategies
✅ **Confidence**: Confidence scores correlate with actual locator reliability
✅ **Performance**: Exploration completes in <2 minutes for typical page
✅ **Efficiency**: Accessibility tree size 10x smaller than full DOM
✅ **JSON Valid**: Output matches schema exactly, valid JSON
✅ **Phase 2 Ready**: Phase 2 can consume this output and generate tests

---

## KNOWN CHALLENGES (Be Ready For These)

### Challenge 1: Dynamic Content
- Problem: Elements appear after JavaScript execution
- Solution: Wait for content, use `page.wait_for_selector()`
- Implementation: Add to element discovery loop

### Challenge 2: Infinite Scroll
- Problem: More elements load as you scroll
- Solution: Set exploration depth limit, document in output
- Implementation: Track by state IDs, not infinite scrolling

### Challenge 3: Shadow DOM
- Problem: Elements inside Shadow DOM not visible to Playwright
- Solution: Use `page.evaluate_handle()` to pierce shadow boundary
- Implementation: Check for shadow DOM, handle separately

### Challenge 4: Authentication Required
- Problem: Page requires login to see elements
- Solution: Detect and report, suggest pre-authentication
- Implementation: Check for login redirects early

### Challenge 5: Rate Limiting
- Problem: Too many interactions trigger rate limits
- Solution: Add delays between actions, respect rate limiting
- Implementation: Configurable delay between interactions

---

## COLLABORATION WITH PHASE 2

**Phase 1 Output → Phase 2 Input**

Phase 2 will receive your JSON output and:
1. Read `interactive_elements` array
2. Use element IDs and coverage info to plan tests
3. Check `exploration_graph` for state transitions
4. Use locators for test case generation

**If Phase 2 complains**, typical issues:
- "Can't find element by role" → Your locator_confidence was too high
- "State graph is incomplete" → You didn't explore all workflows
- "Too many duplicate elements" → Element extraction is finding the same element twice
- "False positives in the output" → Your validation didn't work

**Make Phase 2's job easy**: Complete, accurate, well-validated output.

---

## TIMELINE FOR IMPLEMENTATION

**Day 1**: Architecture + Accessibility Parser
- Design module structure
- Implement accessibility tree parsing
- Test with sample HTML

**Day 2**: Element Extraction + Locator Generation
- Extract interactive elements
- Generate 5 locator strategies per element
- Build confidence scoring

**Day 3**: Multi-Layer Validation
- Implement 5-layer validation
- Validate locator uniqueness
- Screenshot verification

**Day 4**: State Graph + Exploration Strategy
- Build graph-based explorer
- Implement systematic exploration order
- Add timeout + depth controls

**Day 5**: Integration + Testing
- Wire all modules together
- Test end-to-end exploration
- Generate sample outputs
- Document & polish

---

## FINAL CHECKLIST BEFORE HANDOFF TO PHASE 2

- [ ] JSON output matches schema exactly
- [ ] No hallucinated elements (all validated)
- [ ] All elements have 5 locator strategies
- [ ] Confidence scores are accurate
- [ ] State graph represents actual page flows
- [ ] Coverage is 85%+
- [ ] Exploration completes in <2 minutes
- [ ] All code has docstrings + type hints
- [ ] Unit tests pass
- [ ] Integration test passes
- [ ] Sample output provided
- [ ] README explains how to use
- [ ] Configuration is flexible + documented
- [ ] Error handling is graceful
- [ ] Performance is tracked

---

## KEY PRINCIPLES (Repeat These)

1. **Accuracy First**: Better to miss an element than hallucinate one
2. **Validation Required**: Everything must be confirmed to exist
3. **User-Facing Design**: Prioritize accessible, semantic locators
4. **Efficiency Matters**: Accessibility tree (10x) vs full DOM
5. **Production Quality**: Assume Phase 2 will rely on this output
6. **Zero Hallucinations**: "I'm not sure" is better than confident guess
7. **Clear Output**: JSON schema MUST be followed exactly

---

## QUESTIONS FOR CLAUDE BEFORE STARTING

Ask yourself (and us) these questions:

1. **Test Environment**: Do we have sample websites to test against? Or generate mock HTML?
2. **Headless vs Headed**: Should Playwright run visibly or headless?
3. **Authentication**: Do we need to handle login flows or start with public pages?
4. **Screenshots**: Store as files or base64 in JSON?
5. **Database**: Store exploration results in DB or just JSON files?
6. **Performance**: Is 2 minutes per page acceptable or should we optimize faster?
7. **Scope**: Start with simple pages or complex SPAs immediately?

---

## SUCCESS = PHASE 2 CAN USE PHASE 1 OUTPUT

The ultimate test: Hand off Phase 1 output to Phase 2 and it should be able to:
- Parse the JSON
- Extract all interactive elements
- Generate meaningful test cases
- Achieve 85%+ coverage on those elements

If Phase 2 struggles, Phase 1 needs refinement.

---

**Your Mission**:

Build Phase 1 that is:
✅ **Accurate** (no hallucinations)
✅ **Complete** (85%+ coverage)
✅ **Validated** (everything verified)
✅ **Efficient** (uses 10x less tokens)
✅ **Production-Ready** (Phase 2 ready)

---

**Let's Build Championship-Level Phase 1!** 🏆

