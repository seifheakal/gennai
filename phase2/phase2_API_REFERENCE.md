# Phase 2: API Reference

## Core Classes

### Phase1Parser (Layer 1)
```python
parser = Phase1Parser("phase1_output.json")
phase1 = parser.parse()  # Parse and validate Phase 1 output

# Access methods
element = parser.get_element_by_id("elem_001")
elements = parser.get_elements_by_type("button")
workflows = parser.get_workflows()
summary = parser.summary()
```

### EquivalencePartitioning (Layer 2A)
```python
ep = EquivalencePartitioning(phase1)
tests = ep.generate_ep_tests()  # Generate ~15-20 EP tests

# Tests cover:
# - Valid/invalid/boundary partitions
# - Element types: inputs, buttons, dropdowns, checkboxes
```

### BoundaryValueAnalysis (Layer 2B)
```python
bva = BoundaryValueAnalysis(phase1)
tests = bva.generate_bva_tests()  # Generate ~10-15 BVA tests

# Tests cover:
# - min-1, min, min+1, max-1, max, max+1
# - Numeric and string boundaries
```

### TestGenerator (Layer 2 Orchestrator)
```python
generator = TestGenerator(parser)
tests = generator.generate_tests(
    target_coverage=85.0,
    max_tests=100,
    min_tests=50,
)

# Returns: List[TestCase] with all 3 algorithms
# Stats available via: generator.get_algorithm_stats(tests)
```

### CoverageCalculator (Layer 3)
```python
calc = CoverageCalculator(parser, tests)
coverage = calc.calculate_coverage()

# Coverage types:
print(f"Element: {coverage.element_coverage:.1f}%")
print(f"Path: {coverage.path_coverage:.1f}%")
print(f"Scenario: {coverage.scenario_coverage:.1f}%")
print(f"Blended: {coverage.blended_coverage:.1f}%")

# Identify gaps
gaps = coverage.coverage_gaps
```

### CoverageVisualizer (Layer 4)
```python
viz = CoverageVisualizer(coverage, parser, tests)
heatmap = viz.generate_heatmap_data()  # Generate visualization data
report = viz.generate_coverage_report()  # Full report
quality = viz.get_quality_score()  # 0-100 score
```

### HITLManager (Layer 5)
```python
hitl = HITLManager(generator, parser)
result = hitl.run_hitl_loop(rounds=2)

# Results contain:
# - Feedback from each round
# - Patterns learned
# - Improvement metrics
```

### Phase2Orchestrator (Main)
```python
orchestrator = Phase2Orchestrator("phase1_output.json")
result = orchestrator.run_full_pipeline(
    target_coverage=85.0,
    hitl_rounds=2,
    output_dir="./results"
)

# Saves 4 JSON files:
# - phase2_test_cases.json
# - phase2_coverage_metrics.json
# - phase2_coverage_heatmap.json
# - phase2_feedback_logs.json
```

---

## Data Models

### TestCase
```python
{
  "test_id": "test_001",
  "title": str,
  "algorithm_used": Literal["ep", "bva", "state_combination"],
  "elements_used": List[str],  # element IDs
  "test_steps": List[TestStep],
  "expected_result": str,
  "coverage_contribution": float,
  "importance_score": float,
  "confidence": float,
}
```

### CoverageMetrics
```python
{
  "element_coverage": float,  # %
  "path_coverage": float,  # %
  "scenario_coverage": float,  # %
  "blended_coverage": float,  # %
  "coverage_by_type": Dict[str, float],  # by element type
  "coverage_gaps": List[CoverageGap],
  "total_tests": int,
  "total_elements": int,
  "tested_elements": int,
}
```

### FeedbackRound
```python
{
  "round_number": int,
  "tests_presented": int,
  "feedback_items": List[TestCaseFeedback],
  "approval_rate": float,  # 0-1
  "patterns_learned": List[str],
}
```

### HITLResult
```python
{
  "feedback_rounds": List[FeedbackRound],
  "overall_approval_rate": float,  # 0-1
  "improvements_made": List[str],
}
```

---

## Coverage Calculation

### Formula
```
Blended = 0.4×Element + 0.35×Path + 0.25×Scenario

Element = (tested_elements / total_elements) × 100
Path = (tested_workflows / total_workflows) × 100
Scenario = (tested_scenarios / reachable_scenarios) × 100
```

### Example
```
Element Coverage: 86.5%
Path Coverage: 80.0%
Scenario Coverage: 87.5%

Blended = (0.4 × 86.5) + (0.35 × 80.0) + (0.25 × 87.5)
        = 34.6 + 28.0 + 21.875
        = 84.475%
```

---

## Heatmap Color Coding

| Coverage | Color | Hex |
|----------|-------|-----|
| 90%+ | Green | #00AA00 |
| 75-90% | Orange | #FFAA00 |
| <75% | Red | #FF0000 |

---

## Test Generation Priority Formula

```
Priority = 0.3×Confidence + 0.3×CoverageGap + 0.2×Risk + 0.2×Complexity

Where:
- Confidence: Element locator confidence (0-1)
- CoverageGap: Coverage gain if this test passes (0-1)
- Risk: Business risk of failure (0-1)
- Complexity: Test complexity (0-1)
```

---

## Hallucination Detection

### Validation Checks
```python
detector = HallucinationDetector(phase1)
result = detector.validate_test_batch(tests)

# Returns:
{
  "valid_tests": int,
  "hallucinated_tests": int,
  "hallucination_rate": float,
  "errors": List[str],
}

# Checks performed:
# ✓ Element ID exists in Phase 1
# ✓ All locators match Phase 1
# ✓ Confidence scores valid (0-1)
# ✓ Element types match
```

---

## Example: Full Pipeline

```python
from phase2_main import Phase2Orchestrator

# Step 1: Initialize
orchestrator = Phase2Orchestrator("phase1_output.json")

# Step 2: Run full pipeline
result = orchestrator.run_full_pipeline(
    target_coverage=85.0,
    hitl_rounds=2,
    output_dir="./results"
)

# Step 3: Check results
print(f"✅ Tests Generated: {result['metrics']['total_tests']}")
print(f"✅ Coverage Achieved: {result['metrics']['blended_coverage']}")
print(f"✅ HITL Approval: {result['metrics']['hitl_approval_rate']}")
print(f"✅ Coverage Target Met: {result['metrics']['coverage_target_met']}")

# Step 4: Access outputs
# - results/phase2_test_cases.json
# - results/phase2_coverage_metrics.json
# - results/phase2_coverage_heatmap.json
# - results/phase2_feedback_logs.json
```

---

## Configuration

### Coverage Target
```python
# Default: 85%
# Adjust in orchestrator:
result = orchestrator.run_full_pipeline(
    target_coverage=90.0,  # Set to 90%
)
```

### HITL Rounds
```python
# Default: 2 rounds
# Adjust:
result = orchestrator.run_full_pipeline(
    hitl_rounds=3,  # Run 3 feedback rounds
)
```

### Test Limits
```python
# In TestGenerator.generate_tests():
# - min_tests: 50 (minimum output)
# - max_tests: 100 (maximum output)
# - target: automatically selects between min/max
```

---

## Performance

| Operation | Time | Status |
|-----------|------|--------|
| Parse Phase 1 | <100ms | ✅ |
| Generate 50 tests | <500ms | ✅ |
| Calculate coverage | <200ms | ✅ |
| Generate heatmap | <100ms | ✅ |
| HITL 1 round | ~2s | ✅ |
| Full pipeline (2 rounds) | ~5-10s | ✅ |

---

## Error Handling

### Common Errors

```python
# Error: Phase 1 file not found
try:
    parser = Phase1Parser("phase1_output.json")
except FileNotFoundError:
    print("Phase 1 output file not found")

# Error: Invalid Phase 1 format
try:
    phase1 = parser.parse()
except ValidationError as e:
    print(f"Invalid Phase 1 format: {e}")

# Error: Hallucinations detected
result = detector.validate_test_batch(tests)
if result["hallucination_rate"] > 0:
    print(f"⚠️  Hallucinations detected: {result['errors']}")
```

---

## Extension Points

### Custom Test Generation Algorithm
```python
class CustomAlgorithm:
    def generate_tests(self, parser):
        """Your custom test generation logic"""
        return List[TestCase]

# Integrate into TestGenerator
```

### Custom Coverage Metric
```python
def custom_blend(element, path, scenario):
    """Your custom blending formula"""
    return weighted_combination(...)

# Use in CoverageCalculator
```

### Custom HITL Feedback
```python
def custom_feedback_collection(tests):
    """Your custom feedback collection logic"""
    return List[TestCaseFeedback]

# Use in HITLManager
```

---

**Phase 2 API Reference Complete** ✅
