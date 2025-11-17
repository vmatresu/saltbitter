#!/usr/bin/env python3
"""
Mark a task as completed based on branch name or task ID
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def extract_task_id_from_branch(branch: str) -> str:
    """Extract task ID from branch name."""
    # Expected format: feature/TASK-{id}-{slug} or fix/TASK-{id}-{slug}
    if "TASK-" in branch:
        parts = branch.split("TASK-")
        if len(parts) > 1:
            task_part = parts[1].split("-")[0]
            return f"TASK-{task_part}"
    return None


def complete_task(task_id: str, queue_path: Path):
    """Mark task as completed in queue."""
    with open(queue_path) as f:
        queue = json.load(f)

    # Find task in in_progress
    task_found = False
    for i, task in enumerate(queue["in_progress"]):
        if task["id"] == task_id:
            task_found = True
            completed_task = queue["in_progress"].pop(i)
            completed_task["completed_at"] = datetime.now(timezone.utc).isoformat()
            completed_task["completed_by"] = "ci-system"
            queue["completed"].append(completed_task)
            break

    if not task_found:
        # Check if already completed
        for task in queue["completed"]:
            if task["id"] == task_id:
                print(f"Task {task_id} already completed")
                return True

        print(f"Task {task_id} not found in in_progress queue", file=sys.stderr)
        return False

    queue["metadata"]["total_tasks_completed"] += 1
    queue["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()

    with open(queue_path, "w") as f:
        json.dump(queue, f, indent=2)

    print(f"Marked task {task_id} as completed")
    return True


def main():
    parser = argparse.ArgumentParser(description="Mark task as completed")
    parser.add_argument("--task-id", help="Task ID to complete")
    parser.add_argument("--task-from-branch", help="Extract task ID from branch name")
    args = parser.parse_args()

    if not args.task_id and not args.task_from_branch:
        print("Must provide either --task-id or --task-from-branch", file=sys.stderr)
        sys.exit(1)

    # Determine task ID
    task_id = args.task_id
    if args.task_from_branch:
        task_id = extract_task_id_from_branch(args.task_from_branch)
        if not task_id:
            print(f"Could not extract task ID from branch: {args.task_from_branch}", file=sys.stderr)
            sys.exit(1)

    # Find repo root and queue
    repo_root = Path(__file__).parent.parent.parent
    queue_path = repo_root / ".agents" / "tasks" / "queue.json"

    if not queue_path.exists():
        print(f"Queue file not found: {queue_path}", file=sys.stderr)
        sys.exit(1)

    # Complete task
    success = complete_task(task_id, queue_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
