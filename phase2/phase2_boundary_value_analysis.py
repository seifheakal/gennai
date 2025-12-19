"""
Phase 2: Layer 2 - Boundary Value Analysis Algorithm
Generates tests by testing at domain boundaries where bugs often hide.
"""

from typing import List, Tuple, Any
from phase2_models import Element, BoundaryValue, TestStep, TestCase
from phase2_phase1_parser import Phase1Parser


class BoundaryValueAnalysis:
    """
    Boundary Value Analysis (BVA) Algorithm
    Tests values at boundaries of input domain (min, max, and just outside).
    """

    def __init__(self, parser: Phase1Parser):
        """
        Initialize with Phase 1 parser.

        Args:
            parser: Phase1Parser instance with parsed Phase 1 data
        """
        self.parser = parser

    def generate_bva_tests(self) -> List[TestCase]:
        """
        Generate tests using Boundary Value Analysis.

        Returns:
            List of TestCase objects generated from BVA algorithm
        """
        tests = []
        test_counter = 1

        for element in self.parser.get_all_elements():
            # Only generate BVA tests for constrained inputs
            if element.type != "input" or not element.constraints:
                continue

            element_tests = self._generate_boundary_tests(element, test_counter)
            tests.extend(element_tests)
            test_counter += len(element_tests)

        return tests

    def _generate_boundary_tests(
        self, element: Element, start_id: int
    ) -> List[TestCase]:
        """Generate boundary value tests for an input element"""
        tests = []

        if not element.constraints:
            return tests

        constraint = element.constraints
        boundary_values = self._get_boundary_values(constraint)

        strategy_name, locator, confidence = element.get_best_locator()

        for i, (value, boundary_type) in enumerate(boundary_values):
            test_id = f"test_{start_id + i:03d}"

            # Build step
            step = TestStep(
                step_number=1,
                action=f"Enter {boundary_type} value",
                element_id=element.element_id,
                element_label=element.label,
                element_type=element.type,
                locator=locator,
                locator_strategy=strategy_name,
                locator_confidence=confidence,
                input_value=str(value),
                validation={
                    "type": "boundary_test",
                    "expected": f"Boundary handling for {boundary_type}",
                },
            )

            # Determine expected result based on boundary type
            if boundary_type.endswith("_underflow"):
                expected = "Input rejected (below minimum)"
                priority = "high"
                risk = "high"
            elif boundary_type.endswith("_overflow"):
                expected = "Input rejected (above maximum)"
                priority = "high"
                risk = "high"
            else:
                expected = "Input accepted (at boundary)"
                priority = "medium"
                risk = "medium"

            test = TestCase(
                test_id=test_id,
                title=f"{element.label} - {boundary_type}",
                description=f"Test {element.label} with {boundary_type} value: {value}",
                priority=priority,
                algorithm_used="bva",
                elements_used=[element.element_id],
                test_steps=[step],
                expected_result=expected,
                edge_cases_covered=[boundary_type],
                coverage_contribution=0.6,
                importance_score=0.8,
                risk_level=risk,
                priority_score=0.75,
            )

            tests.append(test)

        return tests

    def _get_boundary_values(self, constraint) -> List[Tuple[Any, str]]:
        """
        Get boundary test values from constraint.

        Returns list of (value, boundary_type) tuples.
        """
        values = []

        # Length constraints (for text input)
        if constraint.min_length is not None and constraint.max_length is not None:
            # Below minimum
            if constraint.min_length > 0:
                values.append((
                    "a" * (constraint.min_length - 1),
                    "length_underflow"
                ))

            # At minimum
            values.append(("a" * constraint.min_length, "length_at_min"))

            # Just above minimum
            values.append((
                "a" * (constraint.min_length + 1),
                "length_above_min"
            ))

            # Just below maximum
            values.append((
                "a" * (constraint.max_length - 1),
                "length_below_max"
            ))

            # At maximum
            values.append(("a" * constraint.max_length, "length_at_max"))

            # Above maximum
            values.append((
                "a" * (constraint.max_length + 1),
                "length_overflow"
            ))

        # Numeric constraints
        elif constraint.min_value is not None and constraint.max_value is not None:
            # Below minimum
            values.append((constraint.min_value - 1, "value_underflow"))

            # At minimum
            values.append((constraint.min_value, "value_at_min"))

            # Just above minimum
            values.append((constraint.min_value + 1, "value_above_min"))

            # Just below maximum
            values.append((constraint.max_value - 1, "value_below_max"))

            # At maximum
            values.append((constraint.max_value, "value_at_max"))

            # Above maximum
            values.append((constraint.max_value + 1, "value_overflow"))

        # Length only
        elif constraint.max_length is not None:
            if constraint.max_length > 0:
                values.append((
                    "a" * (constraint.max_length - 1),
                    "length_below_max"
                ))
            values.append(("a" * constraint.max_length, "length_at_max"))
            values.append((
                "a" * (constraint.max_length + 1),
                "length_overflow"
            ))

        return values
