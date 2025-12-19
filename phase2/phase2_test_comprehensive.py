"""
Phase 2: Comprehensive Unit Tests
Tests for Layer 1 & Layer 2 - 15+ unit tests covering all functionality
"""

import json
import pytest
from pathlib import Path
from phase2_models import (
    Phase1Output,
    Element,
    Workflow,
    Locator,
    LocatorConfidence,
    Constraint,
    TestCase,
    TestStep,
)
from phase2_phase1_parser import Phase1Parser
from phase2_validators import HallucinationDetector
from phase2_equivalence_partitioning import EquivalencePartitioning
from phase2_boundary_value_analysis import BoundaryValueAnalysis
from phase2_test_generator import TestGenerator, StateCombinationTesting


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_phase1_output_dict():
    """Create sample Phase 1 output for testing"""
    return {
        "url": "https://example.com/login",
        "total_elements": 3,
        "exploration_time_ms": 5000,
        "interactive_elements": [
            {
                "element_id": "elem_001",
                "type": "input",
                "label": "Username",
                "description": "Username input field",
                "interaction_type": "type",
                "locators": {
                    "p1_role": "input[aria-label='Username']",
                    "p2_label": "input[placeholder='Username']",
                    "p3_testid": "input[data-testid='username']",
                    "p4_css": "input.username-field",
                    "p5_xpath": "//input[@id='username']"
                },
                "locator_confidence": {
                    "p1_role": 0.95,
                    "p2_label": 0.92,
                    "p3_testid": 0.98,
                    "p4_css": 0.88,
                    "p5_xpath": 0.85
                },
                "constraints": {
                    "min_length": 3,
                    "max_length": 50,
                    "required": True
                },
                "valid_values": ["user123", "testuser"],
                "invalid_values": ["ab", "user@invalid"],
                "importance_rank": 1
            },
            {
                "element_id": "elem_002",
                "type": "input",
                "label": "Password",
                "description": "Password input field",
                "interaction_type": "type",
                "locators": {
                    "p1_role": "input[type='password']",
                    "p3_testid": "input[data-testid='password']",
                },
                "locator_confidence": {
                    "p1_role": 0.96,
                    "p3_testid": 0.99,
                },
                "constraints": {
                    "min_length": 8,
                    "max_length": 128,
                    "required": True
                },
                "valid_values": ["password123"],
                "importance_rank": 2
            },
            {
                "element_id": "elem_003",
                "type": "button",
                "label": "Submit",
                "description": "Submit button",
                "interaction_type": "click",
                "locators": {
                    "p1_role": "button[name='Submit']",
                    "p3_testid": "button[data-testid='login-submit']"
                },
                "locator_confidence": {
                    "p1_role": 0.97,
                    "p3_testid": 0.99
                },
                "importance_rank": 1
            }
        ],
        "workflows": [
            {
                "name": "login_flow",
                "steps": ["elem_001", "elem_002", "elem_003"],
                "description": "Complete login workflow"
            }
        ]
    }


@pytest.fixture
def temp_phase1_json(tmp_path, sample_phase1_output_dict):
    """Create temporary Phase 1 JSON file"""
    json_file = tmp_path / "phase1_output.json"
    with open(json_file, "w") as f:
        json.dump(sample_phase1_output_dict, f)
    return str(json_file)


# ============================================================================
# LAYER 1 TESTS: Phase1Parser
# ============================================================================

class TestPhase1Parser:
    """Tests for Phase 1 Parser (Layer 1)"""

    def test_parse_valid_phase1_output(self, temp_phase1_json):
        """Test parsing valid Phase 1 JSON"""
        parser = Phase1Parser(temp_phase1_json)
        output = parser.parse()

        assert output is not None
        assert output.url == "https://example.com/login"
        assert output.total_elements == 3
        assert len(output.interactive_elements) == 3

    def test_element_lookup_by_id(self, temp_phase1_json):
        """Test looking up element by ID"""
        parser = Phase1Parser(temp_phase1_json)
        parser.parse()

        elem = parser.get_element_by_id("elem_001")
        assert elem is not None
        assert elem.label == "Username"
        assert elem.type == "input"

    def test_get_elements_by_type(self, temp_phase1_json):
        """Test filtering elements by type"""
        parser = Phase1Parser(temp_phase1_json)
        parser.parse()

        input_elements = parser.get_elements_by_type("input")
        assert len(input_elements) == 2

        button_elements = parser.get_elements_by_type("button")
        assert len(button_elements) == 1

    def test_best_locator_strategy(self, temp_phase1_json):
        """Test getting best locator strategy"""
        parser = Phase1Parser(temp_phase1_json)
        parser.parse()

        elem = parser.get_element_by_id("elem_001")
        strategy, locator, confidence = elem.get_best_locator()

        assert strategy == "p3_testid"  # Highest confidence
        assert confidence == 0.98
        assert "data-testid='username'" in locator

    def test_validation_passes(self, temp_phase1_json):
        """Test Phase 1 output validation"""
        parser = Phase1Parser(temp_phase1_json)
        parser.parse()

        # Should not raise exception
        assert parser.validate_phase1_output() is True

    def test_get_workflows(self, temp_phase1_json):
        """Test retrieving workflows"""
        parser = Phase1Parser(temp_phase1_json)
        parser.parse()

        workflows = parser.get_workflows()
        assert len(workflows) == 1
        assert workflows[0].name == "login_flow"
        assert len(workflows[0].steps) == 3

    def test_summary_info(self, temp_phase1_json):
        """Test getting summary information"""
        parser = Phase1Parser(temp_phase1_json)
        parser.parse()

        summary = parser.summary()
        assert summary["total_elements"] == 3
        assert "input" in summary["element_types"]
        assert "button" in summary["element_types"]
        assert summary["high_confidence_elements"] >= 1


# ============================================================================
# VALIDATORS TESTS: Hallucination Detection
# ============================================================================

class TestHallucinationDetector:
    """Tests for Hallucination Detection"""

    def test_validate_valid_test(self, temp_phase1_json):
        """Test validation of valid test"""
        parser = Phase1Parser(temp_phase1_json)
        phase1 = parser.parse()

        detector = HallucinationDetector(phase1)

        # Create valid test
        test = TestCase(
            test_id="test_001",
            title="Valid test",
            description="This should pass",
            priority="high",
            algorithm_used="ep",
            elements_used=["elem_001"],
            test_steps=[
                TestStep(
                    step_number=1,
                    action="Enter username",
                    element_id="elem_001",
                    element_label="Username",
                    element_type="input",
                    locator="input[data-testid='username']",
                    locator_strategy="p3_testid",
                    locator_confidence=0.98,
                    input_value="testuser"
                )
            ],
            expected_result="User entered"
        )

        is_valid, errors = detector.validate_test(test)
        assert is_valid is True
        assert len(errors) == 0

    def test_detect_hallucinated_element(self, temp_phase1_json):
        """Test detection of fake element"""
        parser = Phase1Parser(temp_phase1_json)
        phase1 = parser.parse()

        detector = HallucinationDetector(phase1)

        # Create test with fake element_id
        test = TestCase(
            test_id="test_002",
            title="Hallucinated test",
            description="Contains fake element",
            priority="high",
            algorithm_used="ep",
            elements_used=["elem_999"],  # FAKE!
            test_steps=[
                TestStep(
                    step_number=1,
                    action="Click fake button",
                    element_id="elem_999",
                    element_label="Fake",
                    element_type="button",
                    locator="button[id='fake']",
                    locator_strategy="p1_role",
                    locator_confidence=0.5
                )
            ],
            expected_result="Nothing"
        )

        is_valid, errors = detector.validate_test(test)
        assert is_valid is False
        assert len(errors) > 0
        assert "elem_999" in errors[0]

    def test_batch_validation(self, temp_phase1_json):
        """Test validating batch of tests"""
        parser = Phase1Parser(temp_phase1_json)
        phase1 = parser.parse()

        detector = HallucinationDetector(phase1)

        # Create 5 valid tests and 2 invalid
        tests = []

        for i in range(5):
            tests.append(TestCase(
                test_id=f"test_{i:03d}",
                title="Valid",
                description="",
                priority="high",
                algorithm_used="ep",
                elements_used=["elem_001"],
                test_steps=[
                    TestStep(
                        step_number=1,
                        action="Enter",
                        element_id="elem_001",
                        element_label="Username",
                        element_type="input",
                        locator="input[data-testid='username']",
                        locator_strategy="p3_testid",
                        locator_confidence=0.98
                    )
                ],
                expected_result="OK"
            ))

        for i in range(2):
            tests.append(TestCase(
                test_id=f"test_invalid_{i:03d}",
                title="Invalid",
                description="",
                priority="high",
                algorithm_used="ep",
                elements_used=["elem_fake"],
                test_steps=[
                    TestStep(
                        step_number=1,
                        action="Click",
                        element_id="elem_fake",
                        element_label="Fake",
                        element_type="button",
                        locator="button[id='fake']",
                        locator_strategy="p1_role",
                        locator_confidence=0.5
                    )
                ],
                expected_result="Fail"
            ))

        result = detector.validate_test_batch(tests)
        assert result["total_tests"] == 7
        assert result["valid_tests"] == 5
        assert result["invalid_tests"] == 2
        assert result["hallucination_rate"] > 0


# ============================================================================
# ALGORITHM TESTS: EP & BVA
# ============================================================================

class TestEquivalencePartitioning:
    """Tests for Equivalence Partitioning Algorithm"""

    def test_generate_ep_tests(self, temp_phase1_json):
        """Test EP test generation"""
        parser = Phase1Parser(temp_phase1_json)
        parser.parse()

        ep = EquivalencePartitioning(parser)
        tests = ep.generate_ep_tests()

        assert len(tests) > 0
        assert all(t.algorithm_used == "ep" for t in tests)

    def test_ep_tests_not_hallucinated(self, temp_phase1_json):
        """Test that EP tests contain no hallucinations"""
        parser = Phase1Parser(temp_phase1_json)
        phase1 = parser.parse()

        ep = EquivalencePartitioning(parser)
        tests = ep.generate_ep_tests()

        detector = HallucinationDetector(phase1)
        result = detector.validate_test_batch(tests)

        assert result["hallucination_rate"] == 0.0


class TestBoundaryValueAnalysis:
    """Tests for Boundary Value Analysis Algorithm"""

    def test_generate_bva_tests(self, temp_phase1_json):
        """Test BVA test generation"""
        parser = Phase1Parser(temp_phase1_json)
        parser.parse()

        bva = BoundaryValueAnalysis(parser)
        tests = bva.generate_bva_tests()

        assert len(tests) > 0
        assert all(t.algorithm_used == "bva" for t in tests)

    def test_bva_tests_contain_boundaries(self, temp_phase1_json):
        """Test that BVA tests test boundaries"""
        parser = Phase1Parser(temp_phase1_json)
        parser.parse()

        bva = BoundaryValueAnalysis(parser)
        tests = bva.generate_bva_tests()

        # Check that tests cover boundary cases
        boundary_types = set()
        for test in tests:
            for edge_case in test.edge_cases_covered:
                boundary_types.add(edge_case)

        # Should have overflow/underflow tests
        assert any("overflow" in t or "underflow" in t
                   for t in boundary_types)


# ============================================================================
# TEST GENERATOR TESTS: Layer 2 Orchestrator
# ============================================================================

class TestTestGenerator:
    """Tests for Test Generator (Layer 2 Orchestrator)"""

    def test_generate_tests(self, temp_phase1_json):
        """Test full test generation pipeline"""
        parser = Phase1Parser(temp_phase1_json)
        parser.parse()

        generator = TestGenerator(parser)
        tests = generator.generate_tests()

        assert len(tests) >= 50
        assert all(isinstance(t, TestCase) for t in tests)

    def test_algorithm_stats(self, temp_phase1_json):
        """Test algorithm statistics"""
        parser = Phase1Parser(temp_phase1_json)
        parser.parse()

        generator = TestGenerator(parser)
        tests = generator.generate_tests()

        stats = generator.get_algorithm_stats(tests)

        assert stats["total_tests"] == len(tests)
        assert stats["ep_tests"] >= 0
        assert stats["bva_tests"] >= 0
        assert stats["state_tests"] >= 0
        assert (stats["ep_tests"] +
                stats["bva_tests"] +
                stats["state_tests"]) == stats["total_tests"]

    def test_no_hallucinations_in_generated(self, temp_phase1_json):
        """Test that generated tests have no hallucinations"""
        parser = Phase1Parser(temp_phase1_json)
        phase1 = parser.parse()

        generator = TestGenerator(parser)
        tests = generator.generate_tests()

        detector = HallucinationDetector(phase1)
        result = detector.validate_test_batch(tests)

        assert result["hallucination_rate"] == 0.0, \
            f"Found hallucinations: {result['errors_by_test']}"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """End-to-end integration tests"""

    def test_full_pipeline(self, temp_phase1_json):
        """Test complete Phase 1 -> Phase 2 pipeline"""
        # Parse Phase 1
        parser = Phase1Parser(temp_phase1_json)
        phase1 = parser.parse()

        assert phase1.total_elements == 3

        # Generate tests
        generator = TestGenerator(parser)
        tests = generator.generate_tests()

        assert len(tests) >= 50

        # Validate tests
        detector = HallucinationDetector(phase1)
        result = detector.validate_test_batch(tests)

        assert result["hallucination_rate"] == 0.0
        assert result["invalid_tests"] == 0

    def test_coverage_calculation(self, temp_phase1_json):
        """Test coverage calculation"""
        parser = Phase1Parser(temp_phase1_json)
        parser.parse()

        generator = TestGenerator(parser)
        tests = generator.generate_tests()

        # Get all tested elements
        tested_elements = set()
        for test in tests:
            tested_elements.update(test.elements_used)

        coverage = generator._calculate_coverage(tested_elements)
        assert coverage > 0
        assert coverage <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
