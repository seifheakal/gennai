"""
Phase 3: Layer 2 - Page Object Model Generator
Generates Page Object classes from Phase 1 elements
"""

import sys
from pathlib import Path

# Add phase2 directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "phase2"))

from typing import Dict, List
from phase2_phase1_parser import Phase1Parser


class PageObjectGenerator:
    """
    LAYER 2: Page Object Model Generator
    Creates POM classes with high-confidence locator strategies
    """

    def __init__(self, parser: Phase1Parser, language: str = "python"):
        """
        Initialize POM generator.

        Args:
            parser: Phase1Parser instance
            language: "python", "javascript", "java"
        """
        self.parser = parser
        self.language = language
        self.phase1 = parser.phase1_output

    def generate_page_objects(self) -> Dict[str, str]:
        """
        Generate all page object classes.

        Returns:
            Dictionary of {page_name: page_object_code}
        """
        page_objects = {}

        # Group elements by page (assuming element.page_name exists)
        elements_by_page = self._group_elements_by_page()

        for page_name, elements in elements_by_page.items():
            code = self._generate_page_class(page_name, elements)
            page_objects[page_name] = code

        return page_objects

    def _group_elements_by_page(self) -> Dict[str, List]:
        """Group elements by page/component"""
        elements_by_page = {}

        for elem in self.parser.get_all_elements():
            # Default to "HomePage" if no page specified
            page_name = getattr(elem, "page_name", "HomePage")

            if page_name not in elements_by_page:
                elements_by_page[page_name] = []

            elements_by_page[page_name].append(elem)

        return elements_by_page

    def _generate_page_class(self, page_name: str, elements: List) -> str:
        """
        Generate single page object class.

        Args:
            page_name: Name of page
            elements: List of Element objects

        Returns:
            Complete page object class code
        """
        # Convert camelCase to snake_case for method names
        class_name = self._to_class_name(page_name)

        code = f'''from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import time


class {class_name}:
    """Page Object for {page_name}"""

    # Page URL
    URL = "/{page_name.lower()}"

    # Element Locators (Using best strategy + confidence from Phase 1)
'''

        # Add element properties
        for elem in elements:
            code += self._generate_element_property(elem)

        # Add interaction methods
        for elem in elements:
            code += self._generate_action_methods(elem)

        # Add workflow methods
        code += self._generate_workflow_methods(elements)

        return code

    def _generate_element_property(self, elem) -> str:
        """
        Generate element property with best locator strategy.

        Args:
            elem: Element object from Phase 1

        Returns:
            Python property code
        """
        best_locator, confidence = elem.locator_confidence.best_strategy()

        if not best_locator:
            return ""

        # Extract locator strategy and value
        strategy, value = best_locator.split("::", 1) if "::" in best_locator else ("id", best_locator)

        # Map strategy to By enum
        by_enum = self._strategy_to_by(strategy)

        # Property name from label
        prop_name = self._to_property_name(elem.label)

        # Add wait strategy based on confidence
        if confidence and confidence > 0.9:
            wait_strategy = "EC.presence_of_element_located"
            wait_time = "5"
        elif confidence and confidence > 0.7:
            wait_strategy = "EC.presence_of_element_located"
            wait_time = "10"
        else:
            wait_strategy = "EC.presence_of_element_located"
            wait_time = "15"

        code = f'''
    @property
    def {prop_name}(self):
        """
        {elem.label} - Confidence: {confidence:.0%}
        Locator: {best_locator}
        """
        try:
            return WebDriverWait(self.driver, {wait_time}).until(
                {wait_strategy}(({by_enum}, "{value}"))
            )
        except TimeoutException:
            raise TimeoutException(f"Element '{prop_name}' not found within {wait_time}s")
'''

        return code

    def _generate_action_methods(self, elem) -> str:
        """Generate action methods for element based on type"""
        elem_type = elem.type
        prop_name = self._to_property_name(elem.label)
        method_name = self._to_method_name(elem.label)

        code = ""

        if elem_type in ["input", "textbox", "textarea"]:
            code += f'''
    def {method_name}_with(self, text: str):
        """Enter text in {elem.label}"""
        element = self.{prop_name}
        element.clear()
        element.send_keys(text)
        time.sleep(0.3)
        return self

    def clear_{method_name}(self):
        """Clear {elem.label}"""
        self.{prop_name}.clear()
        time.sleep(0.2)
        return self
'''

        elif elem_type == "button":
            code += f'''
    def click_{method_name}(self):
        """Click {elem.label}"""
        self.{prop_name}.click()
        time.sleep(1)
        return self
'''

        elif elem_type == "dropdown":
            code += f'''
    def select_{method_name}(self, option_text: str):
        """Select option from {elem.label}"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.select import Select
        
        element = self.{prop_name}
        select = Select(element)
        select.select_by_visible_text(option_text)
        time.sleep(0.5)
        return self

    def get_{method_name}_options(self):
        """Get all options from {elem.label}"""
        from selenium.webdriver.support.select import Select
        
        select = Select(self.{prop_name})
        return [opt.text for opt in select.options]
'''

        elif elem_type == "checkbox":
            code += f'''
    def check_{method_name}(self):
        """Check {elem.label}"""
        element = self.{prop_name}
        if not element.is_selected():
            element.click()
        time.sleep(0.3)
        return self

    def uncheck_{method_name}(self):
        """Uncheck {elem.label}"""
        element = self.{prop_name}
        if element.is_selected():
            element.click()
        time.sleep(0.3)
        return self
'''

        return code

    def _generate_workflow_methods(self, elements: List) -> str:
        """Generate workflow/composite action methods"""
        code = '''
    # Utility methods
    
    def wait_for_page_load(self, timeout: int = 10):
        """Wait for page to fully load"""
        time.sleep(2)  # Initial page load
        return self
    
    def get_page_title(self):
        """Get page title"""
        return self.driver.title
    
    def get_current_url(self):
        """Get current URL"""
        return self.driver.current_url
    
    def take_screenshot(self, name: str = "screenshot"):
        """Take screenshot"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.driver.save_screenshot(f"screenshots/{name}_{timestamp}.png")
        return self
'''
        return code

    def _strategy_to_by(self, strategy: str) -> str:
        """Convert strategy to Selenium By enum"""
        mapping = {
            "id": "By.ID",
            "xpath": "By.XPATH",
            "css": "By.CSS_SELECTOR",
            "name": "By.NAME",
            "class": "By.CLASS_NAME",
            "tag": "By.TAG_NAME",
            "link": "By.LINK_TEXT",
        }
        return mapping.get(strategy, "By.ID")

    def _to_class_name(self, name: str) -> str:
        """Convert name to class name (PascalCase)"""
        words = name.replace("-", " ").replace("_", " ").split()
        return "".join(w.capitalize() for w in words) + "Page"

    def _to_property_name(self, label: str) -> str:
        """Convert label to property name (snake_case)"""
        import re
        # Convert to lowercase and replace non-alphanumeric with underscore
        name = re.sub(r"[^a-zA-Z0-9]", "_", label).lower()
        # Remove leading/trailing underscores
        name = name.strip("_")
        return name

    def _to_method_name(self, label: str) -> str:
        """Convert label to method name"""
        import re
        # Convert to lowercase and replace spaces with underscores
        name = re.sub(r"[^a-zA-Z0-9]", "_", label).lower()
        # Remove leading/trailing underscores
        name = name.strip("_")
        return name

    def write_page_objects_to_files(self, output_dir: str = "pages"):
        """
        Write generated page objects to files.

        Args:
            output_dir: Directory to write page object files
        """
        from pathlib import Path

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Write __init__.py
        init_file = output_path / "__init__.py"
        init_file.write_text("# Page Objects\n")

        page_objects = self.generate_page_objects()

        for page_name, code in page_objects.items():
            file_name = self._to_file_name(page_name)
            file_path = output_path / f"{file_name}.py"

            # Add driver initialization to each class
            final_code = code.replace(
                "class ",
                "class ",
            )

            # Insert driver init
            final_code = final_code.replace(
                "Page Object",
                "Page Object\n\n    def __init__(self, driver):\n        self.driver = driver",
            )

            file_path.write_text(final_code)
            print(f"[OK] Created: {file_path}")

    def _to_file_name(self, page_name: str) -> str:
        """Convert page name to file name"""
        import re
        name = re.sub(r"[^a-zA-Z0-9]", "_", page_name).lower()
        return name.strip("_")
