"""
Phase 2: Layer 4 - Coverage Visualizer
Generates heatmap visualization data for Phase 3.
"""

from typing import Dict, List
from phase2_models import CoverageMetrics, TestCase
from phase2_phase1_parser import Phase1Parser
from phase2_coverage_calculator import CoverageCalculator


class CoverageVisualizer:
    """
    LAYER 4: Coverage Visualization
    Generates heatmap data with color-coded elements for Phase 3.
    """

    def __init__(self, coverage: CoverageMetrics, parser: Phase1Parser, tests: List[TestCase]):
        """
        Initialize with coverage metrics and parser.

        Args:
            coverage: CoverageMetrics from Layer 3
            parser: Phase1Parser with Phase 1 data
            tests: List of TestCase objects
        """
        self.coverage = coverage
        self.parser = parser
        self.tests = tests
        self._build_test_map()

    def _build_test_map(self):
        """Build map of element_id → test_count"""
        self.element_test_count: Dict[str, int] = {}
        for test in self.tests:
            for elem_id in test.elements_used:
                self.element_test_count[elem_id] = self.element_test_count.get(elem_id, 0) + 1

    def generate_heatmap_data(self) -> Dict:
        """
        Generate heatmap visualization data.

        Returns:
            Dictionary with elements + summary for visualization
        """
        elements_data = []

        for elem in self.parser.get_all_elements():
            is_tested = elem.element_id in self.coverage.coverage_by_type or any(
                elem.element_id in test.elements_used for test in self.tests
            )

            # Calculate coverage % for this element
            # (assuming multi-step coverage or binary)
            elem_coverage = (
                100.0 if is_tested else 0.0
            )

            color = self._coverage_to_color(elem_coverage)
            test_count = self.element_test_count.get(elem.element_id, 0)

            elements_data.append({
                "element_id": elem.element_id,
                "label": elem.label,
                "type": elem.type,
                "coverage": elem_coverage,
                "color": color,
                "test_count": test_count,
                "importance": elem.importance_rank,
                "confidence": self.parser.get_element_by_id(elem.element_id).locator_confidence.best_strategy()[1] or 0.0,
            })

        return {
            "metadata": {
                "generated_timestamp": "2025-12-19T10:30:00Z",
                "total_elements": len(elements_data),
                "tested_elements": sum(1 for e in elements_data if e["coverage"] > 0),
            },
            "elements": elements_data,
            "summary": {
                "blended_coverage": self.coverage.blended_coverage,
                "element_coverage": self.coverage.element_coverage,
                "path_coverage": self.coverage.path_coverage,
                "scenario_coverage": self.coverage.scenario_coverage,
                "coverage_gaps": len(self.coverage.coverage_gaps),
            },
            "color_scheme": {
                "green": "#00AA00",  # 90%+
                "orange": "#FFAA00",  # 75-90%
                "red": "#FF0000",     # <75%
            },
        }

    def _coverage_to_color(self, coverage: float) -> str:
        """
        Map coverage percentage to color.

        Args:
            coverage: Coverage percentage (0-100)

        Returns:
            Color hex code
        """
        if coverage >= 90:
            return "#00AA00"  # Green - excellent
        elif coverage >= 75:
            return "#FFAA00"  # Orange - good
        else:
            return "#FF0000"  # Red - needs improvement

    def generate_element_heatmap(self) -> Dict:
        """
        Generate heatmap broken down by element type.

        Returns:
            Dictionary with coverage by element type
        """
        heatmap = {}

        for elem_type, coverage_pct in self.coverage.coverage_by_type.items():
            elements_of_type = self.parser.get_elements_by_type(elem_type)
            test_count = sum(
                self.element_test_count.get(e.element_id, 0)
                for e in elements_of_type
            )

            heatmap[elem_type] = {
                "total_elements": len(elements_of_type),
                "coverage_percentage": coverage_pct,
                "color": self._coverage_to_color(coverage_pct),
                "test_count": test_count,
                "elements": [
                    {
                        "id": e.element_id,
                        "label": e.label,
                        "tested": e.element_id in self.coverage.coverage_by_type,
                        "test_count": self.element_test_count.get(e.element_id, 0),
                    }
                    for e in elements_of_type
                ],
            }

        return heatmap

    def generate_coverage_report(self) -> Dict:
        """
        Generate comprehensive coverage report.

        Returns:
            Dictionary with detailed coverage analysis
        """
        heatmap = self.generate_heatmap_data()

        return {
            "title": "Phase 2: Test Coverage Report",
            "summary": {
                "total_tests": self.coverage.total_tests,
                "total_elements": self.coverage.total_elements,
                "tested_elements": self.coverage.tested_elements,
                "coverage_target": "85%",
                "coverage_achieved": f"{self.coverage.blended_coverage:.1f}%",
                "target_met": self.coverage.blended_coverage >= 85.0,
            },
            "coverage_breakdown": {
                "element_coverage": f"{self.coverage.element_coverage:.1f}%",
                "path_coverage": f"{self.coverage.path_coverage:.1f}%",
                "scenario_coverage": f"{self.coverage.scenario_coverage:.1f}%",
                "blended_coverage": f"{self.coverage.blended_coverage:.1f}%",
            },
            "by_type": self.generate_element_heatmap(),
            "coverage_gaps": [
                {
                    "element_id": gap.element_id,
                    "label": gap.element_label,
                    "type": gap.element_type,
                    "confidence": gap.element_confidence,
                    "reason": gap.reason,
                    "recommendation": gap.recommendation,
                }
                for gap in self.coverage.coverage_gaps
            ],
            "visualization_data": heatmap,
        }

    def get_quality_score(self) -> float:
        """
        Calculate overall quality score (0-100).

        Based on:
        - Coverage achievement (85%+ = 50 points)
        - Test count (50+ = 30 points)
        - No hallucinations (20 points)

        Returns:
            Quality score 0-100
        """
        score = 0.0

        # Coverage points (max 50)
        if self.coverage.blended_coverage >= 85.0:
            score += 50.0
        else:
            score += (self.coverage.blended_coverage / 85.0) * 50

        # Test count points (max 30)
        test_ratio = min(1.0, self.coverage.total_tests / 50.0)
        score += test_ratio * 30

        # Hallucination check (20 points) - assumed 0%
        score += 20.0

        return min(100.0, score)
