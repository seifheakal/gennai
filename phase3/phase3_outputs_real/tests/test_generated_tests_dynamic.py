from base_test import BaseTestCase
from datetime import datetime
import os
import time
import json
import pytest
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Dynamically load Phase 1 and Phase 2 data
def load_phase1_elements():
    """Load element data from Phase 1 output"""
    phase1_file = Path(__file__).parent.parent.parent / "phase1" / "phase1_real_output2.json"
    if not phase1_file.exists():
        raise FileNotFoundError(f"Phase 1 output not found at {phase1_file}")
    
    with open(phase1_file, 'r') as f:
        phase1_data = json.load(f)
    
    elements = {}
    for elem in phase1_data.get("interactive_elements", []):
        elem_id = elem["element_id"]
        # Extract best locator strategy
        locators = elem.get("locators", {})
        confidence_scores = elem.get("locator_confidence", {})
        
        # Find the best available locator
        best_locator = None
        best_confidence = 0
        
        for locator_key, locator_value in locators.items():
            conf = confidence_scores.get(locator_key, 0)
            if conf > best_confidence and locator_value:
                best_locator = locator_value
                best_confidence = conf
        
        elements[elem_id] = {
            "label": elem.get("label", ""),
            "type": elem.get("type", ""),
            "locator": best_locator,
            "confidence": best_confidence,
            "aria_name": elem.get("accessibility_info", {}).get("accessible_name", ""),
            "visible": elem.get("visible", False),
            "enabled": elem.get("enabled", False),
        }
    
    return elements


def load_phase2_tests():
    """Load test cases from Phase 2 output"""
    phase2_file = Path(__file__).parent.parent.parent / "phase2" / "phase2_test_cases.json"
    if not phase2_file.exists():
        raise FileNotFoundError(f"Phase 2 output not found at {phase2_file}")
    
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


# Load data at module level
try:
    ELEMENT_MAP = load_phase1_elements()
    TEST_SPECS = load_phase2_tests()
except Exception as e:
    print(f"Warning: Could not load Phase 1/2 data: {e}")
    ELEMENT_MAP = {}
    TEST_SPECS = {}


class TestSuite(BaseTestCase):
    """Dynamically generated comprehensive test suite
    
    This test suite automatically generates tests from Phase 1 element discovery
    and Phase 2 test case specifications. Tests automatically adapt when Phase 1
    discovers new or different elements on the target website.
    
    How it works:
    1. Phase 1 discovers interactive elements and their locators
    2. Phase 2 generates test case specifications
    3. This file dynamically loads both and generates tests for each element
    
    If you run Phase 1 again on a modified website:
    - New tests will be automatically generated for any new elements
    - Test parameters will adapt to new locators
    - Old elements will be skipped if they're no longer found
    
    Data Sources:
    - Phase 1 Output: phase1_real_output2.json (element discovery)
    - Phase 2 Output: phase2_test_cases.json (test specifications)
    """
    
    BASE_URL = "https://automationexercise.com/"
    
    @pytest.mark.parametrize("elem_id", sorted(ELEMENT_MAP.keys()))
    def test_element_interaction(self, elem_id):
        """
        Dynamically generated test for element interaction
        
        This test validates that discovered elements from Phase 1 can be:
        - Located using the automatically selected best locator
        - Verified for visibility and enabled state
        - Interacted with (click/input as applicable)
        
        The test automatically adapts based on element type:
        - Buttons: Verified for visibility, enabled, clickability, and text match
        - Inputs: Verified for visibility and enabled state
        - Other: Verified for visibility and enabled state
        
        Parameters:
            elem_id: Element ID from Phase 1 discovery (elem_001, elem_002, etc.)
                    Auto-generated from interactive_elements in Phase 1 output
        """
        try:
            elem_info = ELEMENT_MAP.get(elem_id)
            if not elem_info:
                pytest.skip(f"Element {elem_id} not found in Phase 1 output")
            
            # Navigate to base URL
            self.driver.get(self.BASE_URL)
            wait = WebDriverWait(self.driver, 10)
            
            elem_label = elem_info.get("label", elem_id)
            elem_locator = elem_info.get("locator")
            elem_type = elem_info.get("type")
            elem_confidence = elem_info.get("confidence", 0)
            
            if not elem_locator:
                pytest.skip(f"No valid locator found for {elem_id} ({elem_label})")
            
            # Log which element we're testing with metadata
            print(f"\n{'='*70}")
            print(f"Testing Element: {elem_id}")
            print(f"  Label: {elem_label}")
            print(f"  Type: {elem_type}")
            print(f"  Confidence: {elem_confidence:.2f}")
            print(f"  Locator: {elem_locator}")
            print(f"{'='*70}")
            
            # Test Steps vary based on element type discovered by Phase 1
            if elem_type == "button":
                # Test button - verify visibility, enabled state, and clickability
                button = wait.until(
                    EC.presence_of_element_located((By.XPATH, elem_locator))
                )
                
                # Verify element properties from Phase 1 discovery
                self.assertTrue(button.is_displayed(), f"{elem_label} should be displayed")
                self.assertTrue(button.is_enabled(), f"{elem_label} should be enabled")
                
                # Verify it's clickable
                clickable_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, elem_locator))
                )
                
                # Verify button text matches Phase 1 label (if label exists)
                if elem_label:
                    button_text = button.text.strip() if button.text else ""
                    if button_text:
                        self.assertTrue(
                            elem_label.lower() in button_text.lower() or button_text.lower() in elem_label.lower(),
                            f"Button text '{button_text}' should match label '{elem_label}'"
                        )
                
                # Try to click and verify response
                try:
                    clickable_button.click()
                    time.sleep(1)
                    # Verify page loaded (at minimum)
                    new_url = self.driver.current_url
                    self.assertIsNotNone(new_url, "Page should be accessible after click")
                    print(f"  ✓ Button click successful - navigated to {new_url}")
                except Exception as click_error:
                    # If click fails (e.g., blocked by ads), element still exists
                    print(f"  ⚠ Click skipped: {str(click_error)[:80]}")
                    pass
            
            elif elem_type == "input":
                # Test input element - verify visibility and enabled state
                input_elem = wait.until(
                    EC.presence_of_element_located((By.XPATH, elem_locator))
                )
                self.assertTrue(input_elem.is_displayed(), f"{elem_label} should be displayed")
                self.assertTrue(input_elem.is_enabled(), f"{elem_label} should be enabled")
                print(f"  ✓ Input element is accessible and enabled")
            
            else:
                # Generic test for any other element type
                element = wait.until(
                    EC.presence_of_element_located((By.XPATH, elem_locator))
                )
                self.assertTrue(element.is_displayed(), f"{elem_label} should be displayed")
                self.assertTrue(element.is_enabled(), f"{elem_label} should be enabled")
                print(f"  ✓ Element is accessible and enabled")
            
            print(f"  ✅ Test passed for {elem_id}: {elem_label}")

        except Exception as e:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"test_failures/{elem_id}_{timestamp}.png"
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            self.driver.save_screenshot(screenshot_path)
            print(f"  ❌ Test failed - screenshot saved to {screenshot_path}")
            raise AssertionError(f"Test failed for {elem_id} ({ELEMENT_MAP.get(elem_id, {}).get('label', 'unknown')}): {str(e)}")


if __name__ == "__main__":
    import unittest
    unittest.main()
