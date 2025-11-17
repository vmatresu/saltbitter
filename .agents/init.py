#!/usr/bin/env python3
"""
Initialize the agent orchestration framework
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def init_framework(max_workers: int = 8):
    """Initialize the agent framework."""
    repo_root = Path(__file__).parent.parent
    agents_dir = repo_root / ".agents"

    print("Initializing agent orchestration framework...")

    # Create directories
    directories = [
        agents_dir / "status",
        agents_dir / "status" / "archive",
        agents_dir / "tasks" / "archive",
        agents_dir / "scripts",
        agents_dir / "logs"
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory.relative_to(repo_root)}")

    # Initialize registry if it doesn't exist
    registry_path = agents_dir / "registry.json"
    if not registry_path.exists():
        registry = {
            "agents": [],
            "metadata": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "active_count": 0,
                "total_spawned": 0
            }
        }
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=2)
        print(f"✓ Initialized registry: {registry_path.relative_to(repo_root)}")
    else:
        print(f"✓ Registry already exists: {registry_path.relative_to(repo_root)}")

    # Initialize queue if it doesn't exist
    queue_path = agents_dir / "tasks" / "queue.json"
    if not queue_path.exists():
        queue = {
            "pending": [],
            "in_progress": [],
            "completed": [],
            "blocked": [],
            "metadata": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "total_tasks_created": 0,
                "total_tasks_completed": 0
            }
        }
        with open(queue_path, "w") as f:
            json.dump(queue, f, indent=2)
        print(f"✓ Initialized task queue: {queue_path.relative_to(repo_root)}")
    else:
        print(f"✓ Task queue already exists: {queue_path.relative_to(repo_root)}")

    # Make scripts executable
    scripts = [
        agents_dir / "coordinator.py",
        agents_dir / "worker.py",
        agents_dir / "coder.py",
        agents_dir / "reviewer.py",
        agents_dir / "tester.py",
        agents_dir / "planner.py",
        agents_dir / "init.py",
        agents_dir / "scripts" / "update_test_results.py",
        agents_dir / "scripts" / "complete_task.py"
    ]

    for script in scripts:
        if script.exists():
            script.chmod(0o755)
            print(f"✓ Made executable: {script.relative_to(repo_root)}")

    print("\n✅ Agent framework initialized successfully!")
    print(f"\nNext steps:")
    print(f"1. Review and customize .agents/config.yml")
    print(f"2. Create or update AGENTS.md with project context")
    print(f"3. Add tasks to .agents/tasks/queue.json")
    print(f"4. Start coordinator: python .agents/coordinator.py --daemon")
    print(f"   Or run single cycle: python .agents/coordinator.py")


def main():
    parser = argparse.ArgumentParser(description="Initialize agent framework")
    parser.add_argument("--max-workers", type=int, default=8, help="Maximum parallel workers")
    args = parser.parse_args()

    try:
        init_framework(args.max_workers)
    except Exception as e:
        print(f"❌ Initialization failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
