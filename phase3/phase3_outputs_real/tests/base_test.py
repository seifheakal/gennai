import unittest
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
