#!/usr/bin/env python3
"""
Base Worker Agent Class
All agent types (Coder, Reviewer, Tester, Planner) inherit from this class.
"""

import json
import os
import subprocess
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml


class BaseAgent(ABC):
    """Base class for all agent types with Git-native coordination."""

    def __init__(self, agent_id: str, agent_type: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.status = "idle"
        self.current_task_id = None
        self.current_branch = None
        self.started_at = None
        self.last_heartbeat = None
        self.container_id = None

        # Load configuration
        self.config = self._load_config()
        self.repo_root = Path(__file__).parent.parent
        self.agents_dir = self.repo_root / ".agents"
        self.status_dir = self.agents_dir / "status"
        self.tasks_dir = self.agents_dir / "tasks"
        self.logs_dir = self.agents_dir / "logs"

        # Ensure directories exist
        self.status_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> Dict:
        """Load configuration from config.yml"""
        config_path = Path(__file__).parent / "config.yml"
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        return {}

    def _run_git_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command with error handling."""
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=check
            )
            return result
        except subprocess.CalledProcessError as e:
            self.log(f"Git command failed: {e.stderr}", level="ERROR")
            raise

    def log(self, message: str, level: str = "INFO"):
        """Log a message to the agent's log file."""
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = f"[{timestamp}] [{level}] [{self.agent_id}] {message}\n"

        log_file = self.logs_dir / f"{self.agent_id}.log"
        with open(log_file, "a") as f:
            f.write(log_entry)

        if level in ["ERROR", "WARNING"]:
            print(log_entry.strip())

    def register(self) -> bool:
        """Register this agent in the registry."""
        try:
            # Pull latest
            self._run_git_command(["git", "pull", "--rebase"], check=False)

            registry_path = self.agents_dir / "registry.json"
            with open(registry_path) as f:
                registry = json.load(f)

            # Check if already registered
            for agent in registry["agents"]:
                if agent["id"] == self.agent_id:
                    self.log("Agent already registered, updating status")
                    agent["status"] = "idle"
                    agent["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
                    break
            else:
                # Add new agent
                registry["agents"].append({
                    "id": self.agent_id,
                    "type": self.agent_type,
                    "status": "idle",
                    "current_task_id": None,
                    "branch": None,
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "last_heartbeat": datetime.now(timezone.utc).isoformat(),
                    "capabilities": self.capabilities,
                    "container_id": self.container_id
                })
                registry["metadata"]["active_count"] = len([a for a in registry["agents"] if a["status"] != "stopped"])
                registry["metadata"]["total_spawned"] += 1

            registry["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()

            with open(registry_path, "w") as f:
                json.dump(registry, f, indent=2)

            # Commit and push
            self._run_git_command(["git", "add", ".agents/registry.json"])
            self._run_git_command([
                "git", "commit", "-m",
                f"[AGENT-REGISTER] {self.agent_id} registered as {self.agent_type}"
            ])

            # Push with retries
            for attempt in range(self.config.get("agents", {}).get("max_retries", 3)):
                result = self._run_git_command(["git", "push"], check=False)
                if result.returncode == 0:
                    self.log("Successfully registered agent")
                    return True
                time.sleep(2 ** attempt)

            self.log("Failed to push registration after retries", level="ERROR")
            return False

        except Exception as e:
            self.log(f"Failed to register: {e}", level="ERROR")
            return False

    def update_heartbeat(self):
        """Update the agent's heartbeat timestamp."""
        try:
            registry_path = self.agents_dir / "registry.json"
            with open(registry_path) as f:
                registry = json.load(f)

            for agent in registry["agents"]:
                if agent["id"] == self.agent_id:
                    agent["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
                    break

            registry["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()

            with open(registry_path, "w") as f:
                json.dump(registry, f, indent=2)

            # Commit and push heartbeat (non-blocking)
            self._run_git_command(["git", "add", ".agents/registry.json"])
            self._run_git_command([
                "git", "commit", "-m",
                f"[HEARTBEAT] {self.agent_id}"
            ], check=False)
            self._run_git_command(["git", "push"], check=False)

        except Exception as e:
            self.log(f"Failed to update heartbeat: {e}", level="WARNING")

    def find_claimable_task(self) -> Optional[Dict]:
        """Find a task that can be claimed by this agent."""
        try:
            queue_path = self.tasks_dir / "queue.json"
            with open(queue_path) as f:
                queue = json.load(f)

            # Filter pending tasks that match capabilities
            for task in queue["pending"]:
                # Check if dependencies are met
                if task.get("dependencies"):
                    completed_ids = [t["id"] for t in queue["completed"]]
                    if not all(dep in completed_ids for dep in task["dependencies"]):
                        continue

                # Check if agent has required capabilities
                required_caps = task.get("required_capabilities", [])
                if required_caps and not any(cap in self.capabilities for cap in required_caps):
                    continue

                return task

            return None

        except Exception as e:
            self.log(f"Failed to find claimable task: {e}", level="ERROR")
            return None

    def claim_task(self, task: Dict) -> bool:
        """Atomically claim a task via Git commit."""
        try:
            # Pull latest
            self._run_git_command(["git", "pull", "--rebase"], check=False)

            queue_path = self.tasks_dir / "queue.json"
            with open(queue_path) as f:
                queue = json.load(f)

            # Find and move task from pending to in_progress
            task_found = False
            for i, t in enumerate(queue["pending"]):
                if t["id"] == task["id"]:
                    task_found = True
                    claimed_task = queue["pending"].pop(i)
                    claimed_task["claimed_by"] = self.agent_id
                    claimed_task["claimed_at"] = datetime.now(timezone.utc).isoformat()
                    queue["in_progress"].append(claimed_task)
                    break

            if not task_found:
                self.log(f"Task {task['id']} no longer available", level="WARNING")
                return False

            queue["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()

            with open(queue_path, "w") as f:
                json.dump(queue, f, indent=2)

            # Create status file
            self._create_status_file(task)

            # Update registry
            self._update_registry_status("active", task["id"])

            # Commit changes
            self._run_git_command(["git", "add", ".agents/"])
            self._run_git_command([
                "git", "commit", "-m",
                f"[AGENT-CLAIM] {self.agent_id} claimed {task['id']}"
            ])

            # Push with retries
            for attempt in range(self.config.get("agents", {}).get("max_retries", 3)):
                result = self._run_git_command(["git", "push"], check=False)
                if result.returncode == 0:
                    self.current_task_id = task["id"]
                    self.status = "active"
                    self.log(f"Successfully claimed task {task['id']}")
                    return True
                time.sleep(2 ** attempt)

            self.log(f"Failed to push claim for {task['id']}", level="ERROR")
            return False

        except Exception as e:
            self.log(f"Failed to claim task: {e}", level="ERROR")
            return False

    def _create_status_file(self, task: Dict):
        """Create a status file for the current task."""
        status_file = self.status_dir / f"{self.agent_id}.md"
        content = f"""# Agent: {self.agent_id}
**Status**: active
**Task**: {task['id']} - {task['title']}
**Branch**: {self.current_branch or 'TBD'}
**Started**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M %Z')}

## Plan
{self._generate_plan(task)}

## Progress
### Started ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')})
- Task claimed and initialized

## Dependencies
- Waiting on: {', '.join(task.get('dependencies', [])) or 'None'}
- Blocking: TBD

## Issues
- None currently

## Test Results
- Not yet run
"""
        with open(status_file, "w") as f:
            f.write(content)

    def _generate_plan(self, task: Dict) -> str:
        """Generate a plan for the task (to be overridden by specific agents)."""
        return "- [ ] Analyze task requirements\n- [ ] Implement solution\n- [ ] Test implementation"

    def _update_registry_status(self, status: str, task_id: Optional[str] = None):
        """Update agent status in registry."""
        try:
            registry_path = self.agents_dir / "registry.json"
            with open(registry_path) as f:
                registry = json.load(f)

            for agent in registry["agents"]:
                if agent["id"] == self.agent_id:
                    agent["status"] = status
                    agent["current_task_id"] = task_id
                    agent["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
                    break

            with open(registry_path, "w") as f:
                json.dump(registry, f, indent=2)

        except Exception as e:
            self.log(f"Failed to update registry status: {e}", level="ERROR")

    def update_status_file(self, message: str, completed_steps: Optional[List[str]] = None):
        """Update the agent's status file with progress."""
        try:
            status_file = self.status_dir / f"{self.agent_id}.md"
            if not status_file.exists():
                return

            with open(status_file, "r") as f:
                content = f.read()

            # Add progress entry
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
            progress_entry = f"\n### Progress Update ({timestamp})\n- {message}\n"

            # Find progress section and append
            if "## Progress" in content:
                parts = content.split("## Dependencies")
                progress_part = parts[0]
                rest = "## Dependencies" + parts[1] if len(parts) > 1 else ""
                content = progress_part + progress_entry + rest

            with open(status_file, "w") as f:
                f.write(content)

        except Exception as e:
            self.log(f"Failed to update status file: {e}", level="ERROR")

    def complete_task(self, task_id: str):
        """Mark task as completed and clean up."""
        try:
            # Pull latest
            self._run_git_command(["git", "pull", "--rebase"], check=False)

            queue_path = self.tasks_dir / "queue.json"
            with open(queue_path) as f:
                queue = json.load(f)

            # Move task from in_progress to completed
            for i, task in enumerate(queue["in_progress"]):
                if task["id"] == task_id:
                    completed_task = queue["in_progress"].pop(i)
                    completed_task["completed_by"] = self.agent_id
                    completed_task["completed_at"] = datetime.now(timezone.utc).isoformat()
                    queue["completed"].append(completed_task)
                    break

            queue["metadata"]["total_tasks_completed"] += 1
            queue["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()

            with open(queue_path, "w") as f:
                json.dump(queue, f, indent=2)

            # Archive status file
            status_file = self.status_dir / f"{self.agent_id}.md"
            if status_file.exists():
                archive_dir = self.status_dir / "archive"
                archive_dir.mkdir(exist_ok=True)
                status_file.rename(archive_dir / f"{self.agent_id}-{task_id}.md")

            # Update registry
            self._update_registry_status("idle")

            # Commit
            self._run_git_command(["git", "add", ".agents/"])
            self._run_git_command([
                "git", "commit", "-m",
                f"[AGENT-COMPLETE] {self.agent_id} completed {task_id}"
            ])
            self._run_git_command(["git", "push"])

            self.current_task_id = None
            self.status = "idle"
            self.log(f"Task {task_id} completed successfully")

        except Exception as e:
            self.log(f"Failed to complete task: {e}", level="ERROR")

    def stop(self):
        """Stop the agent gracefully."""
        try:
            self._update_registry_status("stopped")
            self.log("Agent stopped")
        except Exception as e:
            self.log(f"Failed to stop cleanly: {e}", level="ERROR")

    @abstractmethod
    def execute_task(self, task: Dict) -> bool:
        """Execute the task (implemented by specific agent types)."""
        pass

    def run(self):
        """Main agent loop."""
        self.log(f"Starting {self.agent_type} agent: {self.agent_id}")

        if not self.register():
            self.log("Failed to register agent", level="ERROR")
            return

        heartbeat_interval = self.config.get("agents", {}).get("heartbeat_interval_seconds", 60)
        last_heartbeat = time.time()

        while True:
            try:
                # Update heartbeat periodically
                if time.time() - last_heartbeat > heartbeat_interval:
                    self.update_heartbeat()
                    last_heartbeat = time.time()

                # If idle, look for work
                if self.status == "idle":
                    task = self.find_claimable_task()
                    if task:
                        if self.claim_task(task):
                            success = self.execute_task(task)
                            if success:
                                self.complete_task(task["id"])
                            else:
                                self.log(f"Task {task['id']} execution failed", level="ERROR")
                                self.status = "idle"

                # Sleep to avoid busy-waiting
                time.sleep(self.config.get("coordinator", {}).get("poll_interval_seconds", 30))

            except KeyboardInterrupt:
                self.log("Received interrupt signal")
                break
            except Exception as e:
                self.log(f"Error in main loop: {e}", level="ERROR")
                time.sleep(60)

        self.stop()
