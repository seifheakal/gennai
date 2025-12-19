"""
Phase 1 Constants Module

Defines role enums, element type categorizations, and constants used
throughout the Accessibility Parser (Layer 1).
"""

from typing import Set, FrozenSet

__version__ = "1.0.0"

# ============================================================================
# ARIA ROLES - Categorized by Interactivity Type
# ============================================================================

INTERACTIVE_ROLES: FrozenSet[str] = frozenset({
    # Form Controls
    "button",
    "checkbox",
    "radio",
    "textbox",
    "searchbox",
    "spinbutton",
    "slider",
    "combobox",
    "listbox",
    "option",
    
    # Navigation
    "link",
    "tab",
    "tablist",
    "menuitem",
    "menuitemcheckbox",
    "menuitemradio",
    
    # Input Fields
    "textbox",
    "password",
    "email",
    "url",
    "tel",
    "number",
    "range",
    
    # Text Areas
    "textarea",
    
    # Select/Dropdown
    "select",
    "progressbar",
    "status",
})
"""
Interactive roles that users can interact with.
These elements should be discovered and included in output.
"""

CLICKABLE_ROLES: FrozenSet[str] = frozenset({
    "button",
    "link",
    "checkbox",
    "radio",
    "menuitem",
    "menuitemcheckbox",
    "menuitemradio",
    "option",
    "tab",
})
"""Roles that are primarily clickable."""

EDITABLE_ROLES: FrozenSet[str] = frozenset({
    "textbox",
    "password",
    "email",
    "url",
    "tel",
    "number",
    "textarea",
    "searchbox",
    "spinbutton",
})
"""Roles that accept text/value input."""

FOCUSABLE_ROLES: FrozenSet[str] = INTERACTIVE_ROLES
"""Roles that can receive keyboard focus."""

CONTAINER_ROLES: FrozenSet[str] = frozenset({
    "form",
    "dialog",
    "alertdialog",
    "group",
    "region",
    "article",
    "main",
    "navigation",
    "complementary",
    "contentinfo",
})
"""Container roles (not interactive, just organizational)."""

# ============================================================================
# HTML INPUT TYPES
# ============================================================================

INPUT_TYPES_INTERACTIVE: FrozenSet[str] = frozenset({
    "text",
    "password",
    "email",
    "url",
    "tel",
    "number",
    "search",
    "checkbox",
    "radio",
    "file",
    "submit",
    "reset",
    "button",
    "color",
    "date",
    "datetime-local",
    "month",
    "range",
    "time",
    "week",
})
"""HTML input types that are interactive."""

# ============================================================================
# ARIA STATES & PROPERTIES
# ============================================================================

ARIA_STATES = {
    "aria_pressed": "button state (true/false/mixed)",
    "aria_checked": "checkbox/radio state (true/false/mixed)",
    "aria_selected": "option/tab state (true/false)",
    "aria_disabled": "disabled state (true/false)",
    "aria_hidden": "hidden from accessibility tree (true/false)",
    "aria_readonly": "read-only state (true/false)",
    "aria_required": "required field (true/false)",
    "aria_invalid": "validation error (true/false/grammar/spelling)",
    "aria_expanded": "expandable element (true/false/undefined)",
    "aria_current": "current page/item in navigation",
}
"""Common ARIA states and their meanings."""

ARIA_PROPERTIES = {
    "aria_label": "Accessible name",
    "aria_labelledby": "Reference to labeling element",
    "aria_describedby": "Reference to description element",
    "aria_atomic": "Atomic live region updates",
    "aria_live": "Live region update politeness",
    "aria_busy": "Element state busy/loading",
    "aria_controls": "Controls another element",
    "aria_owns": "Owns another element",
    "aria_haspopup": "Has popup menu/dialog",
    "aria_modal": "Modal dialog",
}
"""Common ARIA properties and their meanings."""

# ============================================================================
# LOCATOR PRIORITY STRATEGY
# ============================================================================

LOCATOR_PRIORITIES = [
    {
        "priority": 1,
        "name": "role",
        "method": "getByRole",
        "description": "Role-based (semantic, accessibility-first)",
        "expected_confidence_range": (0.90, 0.98),
        "example": "button[name='Submit']",
    },
    {
        "priority": 2,
        "name": "label",
        "method": "getByLabel",
        "description": "Label-based (form-friendly, accessible)",
        "expected_confidence_range": (0.85, 0.95),
        "example": "label[for='email_input']",
    },
    {
        "priority": 3,
        "name": "placeholder",
        "method": "getByPlaceholder",
        "description": "Placeholder text (input hints)",
        "expected_confidence_range": (0.75, 0.90),
        "example": "input[placeholder='Enter email']",
    },
    {
        "priority": 4,
        "name": "text",
        "method": "getByText",
        "description": "Visible text content",
        "expected_confidence_range": (0.70, 0.85),
        "example": "button:has-text('Click Me')",
    },
    {
        "priority": 5,
        "name": "testid",
        "method": "getByTestId",
        "description": "Test ID attribute (developer-friendly)",
        "expected_confidence_range": (0.85, 0.98),
        "example": "data-testid='submit-button'",
    },
    {
        "priority": 6,
        "name": "css",
        "method": "CSS Selector",
        "description": "CSS selector (generic)",
        "expected_confidence_range": (0.60, 0.80),
        "example": ".form-submit-btn",
        "use_when": "Higher priorities not available",
    },
    {
        "priority": 7,
        "name": "xpath",
        "method": "XPath",
        "description": "XPath expression (fragile, avoid)",
        "expected_confidence_range": (0.40, 0.70),
        "example": "//button[@type='submit']",
        "use_when": "Last resort only",
    },
]
"""Locator strategy priorities (ranked by reliability)."""

# ============================================================================
# ELEMENT CLASSIFICATION
# ============================================================================

FORM_ELEMENTS = frozenset({
    "input",
    "textarea",
    "select",
    "button",
    "fieldset",
    "legend",
    "label",
    "optgroup",
    "option",
})
"""HTML form elements."""

BUTTON_ELEMENTS = frozenset({
    "button",
    "input[type='button']",
    "input[type='submit']",
    "input[type='reset']",
})
"""Button-like elements."""

LINK_ELEMENTS = frozenset({
    "a",
    "link",
    "area",
})
"""Link elements."""

HEADING_ELEMENTS = frozenset({
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
})
"""Heading elements."""

# ============================================================================
# EXPLORATION STRATEGY PRIORITIES
# ============================================================================

EXPLORATION_PRIORITY_ORDER = [
    "form",           # Priority 1: Forms (high signal, contained)
    "button",         # Priority 2: Buttons (actions, navigation)
    "textbox",        # Priority 3: Text inputs (user data entry)
    "checkbox",       # Priority 4: Checkboxes (selections)
    "radio",          # Priority 5: Radio buttons (selections)
    "select",         # Priority 6: Select dropdowns (selections)
    "link",           # Priority 7: Links (navigation)
    "tab",            # Priority 8: Tabs (navigation)
]
"""Order to explore element types during graph traversal."""

# ============================================================================
# VALIDATION THRESHOLDS
# ============================================================================

CONFIDENCE_THRESHOLDS = {
    "high": 0.90,           # > 90% confidence
    "medium": 0.70,         # 70-90% confidence
    "low": 0.50,            # 50-70% confidence
    "very_low": 0.0,        # < 50% confidence
    "accept_threshold": 0.70,  # Minimum to include in output
}
"""Confidence score thresholds."""

MAX_ELEMENT_DISCOVERY_RETRIES = 3
"""Maximum retries to validate element existence."""

ELEMENT_UNIQUENESS_THRESHOLD = 1
"""Locator must match exactly 1 element (not 0, not 2+)."""

# ============================================================================
# ERROR CODES
# ============================================================================

ERROR_CODES = {
    "E001": "Accessibility tree not available",
    "E002": "Page failed to load",
    "E003": "Timeout during exploration",
    "E004": "Element validation failed",
    "E005": "Locator not unique",
    "E006": "Screenshot capture failed",
    "E007": "Browser closed unexpectedly",
    "E008": "Navigation error",
}
"""Error codes for Phase 1."""

# ============================================================================
# DEFAULTS
# ============================================================================

DEFAULT_ELEMENT_WAIT_MS = 5000
"""Default wait time for element discovery: 5 seconds."""

DEFAULT_PAGE_LOAD_WAIT_MS = 30000
"""Default wait time for page load: 30 seconds."""

DEFAULT_SCREENSHOT_QUALITY = 80
"""Screenshot JPEG quality: 1-100."""

DEFAULT_SCREENSHOT_WIDTH = 1280
"""Default screenshot viewport width."""

DEFAULT_SCREENSHOT_HEIGHT = 720
"""Default screenshot viewport height."""

# ============================================================================
# LOGGING CONSTANTS
# ============================================================================

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
"""Valid log levels."""

LOG_FORMAT_JSON = "json"
LOG_FORMAT_TEXT = "text"
"""Log output formats."""
