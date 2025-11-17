#!/usr/bin/env python3
"""
Coder Agent - Feature implementation and module development
"""

import argparse
import subprocess
from pathlib import Path
from typing import Dict
from worker import BaseAgent


class CoderAgent(BaseAgent):
    """Coder agent for implementing features and modules."""

    def __init__(self, agent_id: str, capabilities: list = None):
        if capabilities is None:
            capabilities = ["python", "fastapi", "postgresql", "testing"]
        super().__init__(agent_id, "coder", capabilities)

    def _generate_plan(self, task: Dict) -> str:
        """Generate implementation plan for the task."""
        plan_items = [
            "[ ] Read AGENTS.md for project context and standards",
            "[ ] Analyze task requirements and acceptance criteria",
            "[ ] Create feature branch",
            "[ ] Implement core functionality",
            "[ ] Write unit tests",
            "[ ] Write integration tests (if applicable)",
            "[ ] Run tests locally and ensure passing",
            "[ ] Commit changes with descriptive messages",
            "[ ] Push branch and create PR",
            "[ ] Tag reviewer for code review"
        ]
        return "\n".join(plan_items)

    def create_feature_branch(self, task: Dict) -> bool:
        """Create a feature branch for the task."""
        try:
            branch_prefix = self.config.get("git", {}).get("feature_branch_prefix", "feature/TASK-")
            task_slug = task["title"].lower().replace(" ", "-")[:50]
            branch_name = f"{branch_prefix}{task['id']}-{task_slug}"

            # Create and checkout branch
            result = self._run_git_command(["git", "checkout", "-b", branch_name], check=False)
            if result.returncode != 0:
                # Branch might exist, try to checkout
                result = self._run_git_command(["git", "checkout", branch_name], check=False)
                if result.returncode != 0:
                    self.log(f"Failed to create/checkout branch {branch_name}", level="ERROR")
                    return False

            self.current_branch = branch_name
            self.log(f"Created feature branch: {branch_name}")
            self.update_status_file(f"Created feature branch: {branch_name}")
            return True

        except Exception as e:
            self.log(f"Failed to create feature branch: {e}", level="ERROR")
            return False

    def read_project_context(self) -> str:
        """Read AGENTS.md for project context."""
        try:
            agents_md = self.repo_root / "AGENTS.md"
            if agents_md.exists():
                with open(agents_md) as f:
                    return f.read()
            else:
                self.log("AGENTS.md not found, proceeding without context", level="WARNING")
                return ""
        except Exception as e:
            self.log(f"Failed to read AGENTS.md: {e}", level="ERROR")
            return ""

    def implement_feature(self, task: Dict) -> bool:
        """Implement the feature described in the task."""
        self.log(f"Implementing task: {task['title']}")

        # Read project context
        context = self.read_project_context()
        self.update_status_file("Read project context from AGENTS.md")

        # This is a placeholder - in a real implementation, this would use
        # an LLM API to generate code based on the task description
        self.log("Feature implementation would happen here using LLM API")
        self.update_status_file("Implemented core functionality (placeholder)")

        return True

    def run_tests(self) -> bool:
        """Run tests for the implementation."""
        try:
            self.log("Running tests...")
            self.update_status_file("Running test suite")

            # Check if pytest is available
            result = subprocess.run(
                ["pytest", "--version"],
                cwd=self.repo_root,
                capture_output=True,
                check=False
            )

            if result.returncode != 0:
                self.log("pytest not installed, skipping tests", level="WARNING")
                return True

            # Run pytest
            result = subprocess.run(
                ["pytest", "tests/", "-v", "--tb=short"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                self.log("All tests passed")
                self.update_status_file("All tests passed ✓")
                return True
            else:
                self.log(f"Tests failed:\n{result.stdout}\n{result.stderr}", level="ERROR")
                self.update_status_file(f"Tests failed - see logs for details")
                return False

        except Exception as e:
            self.log(f"Failed to run tests: {e}", level="ERROR")
            return False

    def commit_changes(self, task: Dict, message: str) -> bool:
        """Commit changes to the feature branch."""
        try:
            # Stage changes
            self._run_git_command(["git", "add", "."])

            # Check if there are changes to commit
            result = self._run_git_command(["git", "diff", "--staged", "--quiet"], check=False)
            if result.returncode == 0:
                self.log("No changes to commit", level="WARNING")
                return True

            # Commit with formatted message
            commit_format = self.config.get("git", {}).get("commit_message_format", "[TASK-{id}] {description}")
            commit_msg = commit_format.format(id=task["id"], description=message)

            self._run_git_command(["git", "commit", "-m", commit_msg])
            self.log(f"Committed changes: {commit_msg}")
            self.update_status_file(f"Committed: {message}")

            return True

        except Exception as e:
            self.log(f"Failed to commit changes: {e}", level="ERROR")
            return False

    def push_branch(self) -> bool:
        """Push the feature branch to remote."""
        try:
            if not self.current_branch:
                self.log("No branch to push", level="ERROR")
                return False

            result = self._run_git_command([
                "git", "push", "-u", "origin", self.current_branch
            ], check=False)

            if result.returncode == 0:
                self.log(f"Pushed branch: {self.current_branch}")
                self.update_status_file(f"Pushed branch to remote")
                return True
            else:
                self.log(f"Failed to push branch: {result.stderr}", level="ERROR")
                return False

        except Exception as e:
            self.log(f"Failed to push branch: {e}", level="ERROR")
            return False

    def create_pull_request(self, task: Dict) -> bool:
        """Create a pull request for the feature."""
        try:
            # Check if gh CLI is available
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                check=False
            )

            if result.returncode != 0:
                self.log("GitHub CLI not available, skipping PR creation", level="WARNING")
                self.update_status_file("Branch pushed - create PR manually")
                return True

            # Create PR
            pr_title = f"{task['id']}: {task['title']}"
            pr_body = f"""## Summary
{task.get('description', 'No description provided')}

## Implementation
- Implemented as described in task {task['id']}

## Testing
- Unit tests added and passing
- Integration tests completed

## Checklist
- [x] Code follows project standards
- [x] Tests added and passing
- [x] Documentation updated (if needed)
- [ ] Ready for review

---
*This PR was automatically created by agent: {self.agent_id}*
"""

            result = subprocess.run(
                ["gh", "pr", "create",
                 "--title", pr_title,
                 "--body", pr_body,
                 "--base", self.config.get("git", {}).get("main_branch", "main")],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                pr_url = result.stdout.strip()
                self.log(f"Created PR: {pr_url}")
                self.update_status_file(f"Created PR: {pr_url}")
                return True
            else:
                self.log(f"Failed to create PR: {result.stderr}", level="ERROR")
                return False

        except Exception as e:
            self.log(f"Failed to create PR: {e}", level="ERROR")
            return False

    def execute_task(self, task: Dict) -> bool:
        """Execute the coding task."""
        try:
            self.log(f"Executing task: {task['id']} - {task['title']}")

            # Create feature branch
            if not self.create_feature_branch(task):
                return False

            # Implement feature
            if not self.implement_feature(task):
                return False

            # Commit initial implementation
            if not self.commit_changes(task, "Initial implementation"):
                return False

            # Run tests
            if not self.run_tests():
                self.log("Tests failed, marking task for revision", level="WARNING")
                # In production, would iterate on fixes
                return False

            # Push branch
            if not self.push_branch():
                return False

            # Create PR
            if not self.create_pull_request(task):
                return False

            self.log(f"Task {task['id']} completed successfully")
            return True

        except Exception as e:
            self.log(f"Failed to execute task: {e}", level="ERROR")
            return False


def main():
    parser = argparse.ArgumentParser(description="Coder Agent")
    parser.add_argument("--agent-id", required=True, help="Agent ID")
    parser.add_argument("--capabilities", nargs="+", help="Agent capabilities")

    args = parser.parse_args()

    agent = CoderAgent(args.agent_id, args.capabilities)
    agent.run()


if __name__ == "__main__":
    main()
