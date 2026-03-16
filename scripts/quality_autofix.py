#!/usr/bin/env python
"""Quality autofix and test runner script.

Runs:
1. ruff --fix (lint fixes)
2. isort (import sorting)
3. black (code formatting)
4. pytest (unit tests with coverage)
5. Generates comprehensive quality report
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Tuple, List, Dict


class QualityRunner:
    """Orchestrates quality checks and autofix operations."""

    def __init__(self):
        self.workspace_root = Path.cwd()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "summary": {},
        }
        self.all_passed = True

    def run_ruff_fix(self) -> bool:
        """Run ruff --fix to fix linting issues."""
        print("\n" + "=" * 80)
        print("Step 1/5: Running Ruff Linter (with autofix)")
        print("=" * 80)
        
        try:
            result = subprocess.run(
                ["ruff", "check", "--fix", "apps", "tests", "config"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            passed = result.returncode == 0
            self.results["checks"]["ruff"] = {
                "status": "PASS" if passed else "WARN",
                "return_code": result.returncode,
                "output": result.stdout[:500],  # First 500 chars
            }
            
            if not passed:
                print("[WARN] Ruff found some issues (may be fixed with --fix)")
            else:
                print("[PASS] Ruff check passed")
            
            return True  # Don't fail on ruff warnings
        except FileNotFoundError:
            print("[SKIP] Ruff not installed")
            self.results["checks"]["ruff"] = {"status": "SKIP", "reason": "Not installed"}
            return True
        except subprocess.TimeoutExpired:
            print("[TIMEOUT] Ruff check timed out")
            self.results["checks"]["ruff"] = {"status": "FAIL", "reason": "Timeout"}
            self.all_passed = False
            return False

    def run_isort(self) -> bool:
        """Run isort to sort imports."""
        print("\n" + "=" * 80)
        print("Step 2/5: Running isort (import sorting)")
        print("=" * 80)
        
        try:
            result = subprocess.run(
                ["isort", "apps", "tests", "config", "--check-only", "--diff"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            
            if result.returncode != 0:
                print("[FIXING] Running isort with modifications...")
                result = subprocess.run(
                    ["isort", "apps", "tests", "config"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                print(result.stdout)
            
            passed = result.returncode == 0
            self.results["checks"]["isort"] = {
                "status": "PASS" if passed else "FIXED",
                "return_code": result.returncode,
            }
            
            print("[PASS] isort completed")
            return True

        except FileNotFoundError:
            print("[SKIP] isort not installed")
            self.results["checks"]["isort"] = {"status": "SKIP", "reason": "Not installed"}
            return True
        except subprocess.TimeoutExpired:
            print("[TIMEOUT] isort timed out")
            self.results["checks"]["isort"] = {"status": "FAIL", "reason": "Timeout"}
            self.all_passed = False
            return False

    def run_black(self) -> bool:
        """Run black code formatter."""
        print("\n" + "=" * 80)
        print("Step 3/5: Running Black (code formatting)")
        print("=" * 80)
        
        try:
            result = subprocess.run(
                ["black", "apps", "tests", "config", "--line-length", "100"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            print(result.stdout)
            
            passed = result.returncode == 0
            self.results["checks"]["black"] = {
                "status": "PASS" if passed else "FIXED",
                "return_code": result.returncode,
            }
            
            print("[PASS] Black formatting completed")
            return True

        except FileNotFoundError:
            print("[SKIP] Black not installed")
            self.results["checks"]["black"] = {"status": "SKIP", "reason": "Not installed"}
            return True
        except subprocess.TimeoutExpired:
            print("[TIMEOUT] Black timed out")
            self.results["checks"]["black"] = {"status": "FAIL", "reason": "Timeout"}
            self.all_passed = False
            return False

    def run_pytest(self) -> bool:
        """Run pytest with coverage reporting."""
        print("\n" + "=" * 80)
        print("Step 4/5: Running Pytest (unit tests with coverage)")
        print("=" * 80)
        
        try:
            result = subprocess.run(
                [
                    "pytest",
                    "--cov=apps",
                    "--cov-report=html",
                    "--cov-report=term-missing",
                    "--cov-report=json",
                    "--cov-fail-under=80",
                    "-v",
                    "--tb=short",
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )
            
            # Print last 100 lines of output
            output_lines = result.stdout.split("\n")
            print("\n".join(output_lines[-100:]))
            
            passed = result.returncode == 0
            self.results["checks"]["pytest"] = {
                "status": "PASS" if passed else "FAIL",
                "return_code": result.returncode,
                "total_tests": self._count_tests(result.stdout),
                "passed_tests": self._count_passed_tests(result.stdout),
            }
            
            if not passed:
                print("\n[FAIL] Some tests failed")
                self.all_passed = False
                if result.stderr:
                    print("STDERR:", result.stderr[-500:])  # Last 500 chars
            else:
                print("\n[PASS] All tests passed with >=80% coverage")
            
            return passed

        except FileNotFoundError:
            print("[SKIP] Pytest not installed")
            self.results["checks"]["pytest"] = {"status": "SKIP", "reason": "Not installed"}
            return False
        except subprocess.TimeoutExpired:
            print("[TIMEOUT] Pytest timed out")
            self.results["checks"]["pytest"] = {"status": "FAIL", "reason": "Timeout"}
            self.all_passed = False
            return False

    def _count_tests(self, output: str) -> int:
        """Extract test count from pytest output."""
        for line in output.split("\n"):
            if "passed" in line or "failed" in line:
                try:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if "passed" in part and i > 0:
                            return int(parts[i - 1])
                except (ValueError, IndexError):
                    pass
        return 0

    def _count_passed_tests(self, output: str) -> int:
        """Extract passed test count from pytest output."""
        return self._count_tests(output)  # Simplified

    def generate_report(self) -> None:
        """Generate quality report."""
        print("\n" + "=" * 80)
        print("Step 5/5: Generating Quality Report")
        print("=" * 80)
        
        summary = {
            "total_checks": len(self.results["checks"]),
            "passed_checks": sum(
                1 for c in self.results["checks"].values()
                if c.get("status") == "PASS"
            ),
            "overall_status": "PASS" if self.all_passed else "FAIL",
            "timestamp": datetime.now().isoformat(),
        }
        
        self.results["summary"] = summary
        
        print("\n" + "=" * 80)
        print("QUALITY ASSURANCE REPORT")
        print("=" * 80)
        print(f"\nTimestamp: {summary['timestamp']}")
        print(f"Overall Status: {summary['overall_status']}")
        print(f"Checks Passed: {summary['passed_checks']}/{summary['total_checks']}")
        
        print("\nDetailed Results:")
        print("-" * 80)
        
        for check_name, check_result in self.results["checks"].items():
            status = check_result.get("status", "UNKNOWN")
            print(f"\n{check_name.upper():20} [{status}]")
            if status == "FAIL":
                print(f"  Return Code: {check_result.get('return_code')}")
                if "reason" in check_result:
                    print(f"  Reason: {check_result['reason']}")
            elif status == "PASS" and "total_tests" in check_result:
                print(
                    f"  Tests: {check_result['passed_tests']}/{check_result['total_tests']}"
                )
        
        print("\n" + "=" * 80)
        print(f"Overall Result: {summary['overall_status']}")
        print("=" * 80)
        
        # Save report as JSON
        report_file = self.workspace_root / "quality_report.json"
        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\nDetailed report saved to: {report_file}")

    def run(self) -> int:
        """Execute all quality checks."""
        print("\n" + "=" * 80)
        print("QUALITY AUTOFIX AND TEST RUNNER")
        print("=" * 80)
        print(f"Workspace: {self.workspace_root}")
        print(f"Started: {datetime.now().isoformat()}")
        
        # Run all checks
        self.run_ruff_fix()
        self.run_isort()
        self.run_black()
        pytest_passed = self.run_pytest()
        
        self.generate_report()
        
        # Return exit code
        return 0 if (self.all_passed and pytest_passed) else 1


def main():
    """Main entry point."""
    runner = QualityRunner()
    exit_code = runner.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
