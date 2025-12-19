"""
Phase 1 Pytest Configuration

Pytest configuration, fixtures, and plugins for Phase 1 tests.
"""

import pytest
import asyncio
import logging

from phase1_logger import setup_logging

__version__ = "1.0.0"


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest."""
    setup_logging("INFO", log_file="phase1_tests.log")


def pytest_collection_modifyitems(config, items):
    """Mark async tests."""
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


# ============================================================================
# MARKERS
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )


# ============================================================================
# SESSION FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for async tests."""
    if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# LOGGING FIXTURES
# ============================================================================

@pytest.fixture
def caplog_with_level(caplog):
    """Capture logs with debug level."""
    caplog.set_level(logging.DEBUG)
    return caplog
