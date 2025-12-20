"""
Phase 3: Layer 1 - Test Code Generator
Converts Phase 2 JSON test cases into executable Selenium + Python tests
"""

import sys
from pathlib import Path

# Add phase2 directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "phase2"))

from typing import Dict, List, Tuple, Optional
import json
from phase2_models import TestCase, TestStep


class TestCodeGenerator:
    """
    LAYER 1: Test Code Generator
    Converts Phase 2 test specifications to executable test code
    """

    def __init__(self, test_cases_json: str, framework: str = "selenium", 
                 language: str = "python"):
        """
        Initialize test code generator.

        Args:
            test_cases_json: Path to phase2_test_cases.json
            framework: "selenium", "playwright", "cypress"
            language: "python", "javascript", "java"
        """
        self.test_cases_json = test_cases_json
        self.framework = framework
        self.language = language
        self.test_cases = self._load_test_cases()
        self.imports = self._generate_imports()

    def _load_test_cases(self) -> List[Dict]:
        """Load Phase 2 test cases from JSON"""
        try:
            with open(self.test_cases_json) as f:
                data = json.load(f)
                return data.get("tests", [])
        except FileNotFoundError:
            print(f"⚠️  Test cases file not found: {self.test_cases_json}")
            return []

    def _generate_imports(self) -> str:
        """Generate import statements based on framework"""
        if self.framework == "selenium" and self.language == "python":
            return """import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from datetime import datetime
import os
"""
        elif self.framework == "playwright" and self.language == "python":
            return """import pytest
from playwright.sync_api import sync_playwright, expect
import asyncio
"""
        elif self.framework == "cypress" and self.language == "javascript":
            return """describe('E2E Tests', () => {
    before(() => {
        cy.visit(Cypress.env('BASE_URL') || 'http://localhost:8080');
    });
"""
        return ""

    def generate_all_tests(self) -> Dict[str, str]:
        """
        Generate all test methods from Phase 2 test cases.

        Returns:
            Dictionary of {test_name: test_code}
        """
        test_code = {}

        for test_case in self.test_cases:
            test_name = test_case.get("test_id", "unknown")
            code = self._generate_test_method(test_case)
            test_code[test_name] = code

        return test_code

    def _generate_test_method(self, test_case: Dict) -> str:
        """
        Generate single test method.

        Args:
            test_case: Test case specification

        Returns:
            Complete test method code
        """
        test_id = test_case.get("test_id", "test_unknown")
        title = test_case.get("title", "Test")
        steps = test_case.get("test_steps", [])
        expected = test_case.get("expected_result", "")

        code = f'''    def test_{test_id.lower()}(self):
        """Test: {test_id} - {title}"""
        try:
            # Test Steps
'''

        for i, step in enumerate(steps, 1):
            code += f'\n            # Step {i}: {step.get("description", "")}\n'
            code += self._generate_step_code(step)

        code += f'\n            # Expected Result: {expected}\n'
        code += self._generate_assertions(expected)

        code += '''
        except Exception as e:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"test_failures/{test_id}_{timestamp}.png"
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            self.driver.save_screenshot(screenshot_path)
            raise AssertionError(f"Test failed: {str(e)}")
'''

        return code

    def _generate_step_code(self, step: Dict) -> str:
        """Generate code for a single test step"""
        action = step.get("action", "")
        element_id = step.get("element_id", "")
        value = step.get("value", "")

        if action == "navigate":
            return f'''            self.driver.get("{value}")
            time.sleep(2)  # Wait for page load
'''

        elif action == "click":
            return f'''            element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "{element_id}"))
            )
            element.click()
            time.sleep(1)
'''

        elif action == "type":
            return f'''            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "{element_id}"))
            )
            element.clear()
            element.send_keys("{value}")
            time.sleep(0.5)
'''

        elif action == "select":
            return f'''            element = self.driver.find_element(By.ID, "{element_id}")
            from selenium.webdriver.common.keys import Keys
            element.send_keys("{value}")
            time.sleep(0.5)
'''

        elif action == "wait":
            timeout = value or "10"
            return f'''            WebDriverWait(self.driver, {timeout}).until(
                EC.presence_of_element_located((By.ID, "{element_id}"))
            )
'''

        return f'''            # Action: {action}\n            time.sleep(1)\n'''

    def _generate_assertions(self, expected: str) -> str:
        """Generate assertion code"""
        return f'''            # Verify expected result
            self.assertIn("{expected}", self.driver.page_source)
'''

    def generate_base_test_class(self) -> str:
        """Generate base test class with setUp/tearDown"""
        return '''import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import os


class BaseTestCase(unittest.TestCase):
    """Base test class with setup/teardown"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.base_url = os.getenv("BASE_URL", "http://localhost:8080")

    def setUp(self):
        """Initialize WebDriver before each test"""
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")  # Uncomment for headless mode
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)
        self.driver.maximize_window()

    def tearDown(self):
        """Clean up after each test"""
        if self.driver:
            self.driver.quit()


if __name__ == "__main__":
    unittest.main()
'''

    def generate_pytest_conftest(self) -> str:
        """Generate pytest configuration file"""
        return '''import pytest
import os
from selenium import webdriver


@pytest.fixture(scope="session")
def base_url():
    """Get base URL from environment or default"""
    return os.getenv("BASE_URL", "http://localhost:8080")


@pytest.fixture
def driver(base_url):
    """Create WebDriver for each test"""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    driver.maximize_window()
    
    yield driver
    
    driver.quit()


@pytest.fixture
def page(driver, base_url):
    """Navigate to base URL"""
    driver.get(base_url)
    return driver


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "regression: mark test as regression"
    )
    config.addinivalue_line(
        "markers", "smoke: mark test as smoke"
    )
'''

    def write_tests_to_files(self, output_dir: str = "generated_tests"):
        """
        Write generated tests to files.

        Args:
            output_dir: Directory to write test files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Write base class
        base_file = output_path / "base_test.py"
        base_file.write_text(self.generate_base_test_class())
        print(f"✅ Created: {base_file}")

        # Write conftest
        conftest_file = output_path / "conftest.py"
        conftest_file.write_text(self.generate_pytest_conftest())
        print(f"✅ Created: {conftest_file}")

        # Write test methods
        test_class = f'''from base_test import BaseTestCase
from datetime import datetime
import os
import time


class TestSuite(BaseTestCase):
    """Comprehensive test suite from Phase 2"""

'''

        tests = self.generate_all_tests()
        for test_name, test_code in tests.items():
            test_class += test_code + "\n\n"

        test_class += '''
if __name__ == "__main__":
    import unittest
    unittest.main()
'''

        test_file = output_path / "test_generated_tests.py"
        test_file.write_text(test_class)
        print(f"✅ Created: {test_file} ({len(tests)} tests)")

        return {
            "base_test": str(base_file),
            "conftest": str(conftest_file),
            "tests": str(test_file),
            "test_count": len(tests),
        }
