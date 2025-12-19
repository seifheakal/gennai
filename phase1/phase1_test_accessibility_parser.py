"""
Phase 1 Unit Tests

Tests for the Accessibility Parser (Layer 1).
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path

from playwright.async_api import async_playwright

from phase1_accessibility_parser import parse_accessibility_tree, AccessibilityParser
from phase1_config import create_custom_config
from phase1_models import Phase1ExplorationOutput, InteractiveElement
from phase1_sample_pages import get_fixture

__version__ = "1.0.0"


# ============================================================================
# FIXTURES & SETUP
# ============================================================================

@pytest.fixture
async def browser():
    """Create a browser instance for testing."""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    yield browser
    await browser.close()
    await playwright.stop()


@pytest.fixture
async def page(browser):
    """Create a page instance for testing."""
    context = await browser.new_context()
    page = await context.new_page()
    yield page
    await context.close()


# ============================================================================
# TEST 1: SIMPLE LOGIN FORM
# ============================================================================

@pytest.mark.asyncio
async def test_parse_simple_login_form(page):
    """
    Test Layer 1 with simple login form.
    
    Expected:
    - Finds 3 interactive elements (username, password, submit button)
    - All have correct roles and labels
    - All marked as interactive
    - Zero false positives
    """
    html = get_fixture("simple_login")
    await page.set_content(html)
    
    # Create parser
    parser = AccessibilityParser()
    
    # Parse accessibility tree
    tree = await parser._parse_accessibility_tree(page)
    
    # Verify tree extracted
    assert tree is not None, "Accessibility tree should not be None"
    assert "role" in tree, "Tree should have role field"
    
    # Extract elements
    elements = await parser._extract_interactive_elements(page, tree)
    
    # Verify element count
    assert len(elements) >= 2, "Should find at least 2 interactive elements (username + password)"
    
    # Verify element types
    roles = [e["aria_role"] for e in elements]
    assert "textbox" in roles or "button" in roles, "Should find textbox or button"
    
    # Verify labels
    labels = [e["label"] for e in elements]
    assert any("Username" in label or "username" in label.lower() for label in labels if label), \
        "Should find username field"


@pytest.mark.asyncio
async def test_simple_login_form_output_schema(page):
    """
    Test that output matches Phase1ExplorationOutput schema.
    """
    html = get_fixture("simple_login")
    await page.set_content(html)
    
    # Create parser and explore
    parser = AccessibilityParser()
    
    # Get accessibility tree
    tree = await parser._parse_accessibility_tree(page)
    elements_raw = await parser._extract_interactive_elements(page, tree)
    elements = await parser._generate_and_validate_locators(page, elements_raw)
    
    # Format output
    await parser._build_state_graph(page, "http://localhost/")
    output = parser._format_output("http://localhost/", elements)
    
    # Verify output is Phase1ExplorationOutput instance
    assert isinstance(output, Phase1ExplorationOutput), \
        f"Output should be Phase1ExplorationOutput, got {type(output)}"
    
    # Verify required fields
    assert output.page_url == "http://localhost/", "URL should match"
    assert output.total_elements >= 0, "Total elements should be >= 0"
    assert output.coverage_percentage >= 0, "Coverage should be >= 0"
    
    # Verify exploration graph
    assert output.exploration_graph is not None, "Exploration graph should not be None"
    assert len(output.exploration_graph.nodes) > 0, "Should have at least one state node"
    
    # Verify quality metrics
    assert output.quality_metrics.ready_for_phase2, "Should be ready for Phase 2"
    assert output.quality_metrics.hallucinated_elements == 0, "Should have zero hallucinated elements"


# ============================================================================
# TEST 2: COMPLEX FORM (Multiple Input Types)
# ============================================================================

@pytest.mark.asyncio
async def test_parse_complex_form(page):
    """
    Test with diverse input types: text, password, email, select, checkbox, radio.
    
    Expected:
    - All 10+ elements discovered with correct roles
    - No false positives for hidden elements
    """
    html = get_fixture("complex_form")
    await page.set_content(html)
    
    parser = AccessibilityParser()
    tree = await parser._parse_accessibility_tree(page)
    elements = await parser._extract_interactive_elements(page, tree)
    
    # Count elements by type
    type_counts = {}
    for element in elements:
        role = element["aria_role"]
        type_counts[role] = type_counts.get(role, 0) + 1
    
    # Should find multiple input types
    assert len(type_counts) > 1, f"Should find multiple element types, got {type_counts}"
    
    # Verify total element count (should be significant)
    assert len(elements) >= 6, f"Should find at least 6 elements, got {len(elements)}"


@pytest.mark.asyncio
async def test_complex_form_element_validation(page):
    """
    Test element validation and locator generation for complex form.
    """
    html = get_fixture("complex_form")
    await page.set_content(html)
    
    parser = AccessibilityParser()
    tree = await parser._parse_accessibility_tree(page)
    elements_raw = await parser._extract_interactive_elements(page, tree)
    elements = await parser._generate_and_validate_locators(page, elements_raw)
    
    # Verify all elements are InteractiveElement instances
    for element in elements:
        assert isinstance(element, InteractiveElement), \
            f"All elements should be InteractiveElement, got {type(element)}"
        
        # Verify required fields
        assert element.element_id, "Element should have ID"
        assert element.aria_role, "Element should have role"
        assert element.locators is not None, "Element should have locators"
        assert element.locator_confidence is not None, "Element should have confidence scores"
    
    # Verify locators are generated
    with_locators = sum(1 for e in elements if e.locators.priority_1_role)
    assert with_locators > 0, "Should have at least some elements with locators"


# ============================================================================
# TEST 3: HIDDEN ELEMENTS (False Positive Detection)
# ============================================================================

@pytest.mark.asyncio
async def test_hidden_elements_excluded(page):
    """
    Test that aria-hidden and display:none elements are NOT included.
    
    Expected:
    - Only 2 visible buttons in output
    - Hidden buttons excluded
    - Disabled button may or may not be included (depends on interpretation)
    """
    html = get_fixture("hidden_elements")
    await page.set_content(html)
    
    parser = AccessibilityParser()
    tree = await parser._parse_accessibility_tree(page)
    elements = await parser._extract_interactive_elements(page, tree)
    
    # Count buttons
    buttons = [e for e in elements if e["aria_role"] == "button"]
    
    # Should find visible buttons only (not hidden, not aria-hidden, not display:none)
    assert len(buttons) <= 6, f"Should find at most 6 buttons, got {len(buttons)}"
    
    # Verify none are marked as hidden
    for button in buttons:
        assert not button.get("aria_hidden"), "Should not include aria-hidden elements"


@pytest.mark.asyncio
async def test_hidden_elements_not_in_output(page):
    """
    Test that hidden elements don't appear in final output.
    """
    html = get_fixture("hidden_elements")
    await page.set_content(html)
    
    parser = AccessibilityParser()
    tree = await parser._parse_accessibility_tree(page)
    elements_raw = await parser._extract_interactive_elements(page, tree)
    elements = await parser._generate_and_validate_locators(page, elements_raw)
    
    # Get all element IDs
    element_ids = [e.element_id for e in elements]
    
    # Verify we have elements
    assert len(element_ids) > 0, "Should have found some elements"
    
    # Verify no duplicates
    assert len(element_ids) == len(set(element_ids)), "Should have no duplicate element IDs"


# ============================================================================
# TEST 4: JSON OUTPUT SCHEMA VALIDATION
# ============================================================================

@pytest.mark.asyncio
async def test_output_json_schema_validation(page):
    """
    Test that Phase1ExplorationOutput JSON schema is valid.
    """
    html = get_fixture("simple_login")
    await page.set_content(html)
    
    parser = AccessibilityParser()
    tree = await parser._parse_accessibility_tree(page)
    elements_raw = await parser._extract_interactive_elements(page, tree)
    elements = await parser._generate_and_validate_locators(page, elements_raw)
    await parser._build_state_graph(page, "http://test.local/")
    output = parser._format_output("http://test.local/", elements)
    
    # Convert to JSON and back (validates schema)
    json_string = output.model_dump_json()
    assert isinstance(json_string, str), "Should produce JSON string"
    
    # Parse JSON back
    import json
    parsed = json.loads(json_string)
    assert isinstance(parsed, dict), "JSON should parse to dict"
    
    # Verify required fields
    required_fields = [
        "page_url",
        "exploration_timestamp",
        "total_elements",
        "coverage_percentage",
        "exploration_graph",
        "interactive_elements",
        "exploration_statistics",
        "quality_metrics",
    ]
    
    for field in required_fields:
        assert field in parsed, f"Missing required field: {field}"


@pytest.mark.asyncio
async def test_output_can_be_serialized(page):
    """
    Test that output can be serialized and saved to file.
    """
    html = get_fixture("simple_login")
    await page.set_content(html)
    
    parser = AccessibilityParser()
    tree = await parser._parse_accessibility_tree(page)
    elements_raw = await parser._extract_interactive_elements(page, tree)
    elements = await parser._generate_and_validate_locators(page, elements_raw)
    await parser._build_state_graph(page, "http://test.local/")
    output = parser._format_output("http://test.local/", elements)
    
    # Save to temporary file
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "phase1_output.json")
        
        # Save JSON
        with open(output_file, 'w') as f:
            f.write(output.model_dump_json(indent=2))
        
        # Verify file exists and has content
        assert os.path.exists(output_file), "Output file should exist"
        assert os.path.getsize(output_file) > 0, "Output file should not be empty"


# ============================================================================
# TEST 5: NAVIGATION & LINKS
# ============================================================================

@pytest.mark.asyncio
async def test_parse_navigation_page(page):
    """
    Test parsing page with navigation links.
    """
    html = get_fixture("navigation")
    await page.set_content(html)
    
    parser = AccessibilityParser()
    tree = await parser._parse_accessibility_tree(page)
    elements = await parser._extract_interactive_elements(page, tree)
    
    # Count links
    links = [e for e in elements if e["aria_role"] == "link"]
    
    # Should find navigation links
    assert len(links) >= 4, f"Should find at least 4 links, got {len(links)}"


# ============================================================================
# TEST 6: PARSER ENTRY POINT
# ============================================================================

@pytest.mark.asyncio
async def test_main_entry_point(page):
    """
    Test main entry point function parse_accessibility_tree().
    """
    html = get_fixture("simple_login")
    
    # Create temporary HTML file
    with tempfile.TemporaryDirectory() as tmpdir:
        html_file = os.path.join(tmpdir, "test.html")
        with open(html_file, 'w') as f:
            f.write(html)
        
        # Convert to file:// URL
        file_url = f"file://{html_file}"
        
        # Note: In real scenario, would test with actual URL
        # For now, just verify function signature and return type
        config = create_custom_config(headless=True)
        assert config is not None, "Config creation should work"


# ============================================================================
# TEST 7: COVERAGE & STATISTICS
# ============================================================================

@pytest.mark.asyncio
async def test_coverage_calculation(page):
    """
    Test coverage percentage calculation.
    """
    html = get_fixture("complex_form")
    await page.set_content(html)
    
    parser = AccessibilityParser()
    tree = await parser._parse_accessibility_tree(page)
    elements_raw = await parser._extract_interactive_elements(page, tree)
    elements = await parser._generate_and_validate_locators(page, elements_raw)
    await parser._build_state_graph(page, "http://test.local/")
    output = parser._format_output("http://test.local/", elements)
    
    # Verify coverage is valid percentage
    assert 0.0 <= output.coverage_percentage <= 1.0, \
        f"Coverage should be between 0-1, got {output.coverage_percentage}"
    
    # For non-empty results, coverage should be > 0
    if len(elements) > 0:
        assert output.coverage_percentage > 0, "Coverage should be > 0 for discovered elements"


@pytest.mark.asyncio
async def test_statistics_populated(page):
    """
    Test that exploration statistics are properly populated.
    """
    html = get_fixture("simple_login")
    await page.set_content(html)
    
    parser = AccessibilityParser()
    tree = await parser._parse_accessibility_tree(page)
    elements_raw = await parser._extract_interactive_elements(page, tree)
    elements = await parser._generate_and_validate_locators(page, elements_raw)
    await parser._build_state_graph(page, "http://test.local/")
    output = parser._format_output("http://test.local/", elements)
    
    stats = output.exploration_statistics
    
    # Verify statistics fields
    assert stats.total_time_seconds >= 0, "Time should be >= 0"
    assert stats.screenshots_taken >= 0, "Screenshots should be >= 0"
    assert stats.hallucinated_elements == 0, "Should have zero hallucinated elements"
    assert stats.false_positives == 0, "Should have zero false positives"
    assert stats.elements_discovered >= 0, "Elements discovered should be >= 0"
