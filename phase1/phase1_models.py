"""
Phase 1 Pydantic Models

Defines data models for accessibility tree parsing, element extraction,
and JSON schema validation for Phase 1 output.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

__version__ = "1.0.0"


# ============================================================================
# ARIA STATE MODELS
# ============================================================================

class AriaStates(BaseModel):
    """ARIA state values for an element."""
    
    pressed: Optional[bool] = Field(None, description="Button pressed state")
    checked: Optional[bool] = Field(None, description="Checkbox/radio checked state")
    selected: Optional[bool] = Field(None, description="Option/tab selected state")
    disabled: bool = Field(False, description="Element disabled")
    hidden: bool = Field(False, description="Element hidden from a11y tree")
    readonly: bool = Field(False, description="Element read-only")
    required: bool = Field(False, description="Element required")
    invalid: bool = Field(False, description="Element has validation error")
    expanded: Optional[bool] = Field(None, description="Expandable element state")
    readonly_value: Optional[bool] = Field(None, description="ARIA readonly value")


class AccessibilityInfo(BaseModel):
    """Accessibility attributes of an element."""
    
    role: str = Field(..., description="ARIA role")
    accessible_name: str = Field("", description="Accessible name")
    accessible_description: str = Field("", description="Accessible description")
    labelledby: Optional[str] = Field(None, description="aria-labelledby reference")
    describedby: Optional[str] = Field(None, description="aria-describedby reference")
    aria_label: Optional[str] = Field(None, description="aria-label value")


class Interactivity(BaseModel):
    """Interactivity capabilities of an element."""
    
    focusable: bool = Field(False, description="Element can receive keyboard focus")
    clickable: bool = Field(False, description="Element can be clicked")
    editable: bool = Field(False, description="Element accepts text input")
    submittable: bool = Field(False, description="Element is form submit button")


# ============================================================================
# LOCATOR MODELS
# ============================================================================

class LocatorConfidenceScores(BaseModel):
    """Confidence scores for each locator strategy."""
    
    priority_1_role: float = Field(0.0, ge=0.0, le=1.0)
    priority_2_label: float = Field(0.0, ge=0.0, le=1.0)
    priority_3_placeholder: float = Field(0.0, ge=0.0, le=1.0)
    priority_4_text: float = Field(0.0, ge=0.0, le=1.0)
    priority_5_testid: float = Field(0.0, ge=0.0, le=1.0)
    priority_6_css: float = Field(0.0, ge=0.0, le=1.0)
    priority_7_xpath: float = Field(0.0, ge=0.0, le=1.0)
    
    def average(self) -> float:
        """Get average confidence across all strategies."""
        scores = [
            self.priority_1_role,
            self.priority_2_label,
            self.priority_3_placeholder,
            self.priority_4_text,
            self.priority_5_testid,
        ]
        valid_scores = [s for s in scores if s > 0]
        return sum(valid_scores) / len(valid_scores) if valid_scores else 0.0


class Locators(BaseModel):
    """Locator strategies for an element (5 priorities)."""
    
    priority_1_role: Optional[str] = Field(None, description="getByRole locator")
    priority_2_label: Optional[str] = Field(None, description="getByLabel locator")
    priority_3_placeholder: Optional[str] = Field(None, description="getByPlaceholder locator")
    priority_4_text: Optional[str] = Field(None, description="getByText locator")
    priority_5_testid: Optional[str] = Field(None, description="getByTestId locator")
    priority_6_css: Optional[str] = Field(None, description="CSS selector (fallback)")
    priority_7_xpath: Optional[str] = Field(None, description="XPath (last resort)")


# ============================================================================
# ELEMENT STATE MODELS
# ============================================================================

class ElementState(BaseModel):
    """State of an element in a specific page state."""
    
    state_id: str = Field(..., description="Page state ID")
    visible: bool = Field(True, description="Element is visible")
    enabled: bool = Field(True, description="Element is enabled")
    value: Optional[str] = Field(None, description="Element value")
    aria_pressed: Optional[bool] = Field(None)
    aria_checked: Optional[bool] = Field(None)


class ValidationEvidence(BaseModel):
    """Evidence from validation layers."""
    
    screenshot_confirmed: bool = Field(False, description="Layer B: Screenshot verified visibility")
    aria_confirmed: bool = Field(False, description="Layer A: Accessibility tree confirmed existence")
    uniqueness_confirmed: bool = Field(False, description="Layer D: Locator uniqueness verified")
    false_positive_check: bool = Field(False, description="Layer E: Not a false positive")
    interactive_confirmed: bool = Field(False, description="Layer C: Interactive capability verified")


# ============================================================================
# INTERACTIVE ELEMENT MODEL
# ============================================================================

class InteractiveElement(BaseModel):
    """Complete model for an interactive element."""
    
    element_id: str = Field(..., description="Unique element identifier")
    type: str = Field(..., description="Element type (button, input, link, etc.)")
    label: str = Field("", description="Human-readable label/text")
    aria_role: str = Field(..., description="ARIA role")
    aria_label: str = Field("", description="ARIA label")
    visible: bool = Field(True, description="Element is visible")
    enabled: bool = Field(True, description="Element is enabled")
    
    # Locators
    locators: Locators = Field(..., description="5 locator strategies")
    locator_confidence: LocatorConfidenceScores = Field(..., description="Confidence for each strategy")
    
    # Accessibility
    accessibility_info: AccessibilityInfo = Field(..., description="ARIA attributes")
    interactivity: Interactivity = Field(..., description="Interactivity capabilities")
    
    # States & Evidence
    states: List[ElementState] = Field(default_factory=list, description="Element states across page states")
    validation_evidence: ValidationEvidence = Field(..., description="Validation layer evidence")
    
    # Metadata
    hierarchy_path: List[str] = Field(default_factory=list, description="DOM hierarchy path")
    hierarchy_depth: int = Field(0, ge=0, description="Depth in DOM tree")


# ============================================================================
# EXPLORATION GRAPH MODELS
# ============================================================================

class GraphNode(BaseModel):
    """Node in the exploration state graph."""
    
    state_id: str = Field(..., description="Unique state identifier")
    label: str = Field(..., description="Human-readable state description")
    url: str = Field(..., description="URL of this state")
    screenshot: Optional[str] = Field(None, description="Screenshot filename")
    timestamp: float = Field(0.0, description="Timestamp when state was discovered")
    
    
class GraphEdge(BaseModel):
    """Edge in the exploration state graph."""
    
    from_state: str = Field(..., description="Source state ID")
    to_state: str = Field(..., description="Destination state ID")
    action: str = Field(..., description="Action that triggered transition (click, fill, select, etc.)")
    element_id: str = Field(..., description="Element ID that was interacted with")
    description: str = Field("", description="Human description of the action")
    timestamp: float = Field(0.0, description="Time taken for action (seconds)")


class ExplorationGraph(BaseModel):
    """Complete exploration state graph."""
    
    nodes: List[GraphNode] = Field(default_factory=list, description="State nodes")
    edges: List[GraphEdge] = Field(default_factory=list, description="State transitions")


# ============================================================================
# VALIDATION CHECKPOINT MODELS
# ============================================================================

class ValidationCheckpoint(BaseModel):
    """Validation checkpoint result."""
    
    checkpoint_id: str = Field(..., description="Checkpoint identifier")
    description: str = Field(..., description="What was validated")
    passed: bool = Field(..., description="Did checkpoint pass?")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Evidence of validation")


# ============================================================================
# EXPLORATION STATISTICS
# ============================================================================

class ExplorationStatistics(BaseModel):
    """Statistics about the exploration process."""
    
    total_time_seconds: float = Field(0.0, description="Total exploration time")
    screenshots_taken: int = Field(0, description="Number of screenshots captured")
    tokens_used_accessibility_tree: int = Field(0, description="Tokens used for ARIA tree")
    tokens_estimate_full_dom: int = Field(0, description="Estimated tokens if using full DOM")
    efficiency_ratio: float = Field(1.0, description="Efficiency: full_dom / accessibility_tree")
    elements_discovered: int = Field(0, description="Total elements discovered")
    elements_with_multiple_locators: int = Field(0, description="Elements with all 5 locators")
    elements_with_fallback_xpath: int = Field(0, description="Elements that needed XPath fallback")
    hallucinated_elements: int = Field(0, description="Hallucinated false positives (should be 0)")
    false_positives: int = Field(0, description="Elements incorrectly marked as interactive")
    states_discovered: int = Field(1, description="Number of page states discovered")


class QualityMetrics(BaseModel):
    """Quality metrics for the exploration."""
    
    coverage_percentage: float = Field(0.85, ge=0.0, le=1.0, description="Element coverage %")
    accessibility_compliance: float = Field(1.0, ge=0.0, le=1.0, description="Accessibility compliance %")
    locator_reliability_avg: float = Field(0.9, ge=0.0, le=1.0, description="Average locator reliability")
    validation_pass_rate: float = Field(1.0, ge=0.0, le=1.0, description="Validation success rate")
    ready_for_phase2: bool = Field(True, description="Ready to hand off to Phase 2?")


# ============================================================================
# MAIN EXPLORATION OUTPUT MODEL
# ============================================================================

class Phase1ExplorationOutput(BaseModel):
    """Complete Phase 1 exploration output."""
    
    # Metadata
    page_url: str = Field(..., description="Target page URL")
    exploration_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When exploration occurred")
    total_states_discovered: int = Field(1, description="Number of unique page states")
    total_elements: int = Field(0, description="Total interactive elements discovered")
    coverage_percentage: float = Field(0.0, description="Element coverage percentage")
    
    # Core Data
    exploration_graph: ExplorationGraph = Field(default_factory=ExplorationGraph, description="State graph")
    interactive_elements: List[InteractiveElement] = Field(default_factory=list, description="Discovered elements")
    validation_checkpoints: List[ValidationCheckpoint] = Field(default_factory=list, description="Validation results")
    
    # Statistics
    exploration_statistics: ExplorationStatistics = Field(default_factory=ExplorationStatistics)
    quality_metrics: QualityMetrics = Field(default_factory=QualityMetrics)
    
    # Notes
    challenges: List[str] = Field(default_factory=list, description="Challenges encountered")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for Phase 2")
    next_phase_hints: List[str] = Field(default_factory=list, description="Hints for test generation")
    
    @field_validator("coverage_percentage")
    def validate_coverage(cls, v: float) -> float:
        """Ensure coverage is between 0-100%."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Coverage must be between 0.0 and 1.0")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump(by_alias=True)
    
    def to_json_string(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json(indent=2, by_alias=True)
