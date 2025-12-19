"""
Phase 2: Layer 2 - Equivalence Partitioning Algorithm
Generates tests by partitioning input domains into equivalence classes.
"""

from typing import List, Tuple, Optional
from phase2_models import Element, Partition, TestStep, TestCase
from phase2_phase1_parser import Phase1Parser


class EquivalencePartitioning:
    """
    Equivalence Partitioning (EP) Algorithm
    Partitions input domain into equivalence classes where all values behave similarly.
    """

    def __init__(self, parser: Phase1Parser):
        """
        Initialize with Phase 1 parser.

        Args:
            parser: Phase1Parser instance with parsed Phase 1 data
        """
        self.parser = parser

    def generate_ep_tests(self) -> List[TestCase]:
        """
        Generate tests using Equivalence Partitioning.

        Returns:
            List of TestCase objects generated from EP algorithm
        """
        tests = []
        test_counter = 1

        for element in self.parser.get_all_elements():
            # Skip elements without interaction type or constraints
            if not element.interaction_type:
                continue

            # Generate EP tests based on element type
            if element.type == "input":
                element_tests = self._generate_input_ep_tests(element, test_counter)
            elif element.type == "button":
                element_tests = self._generate_button_ep_tests(element, test_counter)
            elif element.type == "dropdown":
                element_tests = self._generate_dropdown_ep_tests(element, test_counter)
            elif element.type == "checkbox":
                element_tests = self._generate_checkbox_ep_tests(element, test_counter)
            else:
                element_tests = self._generate_generic_ep_tests(element, test_counter)

            tests.extend(element_tests)
            test_counter += len(element_tests)

        return tests

    def _generate_input_ep_tests(
        self, element: Element, start_id: int
    ) -> List[TestCase]:
        """Generate EP tests for text input"""
        tests = []
        partitions = self._partition_text_input(element)

        for i, partition in enumerate(partitions):
            test_id = f"test_{start_id + i:03d}"

            # Build test step
            strategy_name, locator, confidence = element.get_best_locator()

            step = TestStep(
                step_number=1,
                action=f"Enter {partition.name} value",
                element_id=element.element_id,
                element_label=element.label,
                element_type=element.type,
                locator=locator,
                locator_strategy=strategy_name,
                locator_confidence=confidence,
                input_value=partition.representative,
                validation={
                    "type": "input_acceptance",
                    "expected": partition.expected_behavior,
                },
            )

            test = TestCase(
                test_id=test_id,
                title=f"{element.label} - {partition.name}",
                description=f"Test {element.label} with {partition.name} input: {partition.description}",
                priority="medium",
                algorithm_used="ep",
                elements_used=[element.element_id],
                test_steps=[step],
                expected_result=partition.expected_behavior,
                edge_cases_covered=[partition.name],
                coverage_contribution=0.8,
                importance_score=0.7,
                risk_level="low",
                priority_score=0.7,
            )

            tests.append(test)

        return tests

    def _generate_button_ep_tests(
        self, element: Element, start_id: int
    ) -> List[TestCase]:
        """Generate EP tests for buttons"""
        tests = []

        # Partition button states: enabled, disabled
        strategy_name, locator, confidence = element.get_best_locator()

        # Test 1: Button enabled
        step_enabled = TestStep(
            step_number=1,
            action=f"Click {element.label}",
            element_id=element.element_id,
            element_label=element.label,
            element_type=element.type,
            locator=locator,
            locator_strategy=strategy_name,
            locator_confidence=confidence,
            validation={"type": "element_state", "expected": "Button is enabled"},
        )

        test_enabled = TestCase(
            test_id=f"test_{start_id:03d}",
            title=f"{element.label} - enabled state",
            description=f"Verify {element.label} is enabled and clickable",
            priority="high",
            algorithm_used="ep",
            elements_used=[element.element_id],
            test_steps=[step_enabled],
            expected_result="Button responds to click",
            edge_cases_covered=["enabled"],
            coverage_contribution=1.0,
            importance_score=0.9,
            risk_level="medium",
            priority_score=0.85,
        )
        tests.append(test_enabled)

        # Test 2: Button disabled (if applicable)
        if "disabled" in (element.states or []):
            step_disabled = TestStep(
                step_number=1,
                action=f"Try to click {element.label}",
                element_id=element.element_id,
                element_label=element.label,
                element_type=element.type,
                locator=locator,
                locator_strategy=strategy_name,
                locator_confidence=confidence,
                validation={
                    "type": "element_state",
                    "expected": "Button is disabled",
                },
            )

            test_disabled = TestCase(
                test_id=f"test_{start_id + 1:03d}",
                title=f"{element.label} - disabled state",
                description=f"Verify {element.label} is disabled and not clickable",
                priority="medium",
                algorithm_used="ep",
                elements_used=[element.element_id],
                test_steps=[step_disabled],
                expected_result="Button does not respond",
                edge_cases_covered=["disabled"],
                coverage_contribution=0.8,
                importance_score=0.6,
                risk_level="low",
                priority_score=0.6,
            )
            tests.append(test_disabled)

        return tests

    def _generate_dropdown_ep_tests(
        self, element: Element, start_id: int
    ) -> List[TestCase]:
        """Generate EP tests for dropdowns"""
        tests = []
        strategy_name, locator, confidence = element.get_best_locator()

        # Test valid options
        if element.valid_values:
            for i, value in enumerate(element.valid_values[:3]):  # Limit to 3
                step = TestStep(
                    step_number=1,
                    action=f"Select {value}",
                    element_id=element.element_id,
                    element_label=element.label,
                    element_type=element.type,
                    locator=locator,
                    locator_strategy=strategy_name,
                    locator_confidence=confidence,
                    input_value=value,
                    validation={
                        "type": "selection",
                        "expected": f"{value} is selected",
                    },
                )

                test = TestCase(
                    test_id=f"test_{start_id + i:03d}",
                    title=f"{element.label} - select {value}",
                    description=f"Test selecting {value} from {element.label}",
                    priority="medium",
                    algorithm_used="ep",
                    elements_used=[element.element_id],
                    test_steps=[step],
                    expected_result=f"{value} is selected",
                    edge_cases_covered=["valid_option"],
                    coverage_contribution=0.7,
                    importance_score=0.7,
                    risk_level="low",
                    priority_score=0.7,
                )
                tests.append(test)

        return tests

    def _generate_checkbox_ep_tests(
        self, element: Element, start_id: int
    ) -> List[TestCase]:
        """Generate EP tests for checkboxes"""
        tests = []
        strategy_name, locator, confidence = element.get_best_locator()

        # Test 1: Unchecked state
        step_unchecked = TestStep(
            step_number=1,
            action=f"Verify {element.label} is unchecked",
            element_id=element.element_id,
            element_label=element.label,
            element_type=element.type,
            locator=locator,
            locator_strategy=strategy_name,
            locator_confidence=confidence,
            validation={"type": "element_state", "expected": "Checkbox is unchecked"},
        )

        test_unchecked = TestCase(
            test_id=f"test_{start_id:03d}",
            title=f"{element.label} - unchecked",
            description=f"Verify {element.label} is initially unchecked",
            priority="low",
            algorithm_used="ep",
            elements_used=[element.element_id],
            test_steps=[step_unchecked],
            expected_result="Checkbox unchecked",
            edge_cases_covered=["unchecked"],
            coverage_contribution=0.5,
            importance_score=0.6,
            risk_level="low",
            priority_score=0.5,
        )
        tests.append(test_unchecked)

        # Test 2: Checked state
        step_checked = TestStep(
            step_number=1,
            action=f"Check {element.label}",
            element_id=element.element_id,
            element_label=element.label,
            element_type=element.type,
            locator=locator,
            locator_strategy=strategy_name,
            locator_confidence=confidence,
            validation={"type": "element_state", "expected": "Checkbox is checked"},
        )

        test_checked = TestCase(
            test_id=f"test_{start_id + 1:03d}",
            title=f"{element.label} - checked",
            description=f"Verify {element.label} can be checked",
            priority="low",
            algorithm_used="ep",
            elements_used=[element.element_id],
            test_steps=[step_checked],
            expected_result="Checkbox checked",
            edge_cases_covered=["checked"],
            coverage_contribution=0.5,
            importance_score=0.6,
            risk_level="low",
            priority_score=0.5,
        )
        tests.append(test_checked)

        return tests

    def _generate_generic_ep_tests(
        self, element: Element, start_id: int
    ) -> List[TestCase]:
        """Generate generic EP tests for unknown types"""
        tests = []
        strategy_name, locator, confidence = element.get_best_locator()

        step = TestStep(
            step_number=1,
            action=f"Interact with {element.label}",
            element_id=element.element_id,
            element_label=element.label,
            element_type=element.type,
            locator=locator,
            locator_strategy=strategy_name,
            locator_confidence=confidence,
            validation={"type": "element_exists", "expected": "Element is interactive"},
        )

        test = TestCase(
            test_id=f"test_{start_id:03d}",
            title=f"{element.label} - basic interaction",
            description=f"Verify {element.label} is interactive",
            priority="low",
            algorithm_used="ep",
            elements_used=[element.element_id],
            test_steps=[step],
            expected_result="Element responds",
            edge_cases_covered=["interaction"],
            coverage_contribution=0.5,
            importance_score=0.5,
            risk_level="low",
            priority_score=0.5,
        )
        tests.append(test)

        return tests

    def _partition_text_input(self, element: Element) -> List[Partition]:
        """
        Partition text input into equivalence classes.

        Returns: [valid_partition, invalid_partition, boundary_partition]
        """
        partitions = []

        # Valid partition
        if element.valid_values:
            partitions.append(
                Partition(
                    name="valid",
                    representative=element.valid_values[0],
                    expected_behavior="Input accepted",
                    description=f"Valid format: {element.valid_values[0]}",
                )
            )
        else:
            partitions.append(
                Partition(
                    name="valid",
                    representative="testvalue",
                    expected_behavior="Input accepted",
                    description="Standard valid input",
                )
            )

        # Invalid partition
        if element.invalid_values:
            partitions.append(
                Partition(
                    name="invalid",
                    representative=element.invalid_values[0],
                    expected_behavior="Input rejected or error shown",
                    description=f"Invalid format: {element.invalid_values[0]}",
                )
            )
        else:
            partitions.append(
                Partition(
                    name="invalid",
                    representative="!!!invalid!!!",
                    expected_behavior="Input rejected",
                    description="Invalid special characters",
                )
            )

        # Boundary partition (length constraints)
        if element.constraints and element.constraints.max_length:
            partitions.append(
                Partition(
                    name="boundary",
                    representative="a" * element.constraints.max_length,
                    expected_behavior="Input accepted at maximum length",
                    description=f"At max length: {element.constraints.max_length}",
                )
            )

        return partitions
