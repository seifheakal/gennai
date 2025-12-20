"""Base test class for all tests"""

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
