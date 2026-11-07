"""
ArduinoMate - Unified Test Runner
---------------------------------
Convenience script to run all unit and integration tests
without requiring external dependencies.
Usage:
    python tests/run_tests.py
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    """Discover and execute all test cases in the tests directory."""
    print("=" * 65)
    print("           RUNNING ARDUINOMATE AUTOMATED TEST SUITE          ")
    print("=" * 65)
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(PROJECT_ROOT / "tests"), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("=" * 65)
    if result.wasSuccessful():
        print(f"SUCCESS: All {result.testsRun} tests passed successfully!")
        sys.exit(0)
    else:
        print(f"FAILURE: {len(result.failures)} failures, {len(result.errors)} errors out of {result.testsRun} tests.")
        sys.exit(1)


if __name__ == "__main__":
    main()

