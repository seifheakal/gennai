"""Pytest configuration and fixtures"""

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
            print(f"✅ PASSED: {report.nodeid}")
        elif report.outcome == "failed":
            print(f"❌ FAILED: {report.nodeid}")
        elif report.outcome == "skipped":
            print(f"⏭️  SKIPPED: {report.nodeid}")
