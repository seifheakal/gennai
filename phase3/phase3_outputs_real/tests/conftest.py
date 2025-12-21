import pytest
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
