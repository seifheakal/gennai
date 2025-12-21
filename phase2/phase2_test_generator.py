"""
Phase 2: Layer 2 - State Combination & Test Generator Orchestrator
Combines all algorithms and selects best tests for 85%+ coverage.
"""

from typing import List, Dict, Set, Tuple
from datetime import datetime
from phase2_models import TestCase, Phase1Output
from phase2_phase1_parser import Phase1Parser
from phase2_equivalence_partitioning import EquivalencePartitioning
from phase2_boundary_value_analysis import BoundaryValueAnalysis
from phase2_validators import HallucinationDetector


class StateCombinationTesting:
    """
    State Combination Testing
    Generates tests by following user workflows from Phase 1 state graph.
    """

    def __init__(self, parser: Phase1Parser):
        """Initialize with Phase 1 parser"""
        self.parser = parser

    def generate_state_tests(self) -> List[TestCase]:
        """
        Generate tests from workflows (state transitions).

        Returns:
            List of TestCase objects for workflows
        """
        tests = []
        test_counter = 1

        for workflow in self.parser.get_workflows():
            test = self._generate_workflow_test(workflow, test_counter)
            if test:
                tests.append(test)
                test_counter += 1

        return tests

    def _generate_workflow_test(self, workflow, test_id_num: int) -> TestCase:
        """Generate single workflow test from Phase 1 workflow"""
        workflow_steps = []

        for step_num, element_id in enumerate(workflow.steps, 1):
            element = self.parser.get_element_by_id(element_id)
            if not element:
                continue

            strategy_name, locator, confidence = element.get_best_locator()

            # Determine action based on element type
            if element.type == "input":
                action = f"Enter data in {element.label}"
                input_value = element.valid_values[0] if element.valid_values else "test"
            elif element.type == "button":
                action = f"Click {element.label}"
                input_value = None
            elif element.type == "dropdown":
                action = f"Select from {element.label}"
                input_value = element.valid_values[0] if element.valid_values else "option1"
            else:
                action = f"Interact with {element.label}"
                input_value = None

            step = TestCase.model_validate({
                "test_id": "temp",
                "title": "temp",
                "description": "temp",
                "priority": "high",
                "algorithm_used": "state",
                "elements_used": [element_id],
                "test_steps": [{
                    "step_number": step_num,
                    "action": action,
                    "element_id": element_id,
                    "element_label": element.label,
                    "element_type": element.type,
                    "locator": locator,
                    "locator_strategy": strategy_name,
                    "locator_confidence": confidence,
                    "input_value": input_value,
                    "validation": {"type": "step_execution", "expected": "Step executes"}
                }],
                "expected_result": "Step completes",
                "edge_cases_covered": [],
                "coverage_contribution": 0.0,
                "importance_score": 0.0,
                "risk_level": "medium",
                "priority_score": 0.0
            })

            workflow_steps.append(step.test_steps[0])

        if not workflow_steps:
            return None

        # Build complete workflow test
        all_element_ids = [step.element_id for step in workflow_steps]

        test = TestCase(
            test_id=f"test_{test_id_num:03d}",
            title=f"Workflow: {workflow.name}",
            description=f"Test complete workflow: {workflow.description or workflow.name}",
            priority="high",
            algorithm_used="state_combination",
            elements_used=all_element_ids,
            test_steps=workflow_steps,
            expected_result=f"Workflow '{workflow.name}' completes successfully",
            edge_cases_covered=["workflow", "integration"],
            coverage_contribution=min(2.0, len(all_element_ids) * 0.5),
            importance_score=0.9,
            risk_level="medium",
            priority_score=0.85,
        )

        return test


class TestGenerator:
    """
    LAYER 2 ORCHESTRATOR
    Combines EP + BVA + State algorithms and selects best tests.
    """

    def __init__(self, parser: Phase1Parser):
        """Initialize with Phase 1 parser"""
        self.parser = parser
        self.detector = HallucinationDetector(parser.phase1_output)
        self.ep = EquivalencePartitioning(parser)
        self.bva = BoundaryValueAnalysis(parser)
        self.state = StateCombinationTesting(parser)

    def generate_tests(
        self,
        target_coverage: float = 85.0,
        max_tests: int = 100,
        min_tests: int = 50,
    ) -> List[TestCase]:
        """
        Generate intelligent test cases.

        Algorithm:
        1. Generate candidates from all algorithms
        2. Calculate priority for each test
        3. Greedy selection until 85%+ coverage OR min_tests reached
        4. Validate all tests (no hallucinations)

        Args:
            target_coverage: Target blended coverage %
            max_tests: Maximum tests to generate
            min_tests: Minimum tests to include

        Returns:
            List of selected TestCase objects
        """
        print("[WRENCH] Generating candidate tests...")

        # Step 1: Generate candidates
        ep_tests = self.ep.generate_ep_tests()
        bva_tests = self.bva.generate_bva_tests()
        state_tests = self.state.generate_state_tests()

        all_candidates = ep_tests + bva_tests + state_tests
        print(f"  EP tests: {len(ep_tests)}")
        print(f"  BVA tests: {len(bva_tests)}")
        print(f"  State tests: {len(state_tests)}")
        print(f"  Total candidates: {len(all_candidates)}")

        # Step 2: Calculate priority scores
        self._calculate_priority_scores(all_candidates)

        # Step 3: Sort by priority
        all_candidates.sort(key=lambda t: t.priority_score, reverse=True)

        # Step 4: Greedy selection
        selected_tests = []
        covered_elements: Set[str] = set()

        for test in all_candidates:
            if len(selected_tests) >= max_tests:
                break

            # Add test
            selected_tests.append(test)
            covered_elements.update(test.elements_used)

            # Check if we've reached target
            if len(selected_tests) >= min_tests:
                coverage = self._calculate_coverage(covered_elements)
                if coverage >= target_coverage:
                    break

        print(f"  Selected: {len(selected_tests)} tests")

        # Step 5: Validate (zero hallucinations)
        print("[SEARCH] Validating tests...")
        validation_result = self.detector.validate_test_batch(selected_tests)
        print(f"  Valid: {validation_result['valid_tests']}")
        print(f"  Hallucinations: {validation_result['invalid_tests']}")

        if validation_result["hallucination_rate"] > 0:
            print("  [WARN]  Found hallucinated tests, removing...")
            selected_tests = [
                t for t in selected_tests
                if t.test_id not in validation_result["errors_by_test"]
            ]

        return selected_tests

    def _calculate_priority_scores(self, tests: List[TestCase]):
        """
        Calculate priority score for each test using weighted formula:
        priority = 0.3×confidence + 0.3×coverage_gap + 0.2×risk + 0.2×complexity
        """
        total_elements = len(self.parser.get_all_elements())

        for test in tests:
            # Get average confidence for test elements
            confidence_scores = [
                self.detector.get_element_confidence(elem_id)
                for elem_id in test.elements_used
            ]
            avg_confidence = (
                sum(confidence_scores) / len(confidence_scores)
                if confidence_scores
                else 0.5
            )

            # Coverage gap (how many elements in test are not yet represented)
            coverage_gap = len(test.elements_used) / total_elements if total_elements > 0 else 0.1

            # Risk level mapping
            risk_map = {"low": 0.3, "medium": 0.6, "high": 0.9}
            risk_score = risk_map.get(test.risk_level, 0.5)

            # Complexity (based on number of steps)
            complexity = min(1.0, len(test.test_steps) / 5)

            # Weighted formula
            test.priority_score = (
                0.3 * avg_confidence +
                0.3 * coverage_gap +
                0.2 * risk_score +
                0.2 * complexity
            )

    def _calculate_coverage(self, tested_elements: Set[str]) -> float:
        """Calculate simple element coverage percentage"""
        total = len(self.parser.get_all_elements())
        if total == 0:
            return 0.0
        return (len(tested_elements) / total) * 100

    def get_algorithm_stats(self, tests: List[TestCase]) -> Dict:
        """Get statistics about test generation"""
        ep_count = sum(1 for t in tests if t.algorithm_used == "ep")
        bva_count = sum(1 for t in tests if t.algorithm_used == "bva")
        state_count = sum(1 for t in tests if t.algorithm_used == "state_combination")

        return {
            "total_tests": len(tests),
            "ep_tests": ep_count,
            "bva_tests": bva_count,
            "state_tests": state_count,
            "ep_percentage": (ep_count / len(tests) * 100) if tests else 0,
            "bva_percentage": (bva_count / len(tests) * 100) if tests else 0,
            "state_percentage": (state_count / len(tests) * 100) if tests else 0,
        }
