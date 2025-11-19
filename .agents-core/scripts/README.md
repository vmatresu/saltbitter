# Helper Scripts for Agent Coordination

These scripts provide atomic operations for task management in the multi-agent framework. Agents can use these scripts OR perform the Git operations directly.

## Available Scripts

### 1. claim-task.sh

**Purpose**: Atomically claim a task using Git's first-commit-wins mechanism

**Usage**:
```bash
./scripts/claim-task.sh <agent-id> [project-id] [branch]
```

**Parameters**:
- `agent-id`: Unique identifier for the agent (e.g., `agent-engineer-12345`)
- `project-id`: (Optional) Specific project to search, defaults to all projects
- `branch`: (Optional) Git branch to use, defaults to `develop`

**Examples**:
```bash
# Claim highest priority task from any project
./scripts/claim-task.sh agent-$(date +%s)

# Claim task from specific project
./scripts/claim-task.sh agent-engineer-123 dating-platform

# Claim task on specific branch
./scripts/claim-task.sh agent-123 myproject main
```

**How it works**:
1. Finds highest priority task with `status: ready`
2. Moves task from `state/{project}/tasks/` to `state/{project}/claimed/`
3. Appends claim metadata (agent ID, timestamp, heartbeat)
4. Commits and pushes atomically
5. First agent to push wins, others retry

**Exit codes**:
- `0`: Success, task claimed
- `1`: No ready tasks available
- `2`: Task already claimed by another agent (conflict)

---

### 2. heartbeat-task.sh

**Purpose**: Update heartbeat timestamp to prevent task auto-release

**Usage**:
```bash
./scripts/heartbeat-task.sh <task-id> <agent-id> [project-id]
```

**Parameters**:
- `task-id`: Task identifier (e.g., `TASK-001`)
- `agent-id`: Unique identifier for the agent
- `project-id`: (Optional) Project ID, defaults to scanning all projects

**Examples**:
```bash
./scripts/heartbeat-task.sh TASK-001 agent-123
./scripts/heartbeat-task.sh TASK-042 agent-456 dating-platform
```

**Frequency**: Run every 10-15 minutes during implementation

**Why needed**: Tasks with no heartbeat for 30+ minutes are auto-released

---

### 3. complete-task.sh

**Purpose**: Mark task as completed after PR merge

**Usage**:
```bash
./scripts/complete-task.sh <task-id> <agent-id> <pr-url> [project-id] [branch]
```

**Parameters**:
- `task-id`: Task identifier (e.g., `TASK-001`)
- `agent-id`: Unique identifier for the agent
- `pr-url`: GitHub PR URL (e.g., `https://github.com/user/repo/pull/42`)
- `project-id`: (Optional) Project ID, defaults to scanning
- `branch`: (Optional) Git branch, defaults to `develop`

**Examples**:
```bash
./scripts/complete-task.sh TASK-001 agent-123 https://github.com/user/repo/pull/42
./scripts/complete-task.sh TASK-042 agent-456 PR-42 dating-platform
```

**How it works**:
1. Moves task from `state/{project}/claimed/` to `state/{project}/completed/`
2. Appends completion metadata (agent ID, timestamp, PR URL)
3. Finds dependent tasks (those with this task in `dependencies.required`)
4. Updates dependent tasks to `status: ready` if all dependencies met
5. Commits and pushes atomically

**Automation**: Often handled automatically by GitHub Actions on PR merge

---

### 4. release-stalled.sh

**Purpose**: Release stalled tasks (no heartbeat for 30+ minutes) back to available pool

**Usage**:
```bash
./scripts/release-stalled.sh [project-id] [branch]
```

**Parameters**:
- `project-id`: (Optional) Specific project, defaults to all projects
- `branch`: (Optional) Git branch, defaults to `develop`

**Examples**:
```bash
# Release all stalled tasks
./scripts/release-stalled.sh

# Release stalled tasks for specific project
./scripts/release-stalled.sh dating-platform

# Release on specific branch
./scripts/release-stalled.sh myproject main
```

**How it works**:
1. Scans all claimed tasks
2. Checks `claim.last_heartbeat` timestamp
3. If > 30 minutes ago, moves task back to `state/{project}/tasks/`
4. Removes claim metadata
5. Updates status to `ready`

**Automation**: Typically run by orchestrator every 30 minutes

---

## When to Use Scripts vs Direct Git

### Use Scripts When:
- You want atomic operations handled automatically
- You're building an orchestrator
- You want race condition handling built-in
- You prefer simpler command-line interface

### Use Direct Git When:
- You want full control over Git operations
- You're implementing custom logic
- You want to understand the protocol deeply
- Scripts don't fit your workflow

## Protocol Reference

All scripts implement the protocols defined in:
- `core/protocols/task-lifecycle.toon`
- `core/protocols/git-coordination.toon`

## Error Handling

All scripts:
- Use `set -e` (exit on error)
- Return meaningful exit codes
- Print errors to stderr
- Rollback on conflicts
- Handle race conditions gracefully

## Customization

These scripts can be customized for your project:
- Change default branch (modify `BRANCH` variable)
- Adjust heartbeat intervals (modify metadata appended)
- Change stale threshold (modify time check in release-stalled.sh)
- Add project-specific validation

## Observability

Monitor script usage via Git log:
```bash
# View all agent activity
git log --grep="\[AGENT-"

# View claims
git log --grep="\[AGENT-CLAIM\]"

# View completions
git log --grep="\[AGENT-COMPLETE\]"

# View heartbeats
git log --grep="\[AGENT-HEARTBEAT\]"
```

## Troubleshooting

### "No ready tasks available"
- All tasks are claimed or have unmet dependencies
- Check: `ls state/{project}/tasks/` and `ls state/{project}/claimed/`

### "Task already claimed by another agent"
- Race condition: another agent claimed the task first
- Solution: Script automatically exits, retry with different task

### "Permission denied" or "command not found"
- Scripts not executable
- Solution: `chmod +x scripts/*.sh`

### Stalled tasks not releasing
- Heartbeat script not running
- Solution: Ensure heartbeat script runs every 10-15 minutes

## Best Practices

1. **Always send heartbeats** during long-running tasks
2. **Check exit codes** when calling scripts programmatically
3. **Use atomic operations** - don't bypass scripts with manual file moves
4. **Monitor Git log** for agent activity
5. **Run release-stalled.sh** periodically in production
