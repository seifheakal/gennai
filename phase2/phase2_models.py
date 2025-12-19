"""
Phase 2: Data Models & Schemas
Complete Pydantic models for Phase 2 Collaborative Test Design & Generation

All data models are fully typed and validated.
"""

from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum


# ============================================================================
# PHASE 1 INPUT MODELS (From Phase 1 Output)
# ============================================================================

class Locator(BaseModel):
    """Represents a single locator strategy (p1-p5)"""
    p1_role: Optional[str] = None
    p2_label: Optional[str] = None
    p3_testid: Optional[str] = None
    p4_css: Optional[str] = None
    p5_xpath: Optional[str] = None

    def best_strategy(self) -> Tuple[str, Optional[str], float]:
        """
        Return best locator strategy (name, value, confidence).
        Assumes locator_confidence has same structure as this model.
        """
        strategies = [
            ("p1_role", self.p1_role),
            ("p2_label", self.p2_label),
            ("p3_testid", self.p3_testid),
            ("p4_css", self.p4_css),
            ("p5_xpath", self.p5_xpath),
        ]
        # Return first non-None strategy (order matters)
        for name, value in strategies:
            if value is not None:
                return (name, value, 0.0)
        return ("unknown", None, 0.0)


class LocatorConfidence(BaseModel):
    """Confidence scores for each locator strategy"""
    p1_role: Optional[float] = None
    p2_label: Optional[float] = None
    p3_testid: Optional[float] = None
    p4_css: Optional[float] = None
    p5_xpath: Optional[float] = None

    def best_strategy(self) -> Tuple[str, float]:
        """Return best strategy name and confidence score"""
        scores = [
            ("p1_role", self.p1_role),
            ("p2_label", self.p2_label),
            ("p3_testid", self.p3_testid),
            ("p4_css", self.p4_css),
            ("p5_xpath", self.p5_xpath),
        ]
        # Return highest confidence
        best_name, best_score = "unknown", 0.0
        for name, score in scores:
            if score is not None and score > best_score:
                best_name = name
                best_score = score
        return (best_name, best_score)


class Constraint(BaseModel):
    """Input constraints for text/numeric inputs"""
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None
    required: Optional[bool] = False


class Element(BaseModel):
    """Interactive element discovered by Phase 1"""
    element_id: str
    type: str  # "button", "input", "dropdown", "link", "checkbox", etc.
    label: str
    description: Optional[str] = None
    interaction_type: str  # "click", "type", "select", etc.
    locators: Locator
    locator_confidence: LocatorConfidence
    constraints: Optional[Constraint] = None
    valid_values: Optional[List[str]] = None
    invalid_values: Optional[List[str]] = None
    states: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    importance_rank: int = 5

    def get_best_locator(self) -> Tuple[str, str, float]:
        """
        Get best locator strategy for this element.
        Returns: (strategy_name, locator_value, confidence)
        """
        _, strategy_name, _ = self.locators.best_strategy()
        best_strategy, confidence = self.locator_confidence.best_strategy()

        if strategy_name is None:
            return (best_strategy, "", confidence)

        # Get locator value based on strategy
        locator_map = {
            "p1_role": self.locators.p1_role,
            "p2_label": self.locators.p2_label,
            "p3_testid": self.locators.p3_testid,
            "p4_css": self.locators.p4_css,
            "p5_xpath": self.locators.p5_xpath,
        }

        locator_value = locator_map.get(best_strategy, "")
        return (best_strategy, locator_value, confidence)


class Workflow(BaseModel):
    """User workflow from Phase 1 state graph"""
    name: str
    steps: List[str]  # element_ids in sequence
    description: Optional[str] = None


class Phase1Output(BaseModel):
    """Complete Phase 1 exploration output"""
    url: str
    total_elements: int
    interactive_elements: List[Element]
    workflows: Optional[List[Workflow]] = None
    exploration_time_ms: Optional[int] = None


# ============================================================================
# PHASE 2 OUTPUT MODELS (Test Cases & Coverage)
# ============================================================================

class TestStep(BaseModel):
    """Single step in a test case"""
    step_number: int
    action: str  # "Enter username", "Click submit", etc.
    element_id: str
    element_label: str
    element_type: str
    locator: str  # Actual CSS/XPath selector
    locator_strategy: str  # "p1_role", "p2_label", etc.
    locator_confidence: float = Field(ge=0.0, le=1.0)
    input_value: Optional[str] = None
    validation: Dict[str, Any] = Field(default_factory=dict)
    # validation: {"type": "presence", "expected": "Input accepts text"}


class TestCase(BaseModel):
    """Complete test case"""
    test_id: str
    title: str
    description: str
    priority: str  # "high", "medium", "low"
    algorithm_used: str  # "ep", "bva", "state_combination"
    elements_used: List[str]  # element_ids
    test_steps: List[TestStep]
    expected_result: str
    edge_cases_covered: List[str] = Field(default_factory=list)
    coverage_contribution: float = Field(default=0.0, ge=0.0)
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    risk_level: str = "medium"  # "low", "medium", "high"
    priority_score: float = Field(default=0.5, ge=0.0, le=1.0)


class TestCaseFeedback(BaseModel):
    """HITL feedback for a single test"""
    test_id: str
    verdict: str  # "approve", "reject", "modify"
    comment: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    element_id: str
    algorithm: str
    approval_confidence: Optional[float] = None


class FeedbackRound(BaseModel):
    """Single round of HITL feedback"""
    round_number: int
    tests_presented: int
    feedback_items: List[TestCaseFeedback] = Field(default_factory=list)
    approval_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    patterns_learned: List[str] = Field(default_factory=list)

    def calculate_approval_rate(self) -> float:
        """Calculate approval rate from feedback items"""
        if not self.feedback_items:
            return 0.0
        approved = sum(1 for f in self.feedback_items if f.verdict == "approve")
        return approved / len(self.feedback_items)


class CoverageGap(BaseModel):
    """Element that's not covered by tests"""
    element_id: str
    element_label: str
    element_type: str
    element_confidence: float
    reason: str
    recommendation: str


class CoverageMetrics(BaseModel):
    """Complete coverage calculation"""
    element_coverage: float = Field(ge=0.0, le=100.0)
    path_coverage: float = Field(ge=0.0, le=100.0)
    scenario_coverage: float = Field(ge=0.0, le=100.0)
    blended_coverage: float = Field(ge=0.0, le=100.0)
    coverage_by_type: Dict[str, float] = Field(default_factory=dict)
    coverage_gaps: List[CoverageGap] = Field(default_factory=list)
    total_tests: int = 0
    total_elements: int = 0
    tested_elements: int = 0


class HITLResult(BaseModel):
    """Complete HITL 2.0 result"""
    feedback_rounds: List[FeedbackRound] = Field(default_factory=list)
    overall_approval_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    improvements_made: List[str] = Field(default_factory=list)
    patterns_extracted: Dict[str, Any] = Field(default_factory=dict)


class Phase2Output(BaseModel):
    """Complete Phase 2 output"""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tests: List[TestCase] = Field(default_factory=list)
    coverage_metrics: Optional[CoverageMetrics] = None
    hitl_summary: Optional[HITLResult] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export"""
        return {
            "metadata": self.metadata,
            "tests": [t.model_dump() for t in self.tests],
            "coverage_metrics": (
                self.coverage_metrics.model_dump()
                if self.coverage_metrics
                else None
            ),
            "hitl_summary": (
                self.hitl_summary.model_dump() if self.hitl_summary else None
            ),
        }


# ============================================================================
# PARTITION & BOUNDARY MODELS (Algorithm Support)
# ============================================================================

class Partition(BaseModel):
    """Equivalence partition (EP algorithm)"""
    name: str  # "valid", "invalid", "boundary", etc.
    representative: str
    expected_behavior: str
    description: Optional[str] = None


class BoundaryValue(BaseModel):
    """Boundary value for BVA algorithm"""
    value: Any
    boundary_type: str  # "min", "min+1", "max", "max+1", etc.
    description: Optional[str] = None
