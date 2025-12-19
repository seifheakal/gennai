"""
Phase 2: Validators & Hallucination Detection
Ensures 0% hallucinated tests - all elements traceable to Phase 1
"""

from typing import List, Set, Tuple
from phase2_models import (
    TestCase,
    Element,
    Phase1Output,
    TestStep,
)


class HallucinationDetector:
    """
    Detects hallucinated tests - ensures all elements & locators exist in Phase 1.
    This is CRITICAL for preventing false positives in test generation.
    """

    def __init__(self, phase1_output: Phase1Output):
        """
        Initialize with Phase 1 data for validation.

        Args:
            phase1_output: Parsed Phase 1 output containing all discovered elements
        """
        self.phase1_output = phase1_output
        self._build_element_index()

    def _build_element_index(self):
        """Build fast lookup indices for validation"""
        self.element_map: dict = {
            elem.element_id: elem for elem in self.phase1_output.interactive_elements
        }
        self.all_element_ids: Set[str] = set(self.element_map.keys())

    def validate_test(self, test: TestCase) -> Tuple[bool, List[str]]:
        """
        Validate a test case for hallucinations.

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        # Check 1: All element_ids exist
        for step in test.test_steps:
            if step.element_id not in self.all_element_ids:
                errors.append(
                    f"Step {step.step_number}: "
                    f"Element '{step.element_id}' not found in Phase 1"
                )

        # Check 2: All locators are valid
        for step in test.test_steps:
            locator_valid, locator_error = self._validate_locator(step)
            if not locator_valid:
                errors.append(f"Step {step.step_number}: {locator_error}")

        # Check 3: Confidence scores are valid
        for step in test.test_steps:
            if not (0.0 <= step.locator_confidence <= 1.0):
                errors.append(
                    f"Step {step.step_number}: "
                    f"Invalid confidence {step.locator_confidence} (must be 0-1)"
                )

        # Check 4: Element types match Phase 1
        for step in test.test_steps:
            if step.element_id in self.element_map:
                phase1_elem = self.element_map[step.element_id]
                if step.element_type != phase1_elem.type:
                    errors.append(
                        f"Step {step.step_number}: "
                        f"Type mismatch - Phase 1 has '{phase1_elem.type}', "
                        f"test has '{step.element_type}'"
                    )

        return (len(errors) == 0, errors)

    def _validate_locator(self, step: TestStep) -> Tuple[bool, str]:
        """
        Validate that locator exists in Phase 1 for this element.

        Returns:
            (is_valid, error_message)
        """
        if step.element_id not in self.element_map:
            return (False, f"Element {step.element_id} not found in Phase 1")

        element = self.element_map[step.element_id]

        # Get all valid locators for this element
        valid_locators = {
            element.locators.p1_role,
            element.locators.p2_label,
            element.locators.p3_testid,
            element.locators.p4_css,
            element.locators.p5_xpath,
        }
        valid_locators.discard(None)  # Remove None values

        if step.locator not in valid_locators:
            return (
                False,
                f"Locator '{step.locator}' not found in Phase 1 "
                f"(valid: {valid_locators})",
            )

        return (True, "")

    def validate_test_batch(self, tests: List[TestCase]) -> dict:
        """
        Validate batch of tests.

        Returns:
            {
                "total_tests": int,
                "valid_tests": int,
                "invalid_tests": int,
                "errors_by_test": {test_id: [errors]},
                "hallucination_rate": float
            }
        """
        results = {
            "total_tests": len(tests),
            "valid_tests": 0,
            "invalid_tests": 0,
            "errors_by_test": {},
            "hallucination_rate": 0.0,
        }

        for test in tests:
            is_valid, errors = self.validate_test(test)
            if is_valid:
                results["valid_tests"] += 1
            else:
                results["invalid_tests"] += 1
                results["errors_by_test"][test.test_id] = errors

        if results["total_tests"] > 0:
            results["hallucination_rate"] = (
                results["invalid_tests"] / results["total_tests"]
            )

        return results

    def get_phase1_element_map(self) -> dict:
        """
        Get map of all Phase 1 elements for test generation reference.

        Returns:
            {element_id: Element}
        """
        return self.element_map

    def get_all_element_ids(self) -> Set[str]:
        """Get all valid element IDs from Phase 1"""
        return self.all_element_ids

    def get_elements_by_type(self, element_type: str) -> List[Element]:
        """Get all elements of a specific type from Phase 1"""
        return [
            elem
            for elem in self.phase1_output.interactive_elements
            if elem.type == element_type
        ]

    def get_element_confidence(self, element_id: str) -> float:
        """Get best locator confidence for an element"""
        if element_id not in self.element_map:
            return 0.0
        element = self.element_map[element_id]
        _, confidence = element.locator_confidence.best_strategy()
        return confidence if confidence is not None else 0.0


class ValidationError(Exception):
    """Raised when validation fails"""

    pass


class HallucinationError(ValidationError):
    """Raised when hallucination is detected"""

    pass
