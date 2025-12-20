"""
Phase 1 Configuration Module

Defines exploration defaults and configuration management for the
Accessibility Parser (Layer 1) of the Web-Based Testing Agent.
"""

from dataclasses import dataclass
from typing import Literal

__version__ = "1.0.0"


@dataclass
class ExplorationConfig:
    """
    Configuration for Phase 1: Exploration & Knowledge Acquisition.
    
    All parameters are strict defaults for championship-level accuracy.
    """
    
    # Accuracy & Validation
    accuracy_mode: bool = True
    """Enable all validation layers (Layer A-E)"""
    
    validation_level: Literal["strict", "moderate", "minimal"] = "strict"
    """Validation strictness: strict (no compromises) | moderate | minimal"""
    
    # Coverage & Exploration
    coverage_threshold: float = 0.85
    """Stop exploration when 85% of elements discovered"""
    
    max_states: int = 10
    """Maximum state graph nodes before stopping (conservative for crawling)"""
    
    max_depth: int = 2
    """Maximum crawl depth from initial page"""
    
    exploration_depth: Literal["dynamic", "shallow", "deep"] = "dynamic"
    """Exploration strategy: dynamic (adjust based on findings) | shallow | deep"""
    
    # Crawler Settings
    enable_crawling: bool = True
    """Enable multi-page crawling (BFS exploration)"""
    
    wait_after_click_ms: int = 2000
    """Wait time after clicking element (for page settle)"""
    
    same_page_threshold: float = 0.8
    """DOM similarity threshold to consider same state (0-1)"""
    
    # Timeouts & Performance
    timeout_seconds: int = 120
    """Maximum exploration time: 2 minutes"""
    
    page_load_timeout_seconds: int = 30
    """Maximum time to wait for page load"""
    
    element_discovery_timeout_seconds: int = 10
    """Maximum time to wait for element to appear"""
    
    # Browser Configuration
    headless: bool = True
    """Run Playwright in headless mode (faster)"""
    
    browser_type: Literal["chromium", "firefox", "webkit"] = "chromium"
    """Browser to use for exploration"""
    
    # Output & Evidence
    take_screenshots: bool = True
    """Capture screenshots for validation evidence"""
    
    screenshot_dir: str = "screenshots"
    """Directory to store screenshot evidence"""
    
    generate_locator_confidence: bool = True
    """Calculate confidence scores for each locator"""
    
    # Locators & Strategies
    locator_strategies: int = 5
    """Number of locator strategies to generate per element"""
    
    # Validation Layers
    validate_accessibility: bool = True
    """Layer A: Parse accessibility tree"""
    
    validate_screenshot: bool = True
    """Layer B: Verify visibility via screenshots"""
    
    validate_interactivity: bool = True
    """Layer C: Test interactive capabilities"""
    
    validate_uniqueness: bool = True
    """Layer D: Confirm locator uniqueness"""
    
    validate_false_positives: bool = True
    """Layer E: Detect false positive interactive elements"""
    
    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    """Logging verbosity: DEBUG | INFO | WARNING | ERROR"""
    
    log_file: str = "phase1_exploration.log"
    """File to write structured logs"""
    
    # Advanced Options
    test_interactions_without_sideeffects: bool = True
    """Try hover/focus on elements without causing navigation/submission"""
    
    parallel_validation: bool = False
    """Run validation layers in parallel (experimental)"""
    
    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            "accuracy_mode": self.accuracy_mode,
            "validation_level": self.validation_level,
            "coverage_threshold": self.coverage_threshold,
            "max_states": self.max_states,
            "exploration_depth": self.exploration_depth,
            "timeout_seconds": self.timeout_seconds,
            "headless": self.headless,
            "browser_type": self.browser_type,
            "screenshot_dir": self.screenshot_dir,
            "locator_strategies": self.locator_strategies,
        }


# Default Configuration Instance
DEFAULT_CONFIG = ExplorationConfig()


def get_config() -> ExplorationConfig:
    """
    Get the default exploration configuration.
    
    Returns:
        ExplorationConfig: Default configuration with strict validation
    """
    return DEFAULT_CONFIG


def create_custom_config(**kwargs) -> ExplorationConfig:
    """
    Create custom configuration by overriding defaults.
    
    Example:
        config = create_custom_config(
            timeout_seconds=60,
            headless=False,
            validation_level="moderate"
        )
    
    Args:
        **kwargs: Configuration parameters to override
    
    Returns:
        ExplorationConfig: Custom configuration instance
    """
    config_dict = DEFAULT_CONFIG.__dict__.copy()
    config_dict.update(kwargs)
    return ExplorationConfig(**config_dict)
