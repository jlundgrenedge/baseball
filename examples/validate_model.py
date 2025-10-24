"""
Run validation tests for the batted ball physics model.

This script runs the full validation test suite to verify that
the simulator reproduces empirically known relationships.
"""

import sys
sys.path.insert(0, '..')

from batted_ball.validation import run_validation_tests


def main():
    """Run validation tests."""
    # Run all validation tests with verbose output
    results = run_validation_tests(verbose=True)

    # Return exit code based on test results
    if results['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
