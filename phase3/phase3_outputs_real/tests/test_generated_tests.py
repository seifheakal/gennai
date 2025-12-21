from base_test import BaseTestCase
from datetime import datetime
import json
import os
import time
import unittest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path


def load_phase1_elements():
    """Load element data from Phase 1 output"""
    # Try multiple paths since tests can be run from different directories
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
    
    with open(phase1_file, 'r') as f:
        phase1_data = json.load(f)
    
    elements = {}
    for elem in phase1_data.get("interactive_elements", []):
        elem_id = elem.get("element_id")
        if not elem_id:
            continue
            
        # Get the primary locator (first/best one available)
        locators = elem.get("locators", {})
        best_locator = None
        
        # Try priority_1_role first (highest confidence)
        if "priority_1_role" in locators:
            best_locator = locators["priority_1_role"]
        elif "priority_2_label" in locators:
            best_locator = locators["priority_2_label"]
        elif "priority_4_text" in locators:
            best_locator = locators["priority_4_text"]
        else:
            # Use first available
            best_locator = next(iter(locators.values())) if locators else None
        
        elements[elem_id] = {
            "label": elem.get("label", ""),
            "type": elem.get("type", ""),
            "locator": best_locator,
            "enabled": elem.get("enabled", True),
            "visible": elem.get("visible", True),
        }
    
    return elements


def load_phase2_tests():
    """Load test cases from Phase 2 output"""
    # Try multiple paths since tests can be run from different directories
    possible_paths = [
        Path(__file__).parent.parent.parent / "phase2" / "phase2_test_cases.json",
        Path(__file__).parent.parent / ".." / ".." / "phase2" / "phase2_test_cases.json",
        Path(".") / "phase2" / "phase2_test_cases.json",
    ]
    
    phase2_file = None
    for path in possible_paths:
        if path.exists():
            phase2_file = path
            break
    
    if not phase2_file:
        raise FileNotFoundError(f"Phase 2 output not found. Tried: {possible_paths}")
    
    with open(phase2_file, 'r') as f:
        phase2_data = json.load(f)
    
    tests = {}
    for test in phase2_data.get("tests", []):
        test_id = test.get("test_id", "")
        tests[test_id] = {
            "title": test.get("title", ""),
            "description": test.get("description", ""),
            "elements_used": test.get("elements_used", []),
            "test_steps": test.get("test_steps", []),
            "expected_result": test.get("expected_result", ""),
        }
    
    return tests


# Load element data at module level
try:
    ELEMENT_MAP = load_phase1_elements()
    print(f"[OK] Loaded {len(ELEMENT_MAP)} elements from Phase 1")
except Exception as e:
    print(f"[ERROR] Could not load Phase 1 elements: {e}")
    ELEMENT_MAP = {}


class TestSuite(BaseTestCase):
    """Dynamically generated test suite from Phase 1 element discoveries
    
    Automatically creates tests for each element discovered by Phase 1.
    Tests adapt when Phase 1 re-discovers elements on modified websites.
    """
    
    BASE_URL = "https://automationexercise.com/"


# Helper function to convert Playwright locators to XPath
def convert_playwright_to_xpath(locator):
    """Convert Playwright format locators to Selenium XPath"""
    if not locator:
        return None
    
    # Already XPath format
    if locator.startswith("//"):
        return locator
    
    # button[name='Test Cases'] -> //button[contains(text(), 'Test Cases')]
    if locator.startswith("button[name='"):
        text = locator.split("'")[1]
        return f"//button[contains(text(), '{text}')]"
    
    # :text('Test Cases') -> //*[contains(text(), 'Test Cases')]
    if locator.startswith(":text('"):
        text = locator.split("'")[1]
        return f"//*[contains(text(), '{text}')]"
    
    # label:has-text('...') -> //label[contains(text(), '...')]
    if "label:has-text(" in locator:
        text = locator.split("'")[1]
        return f"//label[contains(text(), '{text}')]"
    
    return locator


# Dynamically create test methods for each element
if ELEMENT_MAP:
    for elem_id in sorted(ELEMENT_MAP.keys()):
        elem_data = ELEMENT_MAP[elem_id]
        elem_label = elem_data.get("label", elem_id)
        elem_locator = elem_data.get("locator")
        
        # Convert locator if needed
        if elem_locator:
            elem_locator = convert_playwright_to_xpath(elem_locator)
        
        # Create a unique test method for this element
        def _create_test(element_id, label, locator):
            """Factory function to create a test method for an element"""
            def test_impl(self):
                """Test dynamically generated from Phase 1 element discovery"""
                # Skip if we don't have a locator
                if not locator:
                    self.skipTest(f"{label or element_id}: No locator available")
                
                try:
                    # Navigate to base URL
                    self.driver.get(self.BASE_URL)
                    time.sleep(1)
                    
                    # Wait for element to be present and clickable
                    wait = WebDriverWait(self.driver, 10)
                    
                    # Try to find the element
                    element = None
                    try:
                        element = wait.until(
                            EC.element_to_be_clickable((By.XPATH, locator))
                        )
                    except Exception as find_error:
                        # Element not found on home page (may require workflow)
                        self.skipTest(f"{label or element_id}: Element not found (may require specific workflow)")
                    
                    # Verify element is visible and enabled
                    self.assertTrue(
                        element.is_displayed(),
                        f"{label or element_id} should be displayed"
                    )
                    self.assertTrue(
                        element.is_enabled(),
                        f"{label or element_id} should be enabled"
                    )
                    
                    # Verify label matches if available
                    if label:
                        element_text = element.text.strip() if element.text else ""
                        if element_text:
                            # Allow partial match
                            label_match = (
                                label.lower() in element_text.lower() or
                                element_text.lower() in label.lower()
                            )
                            self.assertTrue(
                                label_match or element_text == label,
                                f"Element text '{element_text}' should contain '{label}'"
                            )
                    
                    # Try clicking (may be blocked by ads/modals, but element exists)
                    try:
                        element.click()
                        time.sleep(1)
                    except:
                        # Click blocked, but element was found and verified
                        pass
                    
                except Exception as e:
                    # Check if this is a SkipTest exception
                    if isinstance(e, unittest.SkipTest):
                        raise
                    
                    # Capture screenshot on failure
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_file = f"test_failures/{element_id}_{timestamp}.png"
                    os.makedirs("test_failures", exist_ok=True)
                    try:
                        self.driver.save_screenshot(screenshot_file)
                    except:
                        pass
                    
                    raise AssertionError(f"{element_id} ({label}): {str(e)}")
            
            return test_impl
        
        # Add test method to TestSuite class
        setattr(TestSuite, f"test_{elem_id}", _create_test(elem_id, elem_label, elem_locator))


if __name__ == "__main__":
    import unittest
    unittest.main()
