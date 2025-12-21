from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import time


class HomepagePage:
    """Page Object

    def __init__(self, driver):
        self.driver = driver for HomePage"""

    # Page URL
    URL = "/homepage"

    # Element Locators (Using best strategy + confidence from Phase 1)

    @property
    def test_cases(self):
        """
        Test Cases - Confidence: 95%
        Locator: p1_role
        """
        try:
            return WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "p1_role"))
            )
        except TimeoutException:
            raise TimeoutException(f"Element 'test_cases' not found within 5s")

    @property
    def apis_list_for_practice(self):
        """
        APIs list for practice - Confidence: 95%
        Locator: p1_role
        """
        try:
            return WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "p1_role"))
            )
        except TimeoutException:
            raise TimeoutException(f"Element 'apis_list_for_practice' not found within 5s")

    @property
    def test_cases(self):
        """
        Test Cases - Confidence: 95%
        Locator: p1_role
        """
        try:
            return WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "p1_role"))
            )
        except TimeoutException:
            raise TimeoutException(f"Element 'test_cases' not found within 5s")

    @property
    def apis_list_for_practice(self):
        """
        APIs list for practice - Confidence: 95%
        Locator: p1_role
        """
        try:
            return WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "p1_role"))
            )
        except TimeoutException:
            raise TimeoutException(f"Element 'apis_list_for_practice' not found within 5s")

    @property
    def test_cases(self):
        """
        Test Cases - Confidence: 95%
        Locator: p1_role
        """
        try:
            return WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "p1_role"))
            )
        except TimeoutException:
            raise TimeoutException(f"Element 'test_cases' not found within 5s")

    @property
    def apis_list_for_practice(self):
        """
        APIs list for practice - Confidence: 95%
        Locator: p1_role
        """
        try:
            return WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "p1_role"))
            )
        except TimeoutException:
            raise TimeoutException(f"Element 'apis_list_for_practice' not found within 5s")

    @property
    def continue_shopping(self):
        """
        Continue Shopping - Confidence: 95%
        Locator: p1_role
        """
        try:
            return WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "p1_role"))
            )
        except TimeoutException:
            raise TimeoutException(f"Element 'continue_shopping' not found within 5s")

    @property
    def (self):
        """
         - Confidence: 95%
        Locator: p1_role
        """
        try:
            return WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "p1_role"))
            )
        except TimeoutException:
            raise TimeoutException(f"Element '' not found within 5s")

    def click_test_cases(self):
        """Click Test Cases"""
        self.test_cases.click()
        time.sleep(1)
        return self

    def click_apis_list_for_practice(self):
        """Click APIs list for practice"""
        self.apis_list_for_practice.click()
        time.sleep(1)
        return self

    def click_test_cases(self):
        """Click Test Cases"""
        self.test_cases.click()
        time.sleep(1)
        return self

    def click_apis_list_for_practice(self):
        """Click APIs list for practice"""
        self.apis_list_for_practice.click()
        time.sleep(1)
        return self

    def click_test_cases(self):
        """Click Test Cases"""
        self.test_cases.click()
        time.sleep(1)
        return self

    def click_apis_list_for_practice(self):
        """Click APIs list for practice"""
        self.apis_list_for_practice.click()
        time.sleep(1)
        return self

    def click_continue_shopping(self):
        """Click Continue Shopping"""
        self.continue_shopping.click()
        time.sleep(1)
        return self

    def click_(self):
        """Click """
        self..click()
        time.sleep(1)
        return self

    # Utility methods
    
    def wait_for_page_load(self, timeout: int = 10):
        """Wait for page to fully load"""
        time.sleep(2)  # Initial page load
        return self
    
    def get_page_title(self):
        """Get page title"""
        return self.driver.title
    
    def get_current_url(self):
        """Get current URL"""
        return self.driver.current_url
    
    def take_screenshot(self, name: str = "screenshot"):
        """Take screenshot"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.driver.save_screenshot(f"screenshots/{name}_{timestamp}.png")
        return self
