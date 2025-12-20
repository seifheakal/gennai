"""
Phase 2: Layer 1 - Phase 1 Parser
Parses Phase 1 JSON output and provides indexed access for test generation.
"""

import json
from typing import List, Dict, Optional, Set
from pathlib import Path
from phase2_models import (
    Phase1Output,
    Element,
    Workflow,
    Locator,
    LocatorConfidence,
    Constraint,
)


class Phase1Parser:
    """
    Parses Phase 1 exploration output and builds indices for efficient access.
    LAYER 1: Foundation for all test generation algorithms.
    """

    def __init__(self, phase1_json_path: str):
        """
        Initialize parser with Phase 1 output file.

        Args:
            phase1_json_path: Path to phase1_output.json from Phase 1
        """
        self.phase1_json_path = Path(phase1_json_path)
        self.phase1_output: Optional[Phase1Output] = None
        self._element_map: Dict[str, Element] = {}
        self._elements_by_type: Dict[str, List[Element]] = {}
        self._workflows: List[Workflow] = []

    def parse(self) -> Phase1Output:
        """
        Main parsing function - loads and validates Phase 1 output.

        Returns:
            Parsed Phase1Output object

        Raises:
            FileNotFoundError: If JSON file not found
            ValueError: If JSON structure invalid
        """
        if not self.phase1_json_path.exists():
            raise FileNotFoundError(f"Phase 1 output not found: {self.phase1_json_path}")

        # Load JSON
        with open(self.phase1_json_path, "r") as f:
            raw_data = json.load(f)

        # Validate and construct Phase1Output
        self.phase1_output = self._construct_phase1_output(raw_data)

        # Build indices
        self._build_indices()

        return self.phase1_output

    def _construct_phase1_output(self, raw_data: dict) -> Phase1Output:
        """
        Construct Phase1Output from raw JSON data.

        Handles flexible Phase 1 JSON format.
        """
        # Extract top-level fields - handle both 'url' and 'page_url'
        url = raw_data.get("url") or raw_data.get("page_url", "")
        total_elements = raw_data.get("total_elements", 0)
        exploration_time_ms = raw_data.get("exploration_time_ms")

        # Parse elements
        interactive_elements = []
        for elem_data in raw_data.get("interactive_elements", []):
            element = self._parse_element(elem_data)
            interactive_elements.append(element)

        # Parse workflows
        workflows = []
        for wf_data in raw_data.get("workflows", []):
            workflow = Workflow(
                name=wf_data.get("name", ""),
                steps=wf_data.get("steps", []),
                description=wf_data.get("description"),
            )
            workflows.append(workflow)

        return Phase1Output(
            url=url,
            total_elements=total_elements,
            interactive_elements=interactive_elements,
            workflows=workflows if workflows else None,
            exploration_time_ms=exploration_time_ms,
        )

    def _parse_element(self, elem_data: dict) -> Element:
        """Parse single element from Phase 1 data"""
        # Parse locators - handle both priority_X and pX formats
        locators_data = elem_data.get("locators", {})
        locators = Locator(
            p1_role=locators_data.get("p1_role") or locators_data.get("priority_1_role"),
            p2_label=locators_data.get("p2_label") or locators_data.get("priority_2_label"),
            p3_testid=locators_data.get("p3_testid") or locators_data.get("priority_3_placeholder") or locators_data.get("priority_5_testid"),
            p4_css=locators_data.get("p4_css") or locators_data.get("priority_4_text") or locators_data.get("priority_6_css"),
            p5_xpath=locators_data.get("p5_xpath") or locators_data.get("priority_7_xpath"),
        )

        # Parse confidence scores - handle both formats
        confidence_data = elem_data.get("locator_confidence", {})
        locator_confidence = LocatorConfidence(
            p1_role=confidence_data.get("p1_role") or confidence_data.get("priority_1_role"),
            p2_label=confidence_data.get("p2_label") or confidence_data.get("priority_2_label"),
            p3_testid=confidence_data.get("p3_testid") or confidence_data.get("priority_3_placeholder") or confidence_data.get("priority_5_testid"),
            p4_css=confidence_data.get("p4_css") or confidence_data.get("priority_4_text") or confidence_data.get("priority_6_css"),
            p5_xpath=confidence_data.get("p5_xpath") or confidence_data.get("priority_7_xpath"),
        )

        # Parse constraints
        constraints = None
        if "constraints" in elem_data:
            constraint_data = elem_data["constraints"]
            constraints = Constraint(
                min_length=constraint_data.get("min_length"),
                max_length=constraint_data.get("max_length"),
                min_value=constraint_data.get("min_value"),
                max_value=constraint_data.get("max_value"),
                pattern=constraint_data.get("pattern"),
                required=constraint_data.get("required"),
            )

        return Element(
            element_id=elem_data.get("element_id", ""),
            type=elem_data.get("type", ""),
            label=elem_data.get("label", ""),
            description=elem_data.get("description"),
            interaction_type=elem_data.get("interaction_type", "click"),
            locators=locators,
            locator_confidence=locator_confidence,
            constraints=constraints,
            valid_values=elem_data.get("valid_values"),
            invalid_values=elem_data.get("invalid_values"),
            states=elem_data.get("states"),
            dependencies=elem_data.get("dependencies"),
            importance_rank=elem_data.get("importance_rank", 5),
        )

    def _build_indices(self):
        """Build fast lookup indices"""
        if self.phase1_output is None:
            raise ValueError("Must call parse() first")

        # Element map by ID
        self._element_map = {
            elem.element_id: elem
            for elem in self.phase1_output.interactive_elements
        }

        # Elements by type
        self._elements_by_type = {}
        for elem in self.phase1_output.interactive_elements:
            if elem.type not in self._elements_by_type:
                self._elements_by_type[elem.type] = []
            self._elements_by_type[elem.type].append(elem)

        # Workflows
        self._workflows = self.phase1_output.workflows or []

    def get_all_elements(self) -> List[Element]:
        """Get all interactive elements"""
        if self.phase1_output is None:
            raise ValueError("Must call parse() first")
        return self.phase1_output.interactive_elements

    def get_element_by_id(self, element_id: str) -> Optional[Element]:
        """Get single element by ID"""
        return self._element_map.get(element_id)

    def get_elements_by_type(self, element_type: str) -> List[Element]:
        """Get all elements of given type"""
        return self._elements_by_type.get(element_type, [])

    def get_workflows(self) -> List[Workflow]:
        """Get all workflows"""
        return self._workflows

    def get_element_dependencies(self, element_id: str) -> List[str]:
        """Get elements that this element depends on"""
        element = self.get_element_by_id(element_id)
        if element is None or element.dependencies is None:
            return []
        return element.dependencies

    def validate_phase1_output(self) -> bool:
        """
        Validate Phase 1 output structure.

        Returns:
            True if valid, raises exception if not
        """
        if self.phase1_output is None:
            raise ValueError("Must call parse() first")

        errors = []

        # Check: all elements have element_id
        for elem in self.phase1_output.interactive_elements:
            if not elem.element_id:
                errors.append("Element missing element_id")

        # Check: all elements have locators
        for elem in self.phase1_output.interactive_elements:
            if not elem.locators:
                errors.append(f"Element {elem.element_id} missing locators")

        # Check: confidence scores are 0-1
        for elem in self.phase1_output.interactive_elements:
            for strategy in [
                elem.locator_confidence.p1_role,
                elem.locator_confidence.p2_label,
                elem.locator_confidence.p3_testid,
                elem.locator_confidence.p4_css,
                elem.locator_confidence.p5_xpath,
            ]:
                if strategy is not None and not (0.0 <= strategy <= 1.0):
                    errors.append(
                        f"Element {elem.element_id} has invalid confidence {strategy}"
                    )

        if errors:
            raise ValueError(f"Phase 1 validation errors: {errors}")

        return True

    def get_element_coverage_gap(self, tested_element_ids: Set[str]) -> float:
        """
        Calculate coverage gap (untested elements as percentage).

        Args:
            tested_element_ids: Set of element_ids that have tests

        Returns:
            Percentage of elements NOT tested (0-100)
        """
        total = len(self.phase1_output.interactive_elements)
        untested = total - len(tested_element_ids)
        return (untested / total * 100) if total > 0 else 0.0

    def get_element_info(self, element_id: str) -> Dict:
        """Get detailed info about element (for debugging)"""
        element = self.get_element_by_id(element_id)
        if element is None:
            return {}

        _, best_locator, best_confidence = element.get_best_locator()

        return {
            "element_id": element.element_id,
            "type": element.type,
            "label": element.label,
            "best_locator": best_locator,
            "best_confidence": best_confidence,
            "constraints": element.constraints.model_dump() if element.constraints else None,
            "valid_values": element.valid_values,
            "invalid_values": element.invalid_values,
            "states": element.states,
            "importance_rank": element.importance_rank,
        }

    def summary(self) -> Dict:
        """Get summary of Phase 1 output"""
        if self.phase1_output is None:
            raise ValueError("Must call parse() first")

        return {
            "url": self.phase1_output.url,
            "total_elements": self.phase1_output.total_elements,
            "exploration_time_ms": self.phase1_output.exploration_time_ms,
            "element_types": list(self._elements_by_type.keys()),
            "elements_by_type": {
                t: len(e) for t, e in self._elements_by_type.items()
            },
            "workflows_count": len(self._workflows),
            "high_confidence_elements": sum(
                1
                for e in self.phase1_output.interactive_elements
                if e.locator_confidence.best_strategy()[1] >= 0.90
            ),
            "low_confidence_elements": sum(
                1
                for e in self.phase1_output.interactive_elements
                if e.locator_confidence.best_strategy()[1] < 0.70
            ),
        }
