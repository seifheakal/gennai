"""
Phase 3: Layer 3 - Test Framework Builder
Builds complete test framework structure (pytest, unittest, testng)
"""

from typing import Dict
from pathlib import Path


class TestFrameworkBuilder:
    """
    LAYER 3: Test Framework Builder
    Creates complete test framework with fixtures, configuration, runners
    """

    def __init__(self, framework_type: str = "pytest", language: str = "python"):
        """
        Initialize framework builder.

        Args:
            framework_type: "pytest", "unittest", "testng"
            language: "python", "javascript", "java"
        """
        self.framework_type = framework_type
        self.language = language

    def generate_pytest_structure(self) -> Dict[str, str]:
        """Generate pytest framework structure"""
        return {
            "conftest.py": self._generate_pytest_conftest(),
            "pytest.ini": self._generate_pytest_ini(),
            "base_test.py": self._generate_base_test_class(),
            "test_runner.py": self._generate_test_runner(),
            "requirements.txt": self._generate_requirements(),
        }

    def _generate_pytest_conftest(self) -> str:
        """Generate pytest conftest.py"""
        return '''"""Pytest configuration and fixtures"""

import pytest
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json


@pytest.fixture(scope="session")
def base_url():
    """Get base URL from environment or default"""
    return os.getenv("BASE_URL", "http://localhost:8080")


@pytest.fixture(scope="session")
def browser_type():
    """Get browser type from environment or default"""
    return os.getenv("BROWSER", "chrome")


@pytest.fixture
def driver(base_url, browser_type):
    """
    Create WebDriver for each test.
    
    Args:
        base_url: Base URL for tests
        browser_type: Browser to use (chrome, firefox, edge)
    
    Yields:
        WebDriver instance
    """
    options = Options()
    
    # Add common options
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Uncomment for headless mode
    # options.add_argument("--headless")
    
    # Create driver based on browser type
    if browser_type == "chrome":
        driver = webdriver.Chrome(options=options)
    elif browser_type == "firefox":
        driver = webdriver.Firefox()
    elif browser_type == "edge":
        driver = webdriver.Edge()
    else:
        driver = webdriver.Chrome(options=options)
    
    driver.implicitly_wait(10)
    driver.maximize_window()
    
    yield driver
    
    # Cleanup
    driver.quit()


@pytest.fixture
def page(driver, base_url):
    """
    Navigate to base URL before each test.
    
    Args:
        driver: WebDriver instance
        base_url: Base URL to navigate to
    
    Yields:
        WebDriver instance at base URL
    """
    driver.get(base_url)
    yield driver


@pytest.fixture
def test_data():
    """Load test data from JSON"""
    test_data_file = "test_data/test_data.json"
    if os.path.exists(test_data_file):
        with open(test_data_file) as f:
            return json.load(f)
    return {}


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "regression: mark test as regression test"
    )
    config.addinivalue_line(
        "markers", "smoke: mark test as smoke test"
    )
    config.addinivalue_line(
        "markers", "critical: mark test as critical"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_runtest_logreport(report):
    """Log test results"""
    if report.when == "call":
        if report.outcome == "passed":
            print(f"[OK] PASSED: {report.nodeid}")
        elif report.outcome == "failed":
            print(f"[ERROR] FAILED: {report.nodeid}")
        elif report.outcome == "skipped":
            print(f"⏭️  SKIPPED: {report.nodeid}")
'''

    def _generate_pytest_ini(self) -> str:
        """Generate pytest.ini"""
        return '''[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Logging
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)8s] %(message)s
log_cli_date_format = %Y-%m-%d %H:%M:%S

# Report
junit_family = xunit2
addopts = 
    --tb=short
    --strict-markers
    --disable-warnings
    -ra
    --maxfail=5

markers =
    regression: Regression tests
    smoke: Smoke tests
    critical: Critical tests
    slow: Slow running tests
'''

    def _generate_base_test_class(self) -> str:
        """Generate base test class"""
        return '''"""Base test class for all tests"""

import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
from datetime import datetime


class BaseTestCase(unittest.TestCase):
    """Base test class with common setup/teardown"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once"""
        cls.base_url = os.getenv("BASE_URL", "http://localhost:8080")
        cls.headless = os.getenv("HEADLESS", "false").lower() == "true"

    def setUp(self):
        """Initialize WebDriver before each test"""
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        if self.headless:
            options.add_argument("--headless")
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 10)

    def tearDown(self):
        """Clean up after each test"""
        # Take screenshot on failure
        if hasattr(self, '_outcome'):
            result = self._outcome.result
            if result.failures or result.errors:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                test_name = self._testMethodName
                os.makedirs("test_failures", exist_ok=True)
                self.driver.save_screenshot(f"test_failures/{test_name}_{timestamp}.png")
        
        if self.driver:
            self.driver.quit()

    # Utility methods
    
    def find_element(self, locator):
        """Find element with explicit wait"""
        return self.wait.until(EC.presence_of_element_located(locator))
    
    def click_element(self, locator):
        """Click element with wait"""
        element = self.wait.until(EC.element_to_be_clickable(locator))
        element.click()
    
    def type_text(self, locator, text):
        """Type text in element"""
        element = self.find_element(locator)
        element.clear()
        element.send_keys(text)
    
    def wait_for_text(self, locator, text, timeout=10):
        """Wait for element to contain text"""
        WebDriverWait(self.driver, timeout).until(
            EC.text_to_be_present_in_element(locator, text)
        )
    
    def take_screenshot(self, name="screenshot"):
        """Take screenshot"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("screenshots", exist_ok=True)
        self.driver.save_screenshot(f"screenshots/{name}_{timestamp}.png")


if __name__ == "__main__":
    unittest.main()
'''

    def _generate_test_runner(self) -> str:
        """Generate test runner script"""
        return '''#!/usr/bin/env python
"""Test runner with argument parsing"""

import argparse
import os
import sys
import pytest


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Run E2E tests")
    
    parser.add_argument(
        "--browser",
        choices=["chrome", "firefox", "edge"],
        default="chrome",
        help="Browser to use"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode"
    )
    
    parser.add_argument(
        "--url",
        default="http://localhost:8080",
        help="Base URL for tests"
    )
    
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="Number of parallel workers"
    )
    
    parser.add_argument(
        "--tag",
        choices=["smoke", "regression", "critical"],
        help="Run tests with specific tag"
    )
    
    parser.add_argument(
        "--report",
        default="html",
        choices=["html", "junit", "json"],
        help="Report format"
    )
    
    args = parser.parse_args()
    
    # Set environment variables
    os.environ["BROWSER"] = args.browser
    os.environ["HEADLESS"] = str(args.headless).lower()
    os.environ["BASE_URL"] = args.url
    
    # Build pytest arguments
    pytest_args = ["tests", "-v", "--tb=short"]
    
    # Add parallel execution if requested
    if args.parallel > 1:
        pytest_args.extend(["-n", str(args.parallel)])
    
    # Add tag filter
    if args.tag:
        pytest_args.extend(["-m", args.tag])
    
    # Add reporting
    if args.report == "html":
        pytest_args.extend(["--html=report.html", "--self-contained-html"])
    elif args.report == "junit":
        pytest_args.extend(["--junit-xml=report.xml"])
    elif args.report == "json":
        pytest_args.extend(["--json-report", "--json-report-file=report.json"])
    
    # Run tests
    print(f"[PHASE] Running tests with: {' '.join(pytest_args)}")
    exit_code = pytest.main(pytest_args)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
'''

    def _generate_requirements(self) -> str:
        """Generate requirements.txt"""
        return '''# Web Automation
selenium==4.15.0
playwright==1.40.0

# Testing Framework
pytest==7.4.3
pytest-xdist==3.5.0
pytest-html==4.1.1
pytest-json-report==1.5.0

# Utilities
python-dotenv==1.0.0
requests==2.31.0

# Code Quality
pylint==3.0.3
black==23.12.1
isort==5.13.2
mypy==1.8.0

# Data Handling
openpyxl==3.11.0
pandas==2.1.4

# Reporting
allure-pytest==2.13.2
'''

    def write_framework_to_files(self, output_dir: str = "."):
        """
        Write framework files to directory.

        Args:
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        files = self.generate_pytest_structure()

        for file_name, content in files.items():
            file_path = output_path / file_name
            file_path.write_text(content, encoding='utf-8')
            print(f"[OK] Created: {file_path}")

        # Create directories
        (output_path / "tests").mkdir(exist_ok=True)
        (output_path / "pages").mkdir(exist_ok=True)
        (output_path / "test_data").mkdir(exist_ok=True)
        (output_path / "screenshots").mkdir(exist_ok=True)
        (output_path / "test_failures").mkdir(exist_ok=True)

        print(f"\n[OK] Test framework created in: {output_path}")

        return {
            "framework": str(output_path),
            "files_created": len(files),
            "directories_created": 5,
        }
