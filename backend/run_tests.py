#!/usr/bin/env python
"""
Test runner script for the backend application.
Provides convenient shortcuts for common testing scenarios.
"""

import os
import sys
import subprocess


def run_command(cmd):
    """Execute a command and return the result"""
    print(f"\n🚀 Running: {cmd}")
    print("-" * 60)
    result = subprocess.run(cmd, shell=True)
    return result.returncode


def main():
    """Main test runner"""
    if len(sys.argv) < 2:
        print("""
📋 Backend Test Runner
====================

Usage: python run_tests.py [command] [options]

Commands:
  all         - Run all tests with coverage
  unit        - Run only unit tests
  integration - Run only integration tests
  fast        - Run tests without coverage (faster)
  watch       - Run tests in watch mode
  coverage    - Generate HTML coverage report
  specific    - Run specific test file (provide path)
  
Examples:
  python run_tests.py all
  python run_tests.py unit
  python run_tests.py specific tests/unit/test_models.py
  python run_tests.py watch
""")
        sys.exit(1)

    command = sys.argv[1]

    # Ensure we're in the correct directory
    if not os.path.exists("manage.py"):
        print("❌ Error: Must run from backend directory")
        sys.exit(1)

    # Base pytest command
    base_cmd = "uv run pytest"

    if command == "all":
        # Run all tests with coverage
        cmd = f"{base_cmd} -v --cov=app --cov-report=html --cov-report=term-missing"
        returncode = run_command(cmd)

    elif command == "unit":
        # Run only unit tests
        cmd = f"{base_cmd} tests/unit/ -v --cov=app --cov-report=term-missing"
        returncode = run_command(cmd)

    elif command == "integration":
        # Run only integration tests
        cmd = f"{base_cmd} tests/integration/ -v --cov=app --cov-report=term-missing"
        returncode = run_command(cmd)

    elif command == "fast":
        # Run tests without coverage (faster)
        cmd = f"{base_cmd} -v"
        returncode = run_command(cmd)

    elif command == "watch":
        # Run tests in watch mode
        cmd = f"{base_cmd} -v --tb=short -f"
        print("👀 Watching for changes... (Ctrl+C to stop)")
        returncode = run_command(cmd)

    elif command == "coverage":
        # Generate and open coverage report
        cmd = f"{base_cmd} --cov=app --cov-report=html --cov-report=term"
        returncode = run_command(cmd)
        if returncode == 0:
            print("\n📊 Opening coverage report...")
            subprocess.run("open htmlcov/index.html", shell=True)

    elif command == "specific":
        # Run specific test file
        if len(sys.argv) < 3:
            print("❌ Error: Please provide test file path")
            sys.exit(1)
        test_path = sys.argv[2]
        cmd = f"{base_cmd} {test_path} -v"
        returncode = run_command(cmd)

    else:
        print(f"❌ Error: Unknown command '{command}'")
        sys.exit(1)

    # Print summary
    print("\n" + "=" * 60)
    if returncode == 0:
        print("✅ Tests passed!")
    else:
        print("❌ Tests failed!")
    print("=" * 60)

    sys.exit(returncode)


if __name__ == "__main__":
    main()
