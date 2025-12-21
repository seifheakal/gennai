#!/usr/bin/env python
"""Test runner with argument parsing"""

import argparse
import os
import sys
import pytest


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Run E2E tests")
    
    parser.add_argument(
        "--browser",
        choices=["chrome", "firefox", "edge"],
        default="chrome",
        help="Browser to use"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode"
    )
    
    parser.add_argument(
        "--url",
        default="http://localhost:8080",
        help="Base URL for tests"
    )
    
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="Number of parallel workers"
    )
    
    parser.add_argument(
        "--tag",
        choices=["smoke", "regression", "critical"],
        help="Run tests with specific tag"
    )
    
    parser.add_argument(
        "--report",
        default="html",
        choices=["html", "junit", "json"],
        help="Report format"
    )
    
    args = parser.parse_args()
    
    # Set environment variables
    os.environ["BROWSER"] = args.browser
    os.environ["HEADLESS"] = str(args.headless).lower()
    os.environ["BASE_URL"] = args.url
    
    # Build pytest arguments
    pytest_args = ["tests", "-v", "--tb=short"]
    
    # Add parallel execution if requested
    if args.parallel > 1:
        pytest_args.extend(["-n", str(args.parallel)])
    
    # Add tag filter
    if args.tag:
        pytest_args.extend(["-m", args.tag])
    
    # Add reporting
    if args.report == "html":
        pytest_args.extend(["--html=report.html", "--self-contained-html"])
    elif args.report == "junit":
        pytest_args.extend(["--junit-xml=report.xml"])
    elif args.report == "json":
        pytest_args.extend(["--json-report", "--json-report-file=report.json"])
    
    # Run tests
    print(f"🚀 Running tests with: {' '.join(pytest_args)}")
    exit_code = pytest.main(pytest_args)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
