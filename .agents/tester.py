#!/usr/bin/env python3
"""
Tester Agent - Automated test execution and validation
"""

import argparse
import json
import subprocess
from pathlib import Path
from typing import Dict
from worker import BaseAgent


class TesterAgent(BaseAgent):
    """Tester agent for automated testing."""

    def __init__(self, agent_id: str):
        super().__init__(agent_id, "tester", ["testing", "qa"])

    def _generate_plan(self, task: Dict) -> str:
        """Generate test plan."""
        plan_items = [
            "[ ] Run unit tests",
            "[ ] Run integration tests",
            "[ ] Run API tests (if applicable)",
            "[ ] Generate coverage report",
            "[ ] Update agent status with results"
        ]
        return "\n".join(plan_items)

    def run_unit_tests(self) -> Dict:
        """Run unit tests."""
        try:
            self.log("Running unit tests")
            result = subprocess.run(
                ["pytest", "tests/unit/", "-v", "--tb=short"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False
            )

            return {
                "passed": result.returncode == 0,
                "output": result.stdout + result.stderr
            }
        except Exception as e:
            self.log(f"Failed to run unit tests: {e}", level="ERROR")
            return {"passed": False, "error": str(e)}

    def run_integration_tests(self) -> Dict:
        """Run integration tests."""
        try:
            self.log("Running integration tests")
            result = subprocess.run(
                ["pytest", "tests/integration/", "-v", "--tb=short"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False
            )

            return {
                "passed": result.returncode == 0,
                "output": result.stdout + result.stderr
            }
        except Exception as e:
            self.log(f"Failed to run integration tests: {e}", level="ERROR")
            return {"passed": False, "error": str(e)}

    def generate_coverage_report(self) -> Dict:
        """Generate coverage report."""
        try:
            self.log("Generating coverage report")
            result = subprocess.run(
                ["pytest", "tests/", "--cov=src", "--cov-report=json", "--cov-report=term"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False
            )

            coverage_file = self.repo_root / "coverage.json"
            coverage = 0.0
            if coverage_file.exists():
                with open(coverage_file) as f:
                    cov_data = json.load(f)
                    coverage = cov_data.get("totals", {}).get("percent_covered", 0.0)

            return {
                "coverage": coverage,
                "output": result.stdout + result.stderr
            }
        except Exception as e:
            self.log(f"Failed to generate coverage: {e}", level="ERROR")
            return {"coverage": 0.0, "error": str(e)}

    def execute_task(self, task: Dict) -> bool:
        """Execute testing task."""
        try:
            self.log(f"Testing task: {task['id']}")

            # Run unit tests
            unit_results = self.run_unit_tests()
            self.update_status_file(f"Unit tests: {'✓' if unit_results['passed'] else '✗'}")

            # Run integration tests
            integration_results = self.run_integration_tests()
            self.update_status_file(f"Integration tests: {'✓' if integration_results['passed'] else '✗'}")

            # Generate coverage
            coverage_results = self.generate_coverage_report()
            self.update_status_file(f"Coverage: {coverage_results['coverage']:.1f}%")

            # All tests must pass
            all_passed = unit_results["passed"] and integration_results["passed"]

            return all_passed

        except Exception as e:
            self.log(f"Failed to execute testing: {e}", level="ERROR")
            return False


def main():
    parser = argparse.ArgumentParser(description="Tester Agent")
    parser.add_argument("--agent-id", required=True, help="Agent ID")
    args = parser.parse_args()

    agent = TesterAgent(args.agent_id)
    agent.run()


if __name__ == "__main__":
    main()
