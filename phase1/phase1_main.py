"""
Phase 1 CLI Entry Point

Command-line interface for running Phase 1 exploration.

Usage:
    python main.py <url>                    # Explore URL
    python main.py --help                   # Show help
    python main.py --test                   # Run with test fixture
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from typing import Optional

from phase1_accessibility_parser import parse_accessibility_tree, AccessibilityParser
from phase1_config import create_custom_config, DEFAULT_CONFIG
from phase1_logger import setup_logging
from phase1_formatter import OutputFormatter
from phase1_sample_pages import get_fixture, list_fixtures

__version__ = "1.0.0"


# ============================================================================
# CLI ARGUMENT PARSER
# ============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Phase 1: Web Accessibility Parser & Element Discovery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py https://example.com
  python main.py --test simple_login
  python main.py --test complex_form --output result.json
  python main.py --headless false https://example.com
  python main.py https://example.com --timeout 60 --log-level DEBUG
        """
    )
    
    # Positional arguments
    parser.add_argument(
        "url",
        nargs="?",
        default=None,
        help="Target URL to explore (or use --test for mock data)"
    )
    
    # Test mode
    parser.add_argument(
        "--test",
        dest="test_fixture",
        default=None,
        choices=list_fixtures(),
        help=f"Run with test fixture instead of URL. Options: {', '.join(list_fixtures())}"
    )
    
    # Output options
    parser.add_argument(
        "-o", "--output",
        dest="output_file",
        default="phase1_output.json",
        help="Output file path (default: phase1_output.json)"
    )
    
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=["json", "summary", "pretty"],
        default="json",
        help="Output format (default: json)"
    )
    
    parser.add_argument(
        "--no-save",
        dest="save_file",
        action="store_false",
        default=True,
        help="Don't save output to file"
    )
    
    # Configuration options
    parser.add_argument(
        "--timeout",
        dest="timeout",
        type=int,
        default=120,
        help="Exploration timeout in seconds (default: 120)"
    )
    
    parser.add_argument(
        "--headless",
        dest="headless",
        type=lambda x: x.lower() in ("true", "yes", "1"),
        default=True,
        help="Run browser in headless mode (default: true)"
    )
    
    parser.add_argument(
        "--coverage",
        dest="coverage_threshold",
        type=float,
        default=0.85,
        help="Coverage threshold (0.0-1.0, default: 0.85)"
    )
    
    parser.add_argument(
        "--max-states",
        dest="max_states",
        type=int,
        default=20,
        help="Maximum states to explore (default: 20)"
    )
    
    # Logging options
    parser.add_argument(
        "--log-level",
        dest="log_level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        dest="log_file",
        default="phase1_exploration.log",
        help="Log file path (default: phase1_exploration.log)"
    )
    
    # Validation options
    parser.add_argument(
        "--strict",
        dest="strict_validation",
        action="store_true",
        default=True,
        help="Enable strict validation (default: enabled)"
    )
    
    # Version
    parser.add_argument(
        "--version",
        action="version",
        version=f"Phase 1 v{__version__}"
    )
    
    return parser


# ============================================================================
# MAIN CLI FUNCTION
# ============================================================================

async def main_async(args: argparse.Namespace) -> int:
    """
    Main async function for Phase 1 exploration.
    
    Args:
        args: Parsed command-line arguments
    
    Returns:
        int: Exit code (0 = success, 1 = failure)
    """
    # Setup logging
    setup_logging(
        log_level=args.log_level,
        log_file=args.log_file if args.save_file else None
    )
    
    print(f"🚀 Phase 1: Web Accessibility Parser v{__version__}")
    print("=" * 60)
    
    # Determine target URL
    if args.test_fixture:
        # Test mode: use fixture HTML
        print(f"📝 Test Mode: Using fixture '{args.test_fixture}'")
        html = get_fixture(args.test_fixture)
        
        # Load HTML into temp file and open
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html)
            temp_file = f.name
        
        url = f"file://{temp_file}"
        print(f"📍 Test HTML loaded: {temp_file}")
    
    elif args.url:
        # URL mode
        url = args.url
        if not url.startswith(("http://", "https://", "file://")):
            url = f"https://{url}"
        print(f"📍 Target URL: {url}")
    
    else:
        # No URL and no test mode
        print("❌ Error: Please provide a URL or use --test with a fixture name")
        print(f"   Available fixtures: {', '.join(list_fixtures())}")
        return 1
    
    try:
        # Create custom configuration
        config = create_custom_config(
            timeout_seconds=args.timeout,
            headless=args.headless,
            coverage_threshold=args.coverage_threshold,
            max_states=args.max_states,
            validation_level="strict" if args.strict_validation else "moderate",
            log_level=args.log_level,
        )
        
        print("\n⏳ Starting exploration...")
        print(f"⚙️  Config: timeout={args.timeout}s, headless={args.headless}, coverage={args.coverage_threshold:.1%}")
        
        # Run exploration
        output = await parse_accessibility_tree(url, config)
        
        # Format output
        print("\n✅ Exploration complete!")
        print(f"📊 Discovered {output.total_elements} interactive elements")
        print(f"📈 Coverage: {output.coverage_percentage:.1%}")
        print(f"⏱️  Time: {output.exploration_statistics.total_time_seconds:.2f}s")
        
        # Display summary
        if args.output_format == "summary" or args.output_format == "pretty":
            print("\n" + OutputFormatter.pretty_print(output))
        
        # Save output
        if args.save_file:
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if args.output_format == "json":
                content = OutputFormatter.to_json_string(output, indent=2)
            else:
                content = OutputFormatter.pretty_print(output)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"\n💾 Output saved: {output_path.absolute()}")
        
        return 0
    
    except KeyboardInterrupt:
        print("\n⚠️  Exploration cancelled by user")
        return 130
    
    except Exception as e:
        print(f"\n❌ Error during exploration: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


def main() -> int:
    """
    Main CLI entry point.
    
    Returns:
        int: Exit code
    """
    parser = create_parser()
    args = parser.parse_args()
    
    # Run async main
    try:
        exit_code = asyncio.run(main_async(args))
        return exit_code
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        return 130


# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    sys.exit(main())
