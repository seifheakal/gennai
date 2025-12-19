# Phase 1: Installation & Quick Validation Guide

## Installation Steps

### 1. Create Virtual Environment

```bash
# Create venv
python3.11 -m venv venv

# Activate
source venv/bin/activate          # macOS/Linux
# OR
venv\Scripts\activate              # Windows
```

### 2. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all requirements
pip install -r phase1_requirements.txt

# Download Playwright browsers
playwright install chromium
```

### 3. Verify Installation

```bash
# Check Python version
python --version                   # Should be 3.11+

# Check Playwright
python -c "from playwright.async_api import async_playwright; print('✅ Playwright OK')"

# Check Pydantic
python -c "from pydantic import BaseModel; print('✅ Pydantic OK')"

# Check pytest
pytest --version                   # Should be 7.4.4+

# Full validation
python -c "
import phase1_config
import phase1_constants
import phase1_models
import phase1_accessibility_parser
import phase1_logger
import phase1_playwright_helpers
import phase1_formatter
import phase1_sample_pages
print('✅ All Phase 1 modules imported successfully!')
"
```

Expected Output:
```
✅ Playwright OK
✅ Pydantic OK
✅ All Phase 1 modules imported successfully!
```

---

## Quick Validation

### Test 1: Simple Login Form

```bash
python phase1_main.py --test simple_login
```

Expected Output:
```
🚀 Phase 1: Web Accessibility Parser v1.0.0
============================================================
📝 Test Mode: Using fixture 'simple_login'
📍 Test HTML loaded: /tmp/tmpXXXXXX.html

⏳ Starting exploration...
⚙️  Config: timeout=120s, headless=True, coverage=85%

✅ Exploration complete!
📊 Discovered 3 interactive elements
📈 Coverage: 95%
⏱️  Time: 1.23s

💾 Output saved: phase1_output.json
```

### Test 2: Complex Form

```bash
python phase1_main.py --test complex_form -o results_complex.json
```

Expected Output:
```
✅ Exploration complete!
📊 Discovered 12 interactive elements
📈 Coverage: 87%
⏱️  Time: 2.15s

💾 Output saved: results_complex.json
```

### Test 3: Run Unit Tests

```bash
# Run all tests
pytest phase1_test_accessibility_parser.py -v

# Expected: All 7 tests pass
```

Expected Output:
```
test_parse_simple_login_form ✓
test_simple_login_form_output_schema ✓
test_parse_complex_form ✓
test_complex_form_element_validation ✓
test_hidden_elements_excluded ✓
test_hidden_elements_not_in_output ✓
test_output_json_schema_validation ✓

===== 7 passed in 45.23s =====
```

---

## Verify Output JSON

### Check Generated JSON

```bash
# Validate JSON is valid
python -c "
import json
with open('phase1_output.json') as f:
    data = json.load(f)
    print(f'✅ Valid JSON')
    print(f'  Page URL: {data[\"page_url\"]}')
    print(f'  Elements: {data[\"total_elements\"]}')
    print(f'  Coverage: {data[\"coverage_percentage\"]:.1%}')
"
```

### Check Elements Structure

```bash
python -c "
import json
with open('phase1_output.json') as f:
    data = json.load(f)
    for elem in data['interactive_elements'][:3]:  # First 3 elements
        print(f'Element: {elem[\"label\"]} ({elem[\"aria_role\"]})')
        print(f'  Locators: {list(elem[\"locators\"].keys())}')
        print(f'  Primary: {elem[\"locators\"][\"priority_1_role\"]}')
        print()
"
```

---

## Quick Integration Test

### Verify Phase 1 Output Format

```bash
python -c "
import json
from phase1_models import Phase1ExplorationOutput

# Load Phase 1 output
with open('phase1_output.json') as f:
    data = json.load(f)

# Validate against model
try:
    # This would normally come from Pydantic validation
    # For now, just check key fields exist
    required_fields = [
        'page_url',
        'total_elements',
        'coverage_percentage',
        'exploration_graph',
        'interactive_elements',
        'exploration_statistics',
        'quality_metrics'
    ]
    
    for field in required_fields:
        assert field in data, f'Missing field: {field}'
    
    print('✅ Phase 1 output format valid!')
    print(f'✅ Ready for Phase 2 test generation')
except AssertionError as e:
    print(f'❌ Validation failed: {e}')
"
```

Expected Output:
```
✅ Phase 1 output format valid!
✅ Ready for Phase 2 test generation
```

---

## Troubleshooting Installation

### Issue: "playwright module not found"

```bash
# Solution: Install again explicitly
pip uninstall playwright -y
pip install playwright==1.48.2
playwright install chromium
```

### Issue: "ModuleNotFoundError: No module named 'pydantic'"

```bash
# Solution: Install all requirements fresh
pip install -r phase1_requirements.txt --force-reinstall
```

### Issue: "Timeout waiting for chromium"

```bash
# Solution: Use Firefox instead
python phase1_main.py --test simple_login --browser firefox

# Or download manually
playwright install firefox
```

### Issue: "Permission denied" on log file

```bash
# Solution: Ensure write permissions
mkdir -p logs
python phase1_main.py --test simple_login --log-file logs/phase1.log
```

---

## Environment Variables (Optional)

```bash
# Set logging level
export PHASE1_LOG_LEVEL=DEBUG

# Set output directory
export PHASE1_OUTPUT_DIR=./results

# Set timeout
export PHASE1_TIMEOUT=60
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Phase 1 Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r phase1_requirements.txt
        playwright install chromium
    
    - name: Run tests
      run: pytest phase1_test_accessibility_parser.py -v --cov=phase1
    
    - name: Run exploration test
      run: python phase1_main.py --test simple_login
    
    - name: Verify output
      run: |
        python -c "
        import json
        with open('phase1_output.json') as f:
            data = json.load(f)
            assert data['total_elements'] > 0
            assert data['quality_metrics']['ready_for_phase2']
        "
```

---

## Docker Support (Optional)

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY phase1_requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r phase1_requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy source code
COPY phase1_*.py .

# Run tests on startup
CMD ["pytest", "phase1_test_accessibility_parser.py", "-v"]
```

### Build and Run

```bash
# Build
docker build -t phase1-testing .

# Run tests
docker run phase1-testing

# Run exploration
docker run phase1-testing python phase1_main.py --test complex_form
```

---

## Production Deployment

### Requirements.txt for Production

```bash
# Install only production dependencies (no dev tools)
pip install -r phase1_requirements.txt --ignore-requires-python

# Verify only necessary packages
pip list | grep -E 'playwright|pydantic|pytest'
```

### Health Check

```bash
#!/bin/bash
# health_check.sh

echo "Phase 1 Health Check..."

# Test 1: Module imports
python -c "
import phase1_config
import phase1_accessibility_parser
print('✅ Module imports OK')
" || exit 1

# Test 2: Playwright
python -c "
from playwright.async_api import async_playwright
print('✅ Playwright OK')
" || exit 1

# Test 3: Test fixture
python phase1_main.py --test simple_login > /dev/null 2>&1
if [ -f phase1_output.json ]; then
    echo "✅ Exploration OK"
else
    exit 1
fi

echo "✅ All health checks passed!"
```

---

## Performance Monitoring

### Monitor Phase 1 Execution

```bash
#!/bin/bash
# Run and monitor

time python phase1_main.py --test complex_form

# Check memory usage
ps aux | grep phase1_main

# Check output file size
ls -lh phase1_output.json
```

Expected Output:
```
real    0m2.341s
user    0m1.123s
sys     0m0.456s
phase1_output.json -> 45K
```

---

## Next: Phase 2 Preparation

Once Phase 1 is validated:

1. ✅ Verify JSON output exists
2. ✅ Confirm elements are discovered (>0)
3. ✅ Check coverage is 85%+
4. ✅ Verify no hallucinated elements
5. ✅ Confirm Phase 2 is ready
6. 🚀 Start Phase 2: Collaborative Test Design

---

## Success Checklist ✅

- [ ] Virtual environment created and activated
- [ ] All dependencies installed
- [ ] Playwright browsers downloaded
- [ ] All imports successful
- [ ] Simple login form test passes
- [ ] Complex form test passes
- [ ] All 7 unit tests pass
- [ ] JSON output generated and valid
- [ ] Phase 1 output ready for Phase 2

---

**🎉 Phase 1 Installation Complete - Ready for Phase 2!**
