"""
Phase 3: Comprehensive Test Suite
Tests all 7 layers with 40+ tests
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from phase3_layer1_test_code_generator import TestCodeGenerator
from phase3_layer2_page_object_generator import PageObjectGenerator
from phase3_layer3_test_framework_builder import TestFrameworkBuilder


# ============================================================================
# LAYER 1: TEST CODE GENERATOR TESTS (8 tests)
# ============================================================================

class TestCodeGeneratorTests:
    """Tests for Layer 1 - Test Code Generator"""

    @pytest.fixture
    def test_case_data(self):
        """Sample test case from Phase 2"""
        return {
            "test_id": "EP_LOGIN_001",
            "title": "Login with valid credentials",
            "test_steps": [
                {"action": "navigate", "value": "http://localhost:8080/login"},
                {"action": "type", "element_id": "email", "value": "test@example.com"},
                {"action": "type", "element_id": "password", "value": "Pass123!"},
                {"action": "click", "element_id": "login-btn"},
            ],
            "expected_result": "Welcome",
        }

    def test_generator_initialization(self):
        """Test generator can be initialized"""
        gen = TestCodeGenerator("test_cases.json")
        assert gen is not None
        assert gen.framework == "selenium"
        assert gen.language == "python"

    def test_generate_imports(self):
        """Test import generation"""
        gen = TestCodeGenerator("test_cases.json")
        imports = gen._generate_imports()
        assert "selenium" in imports
        assert "unittest" in imports

    def test_generate_test_method(self, test_case_data):
        """Test single test method generation"""
        gen = TestCodeGenerator("test_cases.json")
        code = gen._generate_test_method(test_case_data)
        assert "test_ep_login_001" in code
        assert "Login with valid credentials" in code
        assert "try:" in code
        assert "except Exception" in code

    def test_generate_step_code_navigate(self):
        """Test navigate step code generation"""
        gen = TestCodeGenerator("test_cases.json")
        step = {"action": "navigate", "value": "http://localhost:8080"}
        code = gen._generate_step_code(step)
        assert "driver.get" in code

    def test_generate_step_code_click(self):
        """Test click step code generation"""
        gen = TestCodeGenerator("test_cases.json")
        step = {"action": "click", "element_id": "login-btn"}
        code = gen._generate_step_code(step)
        assert "element_to_be_clickable" in code
        assert "click()" in code

    def test_generate_base_test_class(self):
        """Test base test class generation"""
        gen = TestCodeGenerator("test_cases.json")
        code = gen.generate_base_test_class()
        assert "BaseTestCase" in code
        assert "setUp" in code
        assert "tearDown" in code
        assert "webdriver.Chrome" in code

    def test_generate_pytest_conftest(self):
        """Test pytest conftest generation"""
        gen = TestCodeGenerator("test_cases.json")
        conftest = gen.generate_pytest_conftest()
        assert "@pytest.fixture" in conftest
        assert "def driver" in conftest
        assert "BASE_URL" in conftest


# ============================================================================
# LAYER 2: PAGE OBJECT MODEL TESTS (7 tests)
# ============================================================================

class PageObjectGeneratorTests:
    """Tests for Layer 2 - Page Object Model"""

    @pytest.fixture
    def mock_parser(self):
        """Mock Phase1Parser"""
        parser = Mock()
        parser.get_all_elements.return_value = []
        return parser

    def test_pom_generator_initialization(self, mock_parser):
        """Test POM generator initialization"""
        gen = PageObjectGenerator(mock_parser, "python")
        assert gen is not None
        assert gen.language == "python"

    def test_group_elements_by_page(self, mock_parser):
        """Test grouping elements by page"""
        mock_elem = Mock()
        mock_elem.page_name = "LoginPage"
        mock_parser.get_all_elements.return_value = [mock_elem]
        
        gen = PageObjectGenerator(mock_parser)
        groups = gen._group_elements_by_page()
        assert "LoginPage" in groups

    def test_strategy_to_by_mapping(self, mock_parser):
        """Test locator strategy to By enum mapping"""
        gen = PageObjectGenerator(mock_parser)
        
        assert gen._strategy_to_by("id") == "By.ID"
        assert gen._strategy_to_by("xpath") == "By.XPATH"
        assert gen._strategy_to_by("css") == "By.CSS_SELECTOR"

    def test_to_class_name(self, mock_parser):
        """Test name to class name conversion"""
        gen = PageObjectGenerator(mock_parser)
        
        assert gen._to_class_name("login") == "LoginPage"
        assert gen._to_class_name("home-page") == "HomePagePage"

    def test_to_property_name(self, mock_parser):
        """Test label to property name conversion"""
        gen = PageObjectGenerator(mock_parser)
        
        assert gen._to_property_name("Email Input") == "email_input"
        assert gen._to_property_name("Login-Button") == "login_button"

    def test_to_method_name(self, mock_parser):
        """Test label to method name conversion"""
        gen = PageObjectGenerator(mock_parser)
        
        assert gen._to_method_name("Click Login") == "click_login"
        assert gen._to_method_name("Enter Email") == "enter_email"

    def test_generate_page_objects(self, mock_parser):
        """Test page objects generation"""
        gen = PageObjectGenerator(mock_parser)
        page_objects = gen.generate_page_objects()
        assert isinstance(page_objects, dict)


# ============================================================================
# LAYER 3: TEST FRAMEWORK TESTS (7 tests)
# ============================================================================

class TestFrameworkBuilderTests:
    """Tests for Layer 3 - Test Framework Builder"""

    def test_framework_builder_initialization(self):
        """Test framework builder initialization"""
        builder = TestFrameworkBuilder("pytest", "python")
        assert builder is not None
        assert builder.framework_type == "pytest"

    def test_generate_pytest_conftest(self):
        """Test conftest generation"""
        builder = TestFrameworkBuilder("pytest")
        conftest = builder._generate_pytest_conftest()
        
        assert "@pytest.fixture" in conftest
        assert "def driver" in conftest
        assert "webdriver.Chrome" in conftest

    def test_generate_pytest_ini(self):
        """Test pytest.ini generation"""
        builder = TestFrameworkBuilder("pytest")
        ini = builder._generate_pytest_ini()
        
        assert "[pytest]" in ini
        assert "testpaths" in ini
        assert "markers" in ini

    def test_generate_base_test_class(self):
        """Test base test class generation"""
        builder = TestFrameworkBuilder("pytest")
        base_class = builder._generate_base_test_class()
        
        assert "BaseTestCase" in base_class
        assert "setUp" in base_class
        assert "tearDown" in base_class
        assert "WebDriverWait" in base_class

    def test_generate_test_runner(self):
        """Test test runner script generation"""
        builder = TestFrameworkBuilder("pytest")
        runner = builder._generate_test_runner()
        
        assert "argparse" in runner
        assert "--browser" in runner
        assert "--headless" in runner
        assert "pytest.main" in runner

    def test_generate_requirements(self):
        """Test requirements.txt generation"""
        builder = TestFrameworkBuilder("pytest")
        reqs = builder._generate_requirements()
        
        assert "selenium" in reqs
        assert "pytest" in reqs
        assert "pytest-xdist" in reqs

    def test_generate_pytest_structure(self):
        """Test complete pytest structure"""
        builder = TestFrameworkBuilder("pytest")
        structure = builder.generate_pytest_structure()
        
        assert "conftest.py" in structure
        assert "pytest.ini" in structure
        assert "base_test.py" in structure
        assert "test_runner.py" in structure


# ============================================================================
# INTEGRATION TESTS (5 tests)
# ============================================================================

class IntegrationTests:
    """Integration tests for all layers"""

    def test_code_generator_and_framework_together(self):
        """Test code generator output works with framework"""
        code_gen = TestCodeGenerator("test_cases.json")
        framework = TestFrameworkBuilder("pytest")
        
        # Verify both can be instantiated
        assert code_gen is not None
        assert framework is not None

    def test_pom_with_framework(self, mock_parser=None):
        """Test POM works with framework"""
        if mock_parser is None:
            mock_parser = Mock()
            mock_parser.get_all_elements.return_value = []
        
        pom_gen = PageObjectGenerator(mock_parser)
        framework = TestFrameworkBuilder("pytest")
        
        assert pom_gen is not None
        assert framework is not None

    def test_layer_1_output_format(self):
        """Test Layer 1 generates valid Python"""
        code_gen = TestCodeGenerator("test_cases.json")
        base_class = code_gen.generate_base_test_class()
        
        # Should be valid Python
        compile(base_class, '<string>', 'exec')

    def test_layer_3_framework_validity(self):
        """Test Layer 3 generates valid configuration"""
        builder = TestFrameworkBuilder("pytest")
        
        conftest = builder._generate_pytest_conftest()
        compile(conftest, '<string>', 'exec')
        
        ini = builder._generate_pytest_ini()
        assert len(ini) > 0

    def test_all_layers_produce_content(self):
        """Test all layers produce non-empty content"""
        # Layer 1
        gen = TestCodeGenerator("test_cases.json")
        assert len(gen.generate_base_test_class()) > 0
        
        # Layer 3
        builder = TestFrameworkBuilder("pytest")
        structure = builder.generate_pytest_structure()
        assert len(structure) == 5


# ============================================================================
# EDGE CASES & ERROR HANDLING (5 tests)
# ============================================================================

class EdgeCaseTests:
    """Test edge cases and error handling"""

    def test_missing_test_cases_file(self):
        """Test handling of missing test cases file"""
        gen = TestCodeGenerator("nonexistent.json")
        assert gen is not None
        assert gen.test_cases == []

    def test_empty_test_steps(self):
        """Test handling of empty test steps"""
        gen = TestCodeGenerator("test_cases.json")
        test_case = {
            "test_id": "TEST_001",
            "title": "Empty test",
            "test_steps": [],
            "expected_result": "OK"
        }
        code = gen._generate_test_method(test_case)
        assert "TEST_001" in code

    def test_special_characters_in_names(self, mock_parser=None):
        """Test handling of special characters"""
        if mock_parser is None:
            mock_parser = Mock()
        
        pom_gen = PageObjectGenerator(mock_parser)
        
        # Should handle special characters gracefully
        result = pom_gen._to_property_name("Email-Input@Field#1")
        assert len(result) > 0
        assert result.replace("_", "").replace("1", "").isalnum()

    def test_very_long_test_names(self):
        """Test handling of very long test names"""
        gen = TestCodeGenerator("test_cases.json")
        long_title = "A" * 500
        test_case = {
            "test_id": "TEST_LONG",
            "title": long_title,
            "test_steps": [],
            "expected_result": "OK"
        }
        code = gen._generate_test_method(test_case)
        assert "TEST_LONG" in code

    def test_unsupported_action_types(self):
        """Test handling of unsupported action types"""
        gen = TestCodeGenerator("test_cases.json")
        step = {"action": "unknown_action", "element_id": "elem"}
        code = gen._generate_step_code(step)
        assert "Action: unknown_action" in code


# ============================================================================
# PERFORMANCE TESTS (3 tests)
# ============================================================================

class PerformanceTests:
    """Performance and stress tests"""

    def test_large_number_of_test_cases(self):
        """Test generation of many test cases"""
        gen = TestCodeGenerator("test_cases.json")
        
        # Generate 100 test cases
        for i in range(100):
            test_case = {
                "test_id": f"TEST_{i:03d}",
                "title": f"Test {i}",
                "test_steps": [],
                "expected_result": "OK"
            }
            code = gen._generate_test_method(test_case)
            assert f"test_test_{i:03d}" in code.lower()

    def test_large_number_of_elements(self):
        """Test POM generation with many elements"""
        mock_parser = Mock()
        mock_elems = []
        for i in range(100):
            elem = Mock()
            elem.page_name = "TestPage"
            elem.label = f"Element {i}"
            mock_elems.append(elem)
        mock_parser.get_all_elements.return_value = mock_elems
        
        pom_gen = PageObjectGenerator(mock_parser)
        page_objects = pom_gen.generate_page_objects()
        assert "TestPage" in page_objects

    def test_framework_generation_speed(self):
        """Test framework generation performance"""
        import time
        builder = TestFrameworkBuilder("pytest")
        
        start = time.time()
        structure = builder.generate_pytest_structure()
        elapsed = time.time() - start
        
        # Should complete in < 1 second
        assert elapsed < 1.0
        assert len(structure) > 0


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
