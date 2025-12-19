"""
Phase 2: Layer 3 - Coverage Calculator
Calculates element, path, scenario coverage and blends into single metric.
"""

from typing import Dict, List, Set
from phase2_models import CoverageMetrics, CoverageGap, TestCase
from phase2_phase1_parser import Phase1Parser


class CoverageCalculator:
    """
    LAYER 3: Coverage Calculation
    Calculates 3 coverage types and blends into single score.
    """

    def __init__(self, parser: Phase1Parser, tests: List[TestCase]):
        """
        Initialize with Phase 1 parser and test cases.

        Args:
            parser: Phase1Parser with parsed Phase 1 data
            tests: List of generated TestCase objects
        """
        self.parser = parser
        self.tests = tests
        self._tested_elements: Set[str] = set()
        self._tested_workflows: Set[str] = set()
        self._build_coverage_sets()

    def _build_coverage_sets(self):
        """Build sets of tested elements and workflows"""
        for test in self.tests:
            self._tested_elements.update(test.elements_used)
            
            # Workflow tests have state_combination algorithm
            if test.algorithm_used == "state_combination":
                self._tested_workflows.add(test.test_id)

    def calculate_coverage(self) -> CoverageMetrics:
        """
        Calculate all coverage metrics.

        Returns:
            CoverageMetrics with element, path, scenario, and blended coverage
        """
        element_cov = self.calculate_element_coverage()
        path_cov = self.calculate_path_coverage()
        scenario_cov = self.calculate_scenario_coverage()
        blended = self.blend_coverage(element_cov, path_cov, scenario_cov)

        # Get coverage by type
        coverage_by_type = self.get_coverage_by_element_type()

        # Identify gaps
        coverage_gaps = self.identify_coverage_gaps()

        return CoverageMetrics(
            element_coverage=element_cov,
            path_coverage=path_cov,
            scenario_coverage=scenario_cov,
            blended_coverage=blended,
            coverage_by_type=coverage_by_type,
            coverage_gaps=coverage_gaps,
            total_tests=len(self.tests),
            total_elements=len(self.parser.get_all_elements()),
            tested_elements=len(self._tested_elements),
        )

    def calculate_element_coverage(self) -> float:
        """
        Calculate element coverage percentage.

        Formula: (tested_elements / total_elements) * 100

        Returns:
            Element coverage percentage (0-100)
        """
        total_elements = len(self.parser.get_all_elements())
        if total_elements == 0:
            return 0.0

        tested_count = len(self._tested_elements)
        return (tested_count / total_elements) * 100

    def calculate_path_coverage(self) -> float:
        """
        Calculate path coverage percentage.

        Formula: (tested_workflows / total_workflows) * 100

        Returns:
            Path coverage percentage (0-100)
        """
        workflows = self.parser.get_workflows()
        total_workflows = len(workflows)

        if total_workflows == 0:
            return 0.0

        tested_count = len(self._tested_workflows)
        return (tested_count / total_workflows) * 100

    def calculate_scenario_coverage(self) -> float:
        """
        Calculate scenario coverage percentage.

        Each test covers scenarios = partitions × boundary_values
        Formula: (tested_scenarios / reachable_scenarios) * 100

        Returns:
            Scenario coverage percentage (0-100)
        """
        # Simplified: sum coverage contributions
        tested_scenarios = sum(t.coverage_contribution for t in self.tests)

        # Total scenarios = rough estimate from elements
        total_elements = len(self.parser.get_all_elements())
        # Assume ~5 scenarios per element on average
        reachable_scenarios = total_elements * 5

        if reachable_scenarios == 0:
            return 0.0

        return (tested_scenarios / reachable_scenarios) * 100

    def blend_coverage(
        self,
        element: float,
        path: float,
        scenario: float
    ) -> float:
        """
        Blend three coverage types into single score.

        Formula: 0.4×element + 0.35×path + 0.25×scenario

        Args:
            element: Element coverage %
            path: Path coverage %
            scenario: Scenario coverage %

        Returns:
            Blended coverage % (0-100)
        """
        return (0.4 * element) + (0.35 * path) + (0.25 * scenario)

    def get_coverage_by_element_type(self) -> Dict[str, float]:
        """
        Calculate coverage breakdown by element type.

        Returns:
            {element_type: coverage_percentage}
        """
        coverage_by_type = {}

        for element_type in ["button", "input", "dropdown", "link", "checkbox"]:
            elements_of_type = self.parser.get_elements_by_type(element_type)
            if not elements_of_type:
                continue

            tested = sum(
                1 for elem in elements_of_type
                if elem.element_id in self._tested_elements
            )

            total = len(elements_of_type)
            coverage_by_type[element_type] = (tested / total * 100) if total > 0 else 0.0

        return coverage_by_type

    def identify_coverage_gaps(self) -> List[CoverageGap]:
        """
        Identify elements that are NOT covered by tests.

        Returns:
            List of CoverageGap objects for uncovered elements
        """
        gaps = []
        all_elements = self.parser.get_all_elements()

        for elem in all_elements:
            if elem.element_id not in self._tested_elements:
                _, conf = elem.locator_confidence.best_strategy()
                
                # Determine recommendation based on confidence
                if conf is not None and conf < 0.70:
                    reason = f"Low confidence ({conf:.0%}), deferred to Phase 3"
                    recommendation = "Validate element exists, then add 3-5 tests"
                else:
                    reason = "Not covered by generated tests"
                    recommendation = "Add manual tests or adjust test selection"

                gap = CoverageGap(
                    element_id=elem.element_id,
                    element_label=elem.label,
                    element_type=elem.type,
                    element_confidence=conf if conf is not None else 0.0,
                    reason=reason,
                    recommendation=recommendation,
                )
                gaps.append(gap)

        return gaps

    def get_coverage_summary(self) -> Dict:
        """
        Get summary of coverage metrics.

        Returns:
            Dictionary with key coverage statistics
        """
        coverage = self.calculate_coverage()

        return {
            "total_elements": coverage.total_elements,
            "tested_elements": coverage.tested_elements,
            "element_coverage": f"{coverage.element_coverage:.1f}%",
            "path_coverage": f"{coverage.path_coverage:.1f}%",
            "scenario_coverage": f"{coverage.scenario_coverage:.1f}%",
            "blended_coverage": f"{coverage.blended_coverage:.1f}%",
            "coverage_target_met": coverage.blended_coverage >= 85.0,
            "coverage_gaps_count": len(coverage.coverage_gaps),
        }

    def is_coverage_sufficient(self, target: float = 85.0) -> bool:
        """
        Check if coverage meets target threshold.

        Args:
            target: Target coverage percentage (default: 85.0)

        Returns:
            True if blended coverage >= target
        """
        coverage = self.calculate_coverage()
        return coverage.blended_coverage >= target
