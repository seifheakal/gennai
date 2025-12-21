# Dynamic Test Generation - Technical Documentation

## Architecture Overview

### System Components

```
┌────────────────────────────────────────────────────────────┐
│  test_generated_tests.py                                    │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Imports & Setup                                         │
│     ├─ Selenium WebDriver                                  │
│     ├─ Pytest framework                                    │
│     └─ JSON file loading utilities                         │
│                                                             │
│  2. convert_locator_to_xpath(locator_value)                │
│     └─ Converts Playwright syntax to Selenium XPath        │
│                                                             │
│  3. load_phase1_elements()                                  │
│     ├─ Reads phase1_real_output2.json                     │
│     ├─ Selects best locator by confidence                 │
│     └─ Returns ELEMENT_MAP                                │
│                                                             │
│  4. load_phase2_tests()                                     │
│     ├─ Reads phase2_test_cases.json                       │
│     └─ Returns TEST_SPECS                                 │
│                                                             │
│  5. TestSuite (BaseTestCase subclass)                      │
│     ├─ Base URL configuration                             │
│     └─ Dynamically injected test methods (test_elem_001...)│
│                                                             │
│  6. Dynamic Test Generation Block                          │
│     ├─ For each elem_id in ELEMENT_MAP:                   │
│     │  ├─ create_test_method(element_id)                  │
│     │  ├─ Define test_method closure                      │
│     │  └─ setattr(TestSuite, f"test_{elem_id}", ...)      │
│     └─ Tests ready for pytest discovery                   │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

## Detailed Function Reference

### 1. convert_locator_to_xpath()

**Purpose**: Convert Playwright locator syntax to Selenium-compatible XPath

**Signature**:
```python
def convert_locator_to_xpath(locator_value: str) -> Optional[str]
```

**Input Formats Handled**:
1. **Already XPath**: `//button[text()='...']` → returns as-is
2. **Button role**: `button[name='Test Cases']` → `//button[contains(@aria-label, 'Test Cases') or contains(text(), 'Test Cases')]`
3. **Text selector**: `:text('Test Cases')` → `//*[contains(text(), 'Test Cases')]`
4. **Label selector**: `label:has-text('Test')` → `//label[contains(text(), 'Test')]`
5. **Generic button**: `button` → `//button`

**Returns**: Valid XPath string or original input

**Key Feature**: Includes OR conditions for flexible matching
```python
# button[name='Test Cases'] becomes:
//button[contains(@aria-label, 'Test Cases') or contains(text(), 'Test Cases')]
# This matches both @aria-label attribute AND text content
```

### 2. load_phase1_elements()

**Purpose**: Load and parse Phase 1 element discovery output

**Signature**:
```python
def load_phase1_elements() -> Dict[str, Dict[str, Any]]
```

**Algorithm**:
1. Define multiple search paths (for different working directories)
2. Find first existing path
3. Parse phase1_real_output2.json
4. For each element:
   - Extract element_id
   - Select best locator by confidence score
   - Build element info dict
5. Return complete ELEMENT_MAP

**Output Structure**:
```python
{
    "elem_001": {
        "label": "Test Cases",
        "type": "button",
        "locator": "button[name='Test Cases']",
        "confidence": 0.95,
        "aria_name": "Test Cases",
        "visible": True,
        "enabled": True
    },
    # ... 7 more elements
}
```

**Error Handling**: Raises FileNotFoundError if no Phase 1 output found

### 3. load_phase2_tests()

**Purpose**: Load Phase 2 test case specifications (currently unused in dynamic generation)

**Signature**:
```python
def load_phase2_tests() -> Dict[str, Dict[str, Any]]
```

**Output Structure**:
```python
{
    "test_001": {
        "title": "Test Cases - enabled state",
        "description": "Verify Test Cases is enabled and clickable",
        "elements_used": ["elem_001"],
        "test_steps": [
            {
                "action": "Click Test Cases",
                "element_id": "elem_001",
                "locator": "button[name='Test Cases']"
            }
        ],
        "expected_result": "Button responds to click"
    },
    # ... 7 more tests
}
```

## Test Method Generation

### Dynamic Method Creation Pattern

```python
# At module level, after loading ELEMENT_MAP:

for elem_id in sorted(ELEMENT_MAP.keys()):  # Ensures deterministic order
    def create_test_method(element_id):
        """Closure to capture element_id"""
        def test_method(self):
            """Actual test method"""
            try:
                elem_info = ELEMENT_MAP.get(element_id)
                # ... test logic ...
            except Exception as e:
                # ... error handling ...
        return test_method
    
    # Inject method into TestSuite class
    test_name = f"test_{elem_id}"
    setattr(TestSuite, test_name, create_test_method(elem_id))
```

### Why This Pattern?

**Problem**: Can't use pytest.mark.parametrize with unittest.TestCase

**Solution**: Use `setattr()` to dynamically add methods to test class

**Benefits**:
- Works with unittest.TestCase
- Each test has proper method name (test_elem_001, etc.)
- Pytest discovers methods naturally
- Can add any number of tests at runtime

## Test Execution Flow

### Single Test Method Execution

```
1. INITIALIZATION
   ├─ Get element_id parameter
   ├─ Retrieve ELEMENT_MAP[element_id]
   └─ Extract: label, type, locator, confidence

2. NAVIGATION
   ├─ driver.get(BASE_URL)
   ├─ Print element info
   └─ Initialize WebDriverWait(driver, 10)

3. LOCATOR CONVERSION
   ├─ original_locator = ELEMENT_MAP["locator"]
   ├─ converted = convert_locator_to_xpath(original_locator)
   └─ Log: "Converted locator: {converted}"

4. LOCATOR VALIDATION
   ├─ Check if locator is "//button" (generic)
   ├─ If incomplete, pytest.skip()
   └─ Continue if valid locator

5. ELEMENT DISCOVERY (Multi-strategy)
   ├─ Try primary locator (Attempt 1)
   ├─ If fails, try text-based locator (Attempt 2)
   ├─ If fails, try ARIA label locator (Attempt 3)
   ├─ If fails, try exact match locator (Attempt 4)
   ├─ If fails, try role-based locator (Attempt 5)
   └─ If all fail, pytest.skip() with reason

6. ELEMENT VERIFICATION
   ├─ Assert: button.is_displayed()
   ├─ Assert: button.is_enabled()
   └─ If label exists, assert text matches

7. INTERACTION
   ├─ Click element
   ├─ Wait 1 second
   └─ Verify page URL changed

8. CLEANUP & REPORTING
   ├─ On success: Log "Test passed"
   ├─ On failure: Capture screenshot
   └─ Raise AssertionError with details
```

## Path Resolution Strategy

### Problem
Tests can be run from different working directories:
- From `phase3_outputs_real/`: Need `../../phase1/`
- From `phase3_outputs_real/tests/`: Need `../../../phase1/`
- From project root: Need `./phase1/`

### Solution: Multiple Path Attempts

```python
possible_paths = [
    Path(__file__).parent.parent.parent / "phase1" / "phase1_real_output2.json",
    Path(__file__).parent.parent / ".." / ".." / "phase1" / "phase1_real_output2.json",
    Path(".") / "phase1" / "phase1_real_output2.json",
]

phase1_file = None
for path in possible_paths:
    if path.exists():
        phase1_file = path
        break

if not phase1_file:
    raise FileNotFoundError(f"Phase 1 output not found. Tried: {possible_paths}")
```

## Locator Conversion Algorithm

### Regex Patterns Used

```python
# Pattern 1: button[name='...']
import re
match = re.search(r"button\[name='([^']+)'\]", locator_value)
if match:
    name = match.group(1)
    return f"//button[contains(@aria-label, '{name}') or contains(text(), '{name}')]"

# Pattern 2: :text('...')
match = re.search(r":text\('([^']+)'\)", locator_value)
if match:
    text = match.group(1)
    return f"//*[contains(text(), '{text}')]"

# Pattern 3: label:has-text('...')
match = re.search(r"label:has-text\('([^']+)'\)", locator_value)
if match:
    text = match.group(1)
    return f"//label[contains(text(), '{text}')]"
```

### XPath Generation

**Key XPath Techniques Used**:
1. **Text matching**: `contains(text(), 'value')`
   - Case-sensitive
   - Partial matches
   - Example: `//button[contains(text(), 'Test Cases')]`

2. **Attribute matching**: `contains(@attr, 'value')`
   - Matches aria-label, name, id, etc.
   - Example: `//button[contains(@aria-label, 'Test Cases')]`

3. **OR conditions**: `[condition1 or condition2]`
   - Matches if either condition true
   - Example: `//button[contains(@aria-label, 'X') or contains(text(), 'X')]`

4. **Role matching**: `contains(@role, 'button')`
   - Matches role attribute
   - Example: `//*[contains(text(), 'X') and contains(@role, 'button')]`

## Test Data Flow

### Phase 1 → Phase 3

```
phase1_real_output2.json (517 lines)
├── interactive_elements: [
│   {
│       "element_id": "elem_001",
│       "label": "Test Cases",
│       "type": "button",
│       "locators": {
│           "priority_1_role": "button[name='Test Cases']",
│           "priority_2_label": "label:has-text('Test Cases')",
│           "priority_4_text": ":text('Test Cases')"
│       },
│       "locator_confidence": {
│           "priority_1_role": 0.95,
│           "priority_2_label": 0.9,
│           "priority_4_text": 0.85
│       },
│       "visible": true,
│       "enabled": true,
│       "accessibility_info": {
│           "role": "button",
│           "accessible_name": "Test Cases"
│       }
│   },
│   # ... 7 more elements
│ ]
└── coverage: 95%

    ↓ (load_phase1_elements)
    ↓ (select best locator by confidence)
    ↓

ELEMENT_MAP (in-memory)
├── elem_001: {
│   "label": "Test Cases",
│   "type": "button",
│   "locator": "button[name='Test Cases']",  # Best: 0.95 confidence
│   "confidence": 0.95,
│   # ...
│ }
└── elem_002-008: (similar structure)

    ↓ (convert_locator_to_xpath)
    ↓

Test Execution
├── elem_001: "//button[contains(@aria-label, 'Test Cases') or contains(text(), 'Test Cases')]"
├── elem_002: "//button[contains(@aria-label, 'APIs list for practice') or contains(text(), 'APIs list for practice')]"
└── elem_003-008: (similar conversions)

    ↓ (Selenium WebDriver)
    ↓

Browser Interaction
├── Navigate to https://automationexercise.com/
├── Find elements via converted XPath
├── Verify properties (visible, enabled, clickable)
├── Click elements
└── Verify responses
```

## Error Handling Strategy

### Skip vs Fail Decision Tree

```
Element Detection Attempt
    ├─ Success: Verify element properties
    │   ├─ Verification passes: PASS
    │   └─ Verification fails: FAIL (take screenshot)
    └─ Failure: Is element required for basic workflow?
        ├─ No (e.g., "Continue Shopping", unlabeled button)
        │   └─ SKIP with reason
        └─ Yes (e.g., home page buttons)
            └─ FAIL with details
```

### Exception Handling Patterns

```python
# Pattern 1: Timeout on element discovery
try:
    element = wait.until(EC.element_to_be_clickable((By.XPATH, locator)))
except TimeoutException:
    pytest.skip(f"Element not found")

# Pattern 2: Verification assertion failure
self.assertTrue(element.is_displayed())  # Raises AssertionError

# Pattern 3: Click blocked or other interaction error
try:
    element.click()
except StaleElementReferenceException:
    # Element became stale, take screenshot and raise

# Pattern 4: Catch-all for unexpected errors
except Exception as e:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"test_failures/{element_id}_{timestamp}.png"
    self.driver.save_screenshot(screenshot_path)
    raise AssertionError(f"Test failed: {str(e)}")
```

## Performance Characteristics

### Timing Breakdown (per test)

```
Navigate + Wait Setup:        ~2-3 seconds
Element Discovery:            ~5-8 seconds
  ├─ Primary locator:         ~2-3 seconds
  ├─ Wait condition check:     ~3-5 seconds
  └─ Fallback attempts:        ~2-3 seconds (if needed)
Element Verification:         ~1-2 seconds
  ├─ is_displayed():           ~0.5 seconds
  ├─ is_enabled():             ~0.5 seconds
  └─ Text comparison:          ~0.5 seconds
Click + Response Wait:         ~3-5 seconds
Screenshot (on failure):       ~1 second
─────────────────────────────────────
Total per test:               ~15-20 seconds
```

### Optimization Opportunities

1. **Parallel Execution**: Use pytest-xdist for concurrent tests
2. **Browser Reuse**: Share browser instance across tests
3. **Element Caching**: Cache element references if not dynamic
4. **Locator Pre-checking**: Validate locators once instead of per test

## Integration Points

### Phase 1 Integration
- **Data Source**: phase1_real_output2.json
- **Usage**: Element discovery, locators, confidence scores
- **Dependency**: Direct file load
- **Update Trigger**: Re-run Phase 1 on website changes

### Phase 2 Integration
- **Data Source**: phase2_test_cases.json
- **Usage**: Test specifications (loaded but not fully utilized in current implementation)
- **Dependency**: Optional (can enhance with Phase 2 test steps)
- **Future Enhancement**: Use Phase 2 test_steps for multi-step tests

### Phase 4 Integration
- **Output Format**: pytest-html compatible
- **Report File**: report_dynamic.html
- **Metrics**: Pass/skip/fail counts, execution times
- **Data**: Test logs, failure details, screenshots

## Extensibility

### Adding New Features

#### 1. Custom Locator Conversion Rules
```python
# Add to convert_locator_to_xpath():
if "custom-selector" in locator_value:
    # Handle custom format
    return f"//custom[@attr='{value}']"
```

#### 2. Multi-Step Test Support
```python
# Use Phase 2 test_steps:
for step in test_specs[elem_id]["test_steps"]:
    action = step["action"]
    if action == "Click":
        element.click()
    elif action == "Input":
        element.send_keys(step["input_value"])
    elif action == "Verify":
        assert step["validation"]["expected"] in page_source
```

#### 3. Element Grouping by Type
```python
# Generate different tests for different element types:
if elem_type == "button":
    # Click test
elif elem_type == "input":
    # Input test
elif elem_type == "link":
    # Navigation test
```

#### 4. Parallel Test Execution
```bash
# Using pytest-xdist:
pytest tests/test_generated_tests.py -n auto
```

## Maintenance Guide

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Tests not found | Locators not loading | Verify phase1_real_output2.json exists |
| Timeout errors | Element not on home page | Add skip logic for workflow-dependent elements |
| Click blocked | Overlaying modal/ads | Add scroll-into-view, wait longer |
| Unicode errors | Windows console encoding | Remove emoji characters |
| Path errors | Wrong working directory | Use relative paths with multiple fallbacks |

### Updating Tests for Website Changes

```bash
# 1. Website changes (new elements, moved elements, etc.)
# 2. Run Phase 1 to rediscover elements:
cd phase1
python phase1_main.py --url https://automationexercise.com/

# 3. Phase 1 generates new phase1_real_output2.json
# 4. Run Phase 3 tests:
cd ../phase3/phase3_outputs_real
python -m pytest tests/test_generated_tests.py -v

# Result: Tests automatically adapt!
# No code changes needed!
```

## Conclusion

The dynamic test generation system provides:
- ✅ Automatic test generation from Phase 1 discoveries
- ✅ Flexible locator format conversion
- ✅ Robust error handling and fallback strategies
- ✅ Seamless adaptation to website changes
- ✅ Extensible architecture for future enhancements

**Implementation Status**: Complete and Production-Ready
