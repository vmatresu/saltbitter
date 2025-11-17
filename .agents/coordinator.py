#!/usr/bin/env python3
"""
Coordinator Agent - Main orchestration script
Responsibilities:
- Task decomposition and distribution
- Worker spawning and monitoring
- Conflict detection and resolution
- Progress reporting
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import yaml


class Coordinator:
    """Main coordinator agent for orchestrating worker agents."""

    def __init__(self, config_path: Optional[Path] = None):
        self.repo_root = Path(__file__).parent.parent
        self.agents_dir = self.repo_root / ".agents"
        self.config = self._load_config(config_path)
        self.registry_path = self.agents_dir / "registry.json"
        self.queue_path = self.agents_dir / "tasks" / "queue.json"
        self.logs_dir = self.agents_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)

    def _load_config(self, config_path: Optional[Path] = None) -> Dict:
        """Load configuration from config.yml"""
        if config_path is None:
            config_path = self.agents_dir / "config.yml"

        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        return {}

    def log(self, message: str, level: str = "INFO"):
        """Log coordinator messages."""
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = f"[{timestamp}] [{level}] [COORDINATOR] {message}\n"

        log_file = self.logs_dir / "coordinator.log"
        with open(log_file, "a") as f:
            f.write(log_entry)

        print(log_entry.strip())

    def _run_git_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command."""
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

    def sync_repository(self):
        """Pull latest changes from repository."""
        try:
            self._run_git_command(["git", "fetch", "origin"])
            result = self._run_git_command(["git", "pull", "--rebase"], check=False)
            if result.returncode != 0:
                self.log(f"Pull failed: {result.stderr}", level="WARNING")
        except Exception as e:
            self.log(f"Failed to sync repository: {e}", level="ERROR")

    def get_registry(self) -> Dict:
        """Load the agent registry."""
        if not self.registry_path.exists():
            return {"agents": [], "metadata": {"active_count": 0}}

        with open(self.registry_path) as f:
            return json.load(f)

    def get_queue(self) -> Dict:
        """Load the task queue."""
        if not self.queue_path.exists():
            return {"pending": [], "in_progress": [], "completed": [], "blocked": []}

        with open(self.queue_path) as f:
            return json.load(f)

    def update_queue(self, queue: Dict):
        """Update the task queue."""
        queue["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.queue_path, "w") as f:
            json.dump(queue, f, indent=2)

    def check_heartbeats(self, registry: Dict) -> List[str]:
        """Check for timed-out agents and return list of failed agent IDs."""
        timeout_minutes = self.config.get("coordinator", {}).get("heartbeat_timeout_minutes", 10)
        timeout_delta = timedelta(minutes=timeout_minutes)
        now = datetime.now(timezone.utc)
        failed_agents = []

        for agent in registry["agents"]:
            if agent["status"] in ["stopped", "idle"]:
                continue

            last_heartbeat = datetime.fromisoformat(agent["last_heartbeat"].replace('Z', '+00:00'))
            if now - last_heartbeat > timeout_delta:
                self.log(f"Agent {agent['id']} timed out (last heartbeat: {last_heartbeat})", level="WARNING")
                failed_agents.append(agent["id"])
                agent["status"] = "timed_out"

        return failed_agents

    def release_failed_tasks(self, failed_agents: List[str]):
        """Release tasks from failed agents back to queue."""
        if not failed_agents:
            return

        queue = self.get_queue()
        released = 0

        for i, task in enumerate(queue["in_progress"][:]):
            if task.get("claimed_by") in failed_agents:
                queue["pending"].append(task)
                queue["in_progress"].remove(task)
                released += 1
                self.log(f"Released task {task['id']} from failed agent {task.get('claimed_by')}")

        if released > 0:
            self.update_queue(queue)
            self._run_git_command(["git", "add", ".agents/"])
            self._run_git_command([
                "git", "commit", "-m",
                f"[COORDINATOR] Released {released} tasks from failed agents"
            ], check=False)
            self._run_git_command(["git", "push"], check=False)

    def calculate_priority(self, task: Dict) -> float:
        """Calculate task priority based on various factors."""
        priority = task.get("priority", 5)
        complexity = task.get("estimated_complexity", "medium")

        complexity_weights = {"low": 1.0, "medium": 1.5, "high": 2.0}
        weight = complexity_weights.get(complexity, 1.5)

        # Boost priority if task is blocking others
        queue = self.get_queue()
        blocking_count = sum(1 for t in queue["pending"]
                            if task["id"] in t.get("dependencies", []))

        return priority + (blocking_count * 2.0) - weight

    def prioritize_tasks(self):
        """Reorder pending tasks by priority."""
        queue = self.get_queue()

        if not queue["pending"]:
            return

        # Calculate priorities and sort
        for task in queue["pending"]:
            task["_calculated_priority"] = self.calculate_priority(task)

        queue["pending"].sort(key=lambda t: t.get("_calculated_priority", 0), reverse=True)

        # Remove temporary priority field
        for task in queue["pending"]:
            task.pop("_calculated_priority", None)

        self.update_queue(queue)

    def get_active_agent_count(self, registry: Dict) -> int:
        """Count active agents."""
        return len([a for a in registry["agents"] if a["status"] in ["active", "idle"]])

    def get_idle_agent_count(self, registry: Dict) -> int:
        """Count idle agents."""
        return len([a for a in registry["agents"] if a["status"] == "idle"])

    def spawn_worker(self, agent_type: str, capabilities: List[str]) -> bool:
        """Spawn a new worker agent."""
        try:
            registry = self.get_registry()
            agent_count = self.get_active_agent_count(registry)
            max_workers = self.config.get("system", {}).get("max_workers", 8)

            if agent_count >= max_workers:
                self.log(f"Cannot spawn worker: at max capacity ({max_workers})", level="WARNING")
                return False

            # Generate agent ID
            agent_id = f"{agent_type}-{int(time.time() * 1000) % 1000000:06d}"

            # Spawn based on type
            script_map = {
                "coder": "coder.py",
                "reviewer": "reviewer.py",
                "tester": "tester.py",
                "planner": "planner.py"
            }

            script = script_map.get(agent_type)
            if not script:
                self.log(f"Unknown agent type: {agent_type}", level="ERROR")
                return False

            script_path = self.agents_dir / script
            if not script_path.exists():
                self.log(f"Agent script not found: {script_path}", level="ERROR")
                return False

            # Launch agent in background
            subprocess.Popen(
                [sys.executable, str(script_path), "--agent-id", agent_id],
                cwd=self.repo_root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            self.log(f"Spawned {agent_type} agent: {agent_id}")
            return True

        except Exception as e:
            self.log(f"Failed to spawn worker: {e}", level="ERROR")
            return False

    def spawn_workers_for_pending_tasks(self):
        """Spawn workers based on pending tasks and idle agent count."""
        queue = self.get_queue()
        registry = self.get_registry()

        pending_count = len(queue["pending"])
        idle_count = self.get_idle_agent_count(registry)

        if pending_count == 0 or idle_count > 0:
            return

        # Spawn coder agents for pending tasks
        needed = min(pending_count, self.config.get("system", {}).get("max_workers", 8))
        current = self.get_active_agent_count(registry)
        to_spawn = min(needed - current, pending_count)

        for _ in range(to_spawn):
            self.spawn_worker("coder", self.config.get("capabilities", {}).get("available", []))

    def detect_conflicts(self) -> List[Dict]:
        """Detect potential merge conflicts between active branches."""
        conflicts = []
        try:
            # Get all active branches
            result = self._run_git_command([
                "git", "branch", "-r", "--format=%(refname:short)"
            ])
            branches = [b.strip() for b in result.stdout.split("\n") if b.strip() and "feature/" in b]

            # Check for overlapping file changes (simplified)
            # In production, would use git diff to detect actual conflicts
            self.log(f"Monitoring {len(branches)} active feature branches")

        except Exception as e:
            self.log(f"Failed to detect conflicts: {e}", level="ERROR")

        return conflicts

    def generate_report(self) -> Dict:
        """Generate status report."""
        registry = self.get_registry()
        queue = self.get_queue()

        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agents": {
                "total": len(registry["agents"]),
                "active": len([a for a in registry["agents"] if a["status"] == "active"]),
                "idle": len([a for a in registry["agents"] if a["status"] == "idle"]),
                "stopped": len([a for a in registry["agents"] if a["status"] == "stopped"]),
                "timed_out": len([a for a in registry["agents"] if a["status"] == "timed_out"])
            },
            "tasks": {
                "pending": len(queue["pending"]),
                "in_progress": len(queue["in_progress"]),
                "completed": len(queue["completed"]),
                "blocked": len(queue["blocked"])
            }
        }

        return report

    def run_coordination_cycle(self):
        """Run one coordination cycle."""
        self.log("Starting coordination cycle")

        # Sync with remote
        self.sync_repository()

        # Load current state
        registry = self.get_registry()
        queue = self.get_queue()

        # Check agent heartbeats
        failed_agents = self.check_heartbeats(registry)
        if failed_agents:
            self.release_failed_tasks(failed_agents)

        # Prioritize tasks
        self.prioritize_tasks()

        # Spawn workers if needed
        if self.config.get("coordinator", {}).get("enable_auto_scaling", True):
            self.spawn_workers_for_pending_tasks()

        # Detect conflicts
        self.detect_conflicts()

        # Generate report
        report = self.generate_report()
        self.log(f"Status: {report['agents']['active']} active agents, "
                f"{report['tasks']['pending']} pending tasks, "
                f"{report['tasks']['in_progress']} in progress")

    def run_daemon(self):
        """Run coordinator as a daemon."""
        self.log("Starting coordinator daemon")
        poll_interval = self.config.get("coordinator", {}).get("poll_interval_seconds", 30)

        try:
            while True:
                self.run_coordination_cycle()
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            self.log("Coordinator daemon stopped by user")
        except Exception as e:
            self.log(f"Coordinator daemon error: {e}", level="ERROR")

    def shutdown_agents(self, force: bool = False, grace_period: int = 300):
        """Shutdown all agents."""
        self.log(f"Shutting down all agents (force={force}, grace={grace_period}s)")

        registry = self.get_registry()
        for agent in registry["agents"]:
            if agent["status"] in ["active", "idle"]:
                agent["status"] = "stopped"

        with open(self.registry_path, "w") as f:
            json.dump(registry, f, indent=2)

        if not force:
            self.log(f"Waiting {grace_period}s for agents to finish current work...")
            time.sleep(grace_period)

        self._run_git_command(["git", "add", ".agents/registry.json"])
        self._run_git_command([
            "git", "commit", "-m",
            "[COORDINATOR] Shutdown all agents"
        ], check=False)
        self._run_git_command(["git", "push"], check=False)

    def scale_workers(self, count: int):
        """Scale worker count."""
        max_workers = self.config.get("system", {}).get("max_workers", 8)
        if count > max_workers:
            self.log(f"Cannot scale to {count}: max is {max_workers}", level="ERROR")
            return

        registry = self.get_registry()
        current = self.get_active_agent_count(registry)

        if count > current:
            # Spawn more workers
            to_spawn = count - current
            self.log(f"Scaling up: spawning {to_spawn} workers")
            for _ in range(to_spawn):
                self.spawn_worker("coder", self.config.get("capabilities", {}).get("available", []))
        elif count < current:
            # Stop excess workers (set to stopped, they'll finish current work)
            to_stop = current - count
            self.log(f"Scaling down: stopping {to_stop} workers")
            stopped = 0
            for agent in registry["agents"]:
                if agent["status"] == "idle" and stopped < to_stop:
                    agent["status"] = "stopped"
                    stopped += 1

            with open(self.registry_path, "w") as f:
                json.dump(registry, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Agent Coordinator")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--spawn-workers", action="store_true", help="Spawn workers for pending tasks")
    parser.add_argument("--max-parallel", type=int, help="Maximum parallel workers")
    parser.add_argument("--prioritize", action="store_true", help="Prioritize tasks")
    parser.add_argument("--shutdown", action="store_true", help="Shutdown all agents")
    parser.add_argument("--force", action="store_true", help="Force shutdown (don't wait)")
    parser.add_argument("--grace-period", type=int, default=300, help="Grace period for shutdown (seconds)")
    parser.add_argument("--scale-workers", type=int, help="Scale to N workers")
    parser.add_argument("--report", action="store_true", help="Generate status report")

    args = parser.parse_args()

    coordinator = Coordinator()

    if args.shutdown:
        coordinator.shutdown_agents(force=args.force, grace_period=args.grace_period)
    elif args.scale_workers is not None:
        coordinator.scale_workers(args.scale_workers)
    elif args.report:
        report = coordinator.generate_report()
        print(json.dumps(report, indent=2))
    elif args.daemon:
        coordinator.run_daemon()
    else:
        # Single coordination cycle
        coordinator.run_coordination_cycle()


if __name__ == "__main__":
    main()
