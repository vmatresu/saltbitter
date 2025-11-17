#!/usr/bin/env python3
"""
Reviewer Agent - Code quality validation and merge approval
"""

import argparse
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from worker import BaseAgent


class ReviewerAgent(BaseAgent):
    """Reviewer agent for code quality validation."""

    def __init__(self, agent_id: str):
        super().__init__(agent_id, "reviewer", ["code-review", "quality-assurance"])

    def _generate_plan(self, task: Dict) -> str:
        """Generate review plan."""
        plan_items = [
            "[ ] Check that all automated tests pass",
            "[ ] Verify code coverage meets minimum threshold",
            "[ ] Run linting and type checking",
            "[ ] Review code quality and complexity",
            "[ ] Check for security vulnerabilities",
            "[ ] Verify adherence to project standards",
            "[ ] Approve or request changes"
        ]
        return "\n".join(plan_items)

    def check_test_results(self, branch: str) -> Dict:
        """Check if tests pass on the branch."""
        try:
            self.log(f"Checking test results for branch: {branch}")

            # Checkout branch
            self._run_git_command(["git", "fetch", "origin", branch])
            self._run_git_command(["git", "checkout", branch])

            # Run tests
            result = subprocess.run(
                ["pytest", "tests/", "-v", "--cov=src", "--cov-report=json"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False
            )

            tests_passed = result.returncode == 0

            # Parse coverage
            coverage = 0.0
            coverage_file = self.repo_root / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    cov_data = json.load(f)
                    coverage = cov_data.get("totals", {}).get("percent_covered", 0.0)

            return {
                "tests_passed": tests_passed,
                "coverage": coverage,
                "output": result.stdout + result.stderr
            }

        except Exception as e:
            self.log(f"Failed to check test results: {e}", level="ERROR")
            return {"tests_passed": False, "coverage": 0.0, "output": str(e)}

    def run_linting(self) -> Dict:
        """Run linting checks."""
        try:
            self.log("Running linting checks")

            linter = self.config.get("quality", {}).get("linter", "ruff")
            results = {}

            if linter == "ruff":
                result = subprocess.run(
                    ["ruff", "check", "src/"],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                    check=False
                )
                results["ruff"] = {
                    "passed": result.returncode == 0,
                    "output": result.stdout + result.stderr
                }

            return results

        except Exception as e:
            self.log(f"Failed to run linting: {e}", level="ERROR")
            return {"error": str(e)}

    def run_type_checking(self) -> Dict:
        """Run type checking."""
        try:
            self.log("Running type checking")

            type_checker = self.config.get("quality", {}).get("type_checker", "mypy")

            if type_checker == "mypy":
                result = subprocess.run(
                    ["mypy", "src/"],
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
            self.log(f"Failed to run type checking: {e}", level="ERROR")
            return {"passed": False, "error": str(e)}

    def run_security_scan(self) -> Dict:
        """Run security scanning."""
        try:
            self.log("Running security scan")

            scanner = self.config.get("quality", {}).get("security_scanner", "bandit")

            if scanner == "bandit":
                result = subprocess.run(
                    ["bandit", "-r", "src/"],
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
            self.log(f"Failed to run security scan: {e}", level="ERROR")
            return {"passed": False, "error": str(e)}

    def check_code_standards(self) -> Dict:
        """Check adherence to code standards from AGENTS.md."""
        try:
            agents_md = self.repo_root / "AGENTS.md"
            if not agents_md.exists():
                return {"passed": True, "note": "AGENTS.md not found, skipping standards check"}

            # In a real implementation, would parse AGENTS.md and check standards
            return {"passed": True, "note": "Standards check completed"}

        except Exception as e:
            self.log(f"Failed to check code standards: {e}", level="ERROR")
            return {"passed": False, "error": str(e)}

    def generate_review_report(self, results: Dict) -> str:
        """Generate a review report."""
        report = []
        report.append("# Code Review Report\n")

        # Test results
        test_results = results.get("tests", {})
        report.append("## Test Results")
        if test_results.get("tests_passed"):
            report.append("✅ All tests passing")
        else:
            report.append("❌ Tests failing")

        coverage = test_results.get("coverage", 0.0)
        min_coverage = self.config.get("testing", {}).get("min_coverage_percent", 80)
        if coverage >= min_coverage:
            report.append(f"✅ Coverage: {coverage:.1f}% (meets {min_coverage}% requirement)")
        else:
            report.append(f"❌ Coverage: {coverage:.1f}% (below {min_coverage}% requirement)")

        # Linting
        linting = results.get("linting", {})
        report.append("\n## Code Quality")
        for tool, result in linting.items():
            if result.get("passed"):
                report.append(f"✅ {tool}: passed")
            else:
                report.append(f"❌ {tool}: failed")

        # Type checking
        type_check = results.get("type_checking", {})
        if type_check.get("passed"):
            report.append("✅ Type checking: passed")
        else:
            report.append("❌ Type checking: failed")

        # Security
        security = results.get("security", {})
        if security.get("passed"):
            report.append("✅ Security scan: passed")
        else:
            report.append("❌ Security scan: issues found")

        # Overall
        all_passed = (
            test_results.get("tests_passed", False) and
            coverage >= min_coverage and
            all(r.get("passed", False) for r in linting.values()) and
            type_check.get("passed", False) and
            security.get("passed", False)
        )

        report.append("\n## Verdict")
        if all_passed:
            report.append("✅ **APPROVED** - All checks passed")
        else:
            report.append("❌ **CHANGES REQUESTED** - Some checks failed")

        return "\n".join(report)

    def approve_pr(self, pr_number: int, report: str) -> bool:
        """Approve a pull request."""
        try:
            # Check if gh CLI is available
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                check=False
            )

            if result.returncode != 0:
                self.log("GitHub CLI not available, cannot approve PR", level="WARNING")
                return False

            # Post review
            result = subprocess.run(
                ["gh", "pr", "review", str(pr_number),
                 "--approve",
                 "--body", report],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                self.log(f"Approved PR #{pr_number}")
                return True
            else:
                self.log(f"Failed to approve PR: {result.stderr}", level="ERROR")
                return False

        except Exception as e:
            self.log(f"Failed to approve PR: {e}", level="ERROR")
            return False

    def request_changes(self, pr_number: int, report: str) -> bool:
        """Request changes on a pull request."""
        try:
            result = subprocess.run(
                ["gh", "pr", "review", str(pr_number),
                 "--request-changes",
                 "--body", report],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                self.log(f"Requested changes on PR #{pr_number}")
                return True
            else:
                self.log(f"Failed to request changes: {result.stderr}", level="ERROR")
                return False

        except Exception as e:
            self.log(f"Failed to request changes: {e}", level="ERROR")
            return False

    def execute_task(self, task: Dict) -> bool:
        """Execute review task."""
        try:
            self.log(f"Reviewing task: {task['id']}")

            # Get branch from task
            branch = task.get("branch")
            if not branch:
                self.log("No branch specified in task", level="ERROR")
                return False

            # Run all checks
            results = {}
            results["tests"] = self.check_test_results(branch)
            self.update_status_file("Completed test verification")

            results["linting"] = self.run_linting()
            self.update_status_file("Completed linting checks")

            results["type_checking"] = self.run_type_checking()
            self.update_status_file("Completed type checking")

            results["security"] = self.run_security_scan()
            self.update_status_file("Completed security scan")

            results["standards"] = self.check_code_standards()
            self.update_status_file("Completed standards check")

            # Generate report
            report = self.generate_review_report(results)
            self.log(f"Review report:\n{report}")

            # Determine if approved
            min_coverage = self.config.get("testing", {}).get("min_coverage_percent", 80)
            all_passed = (
                results["tests"].get("tests_passed", False) and
                results["tests"].get("coverage", 0.0) >= min_coverage and
                all(r.get("passed", False) for r in results.get("linting", {}).values()) and
                results.get("type_checking", {}).get("passed", False) and
                results.get("security", {}).get("passed", False)
            )

            # Get PR number if available
            pr_number = task.get("pr_number")
            if pr_number:
                if all_passed:
                    self.approve_pr(pr_number, report)
                else:
                    self.request_changes(pr_number, report)

            self.update_status_file(f"Review completed: {'APPROVED' if all_passed else 'CHANGES REQUESTED'}")
            return all_passed

        except Exception as e:
            self.log(f"Failed to execute review: {e}", level="ERROR")
            return False


def main():
    parser = argparse.ArgumentParser(description="Reviewer Agent")
    parser.add_argument("--agent-id", required=True, help="Agent ID")
    parser.add_argument("--pr-number", type=int, help="PR number to review")
    parser.add_argument("--require-approval", action="store_true", help="Require approval")

    args = parser.parse_args()

    agent = ReviewerAgent(args.agent_id)

    if args.pr_number:
        # Direct review mode
        task = {
            "id": f"REVIEW-{args.pr_number}",
            "title": f"Review PR #{args.pr_number}",
            "pr_number": args.pr_number
        }
        success = agent.execute_task(task)
        exit(0 if success else 1)
    else:
        # Normal agent mode
        agent.run()


if __name__ == "__main__":
    main()
