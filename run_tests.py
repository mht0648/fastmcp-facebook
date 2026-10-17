#!/usr/bin/env python3
"""
Test Runner for fastmcp-facebook.
Executes all unit, contract, integration, and edge-case tests with structured reporting.

Usage:
    python3 run_tests.py
    python3 run_tests.py -v
"""

import sys
import os
import unittest
import time

# Ensure package directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    verbosity = 2 if "-v" in sys.argv or "--verbose" in sys.argv else 1
    print("=" * 70)
    print(" 🚀 fastmcp-facebook - Automated Test Suite")
    print("=" * 70)
    print(f"Python Version: {sys.version.split()[0]}")
    print(f"Platform:       {sys.platform}")
    print(f"Working Dir:    {os.getcwd()}")
    print("-" * 70)

    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests")
    suite = loader.discover(start_dir, pattern="test_*.py")

    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print(" 📊 Test Execution Summary")
    print("=" * 70)
    print(f"Total Tests Run:  {result.testsRun}")
    print(f"Passed:           {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures:         {len(result.failures)}")
    print(f"Errors:           {len(result.errors)}")
    print(f"Execution Time:   {elapsed:.3f} seconds")
    print("=" * 70)

    if result.wasSuccessful():
        print(" ✅ ALL TESTS PASSED SUCCESSFULLY!")
        return 0
    else:
        print(" ❌ TESTS FAILED. See details above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
