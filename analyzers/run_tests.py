#!/usr/bin/env python3
"""
Test runner for TrBotMaster parser tests.
Provides detailed reporting and statistics.
"""

import sys
import os
import time
from pathlib import Path
import subprocess


def main():
    """Run all parser tests with detailed reporting."""
    print("🚀 Starting TrBotMaster Parser Test Suite")
    print("=" * 50)

    # Add project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("❌ pytest is not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest"])
        import pytest

    # Check if all required dependencies are available
    try:
        import bs4

        print("✅ BeautifulSoup4 is available")
    except ImportError:
        print("❌ BeautifulSoup4 is not installed")
        return 1

    # Set up test environment
    os.chdir(project_root)

    # Test arguments
    test_args = [
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--durations=10",  # Show 10 slowest tests
        "--strict-markers",  # Strict marker checking
        "tests/",  # Test directory
    ]

    # Add coverage if available
    try:
        import coverage

        test_args.extend(["--cov=parsers", "--cov-report=term-missing"])
        print("✅ Coverage reporting enabled")
    except ImportError:
        print("ℹ️  Coverage not available (install with: pip install pytest-cov)")

    print(f"\n🧪 Running tests from: {project_root}")
    print(f"📁 Test directory: {project_root / 'tests'}")
    print(f"📄 Test pages: {project_root / 'parsers' / 'parser-test-pages'}")

    # Check if test pages exist
    test_pages_dir = project_root / "parsers" / "parser-test-pages"
    if not test_pages_dir.exists():
        print(f"❌ Test pages directory not found: {test_pages_dir}")
        return 1

    # Count test files
    test_files = list(Path("tests").glob("test_*.py"))
    print(f"📋 Found {len(test_files)} test files")

    # Count HTML test pages
    html_files = list(test_pages_dir.rglob("*.html"))
    print(f"🌐 Found {len(html_files)} HTML test pages")

    print("\n" + "=" * 50)
    print("🏃 Running tests...")

    start_time = time.time()

    # Run pytest
    exit_code = pytest.main(test_args)

    end_time = time.time()
    duration = end_time - start_time

    print("\n" + "=" * 50)
    print(f"⏱️  Total test duration: {duration:.2f} seconds")

    if exit_code == 0:
        print("✅ All tests passed successfully!")
    else:
        print("❌ Some tests failed.")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
