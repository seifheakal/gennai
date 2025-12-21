#!/usr/bin/env python
"""Test script to verify dynamic test generation"""

import sys
from pathlib import Path

# Add tests directory to path
sys.path.insert(0, str(Path(__file__).parent))

from test_generated_tests import ELEMENT_MAP, TestSuite

print(f"Elements loaded: {len(ELEMENT_MAP)}")
print(f"Element IDs: {list(ELEMENT_MAP.keys())}")
print(f"\nTests on TestSuite: {[m for m in dir(TestSuite) if m.startswith('test_')]}")
