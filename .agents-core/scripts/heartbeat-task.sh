#!/bin/bash
# Update heartbeat timestamp for claimed task to signal active work
# Usage: ./heartbeat-task.sh <task-id> <agent-id> [project-id] [branch]
#
# Best Practice: Agents work on 'develop' branch for coordination

set -e

TASK_ID="$1"
AGENT_ID="$2"
PROJECT="${3:-dating-platform}"
BRANCH="${4:-develop}"  # Default to develop branch

if [ -z "$TASK_ID" ] || [ -z "$AGENT_ID" ]; then
    echo "Usage: $0 <task-id> <agent-id> [project-id]" >&2
    exit 1
fi

CLAIMED_FILE="state/$PROJECT/$TASK_ID.toon"

if [ ! -f "$CLAIMED_FILE" ]; then
    echo "ERROR: Task $TASK_ID is not claimed in project $PROJECT" >&2
    exit 1
fi

# Verify this agent owns the task
OWNER=$(grep "claimed_by:" "$CLAIMED_FILE" | awk '{print $2}')
if [ "$OWNER" != "$AGENT_ID" ]; then
    echo "ERROR: Task $TASK_ID is claimed by $OWNER, not $AGENT_ID" >&2
    exit 1
fi

# Pull latest changes
git checkout "$BRANCH" 2>/dev/null || true
git pull --rebase origin "$BRANCH" 2>/dev/null || true

# Check if task still exists after pull
if [ ! -f "$CLAIMED_FILE" ]; then
    echo "ERROR: Task was released or completed by another agent" >&2
    exit 2
fi

# Update heartbeat timestamp
HEARTBEAT_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Use sed to update the last_heartbeat line (macOS compatible)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS sed
    sed -i '' "s/last_heartbeat:.*/last_heartbeat: $HEARTBEAT_TIME/" "$CLAIMED_FILE"
else
    # Linux sed
    sed -i "s/last_heartbeat:.*/last_heartbeat: $HEARTBEAT_TIME/" "$CLAIMED_FILE"
fi

# Commit heartbeat
git add "$CLAIMED_FILE"
git commit -m "[AGENT-HEARTBEAT] $AGENT_ID working on $TASK_ID" --quiet

# Push heartbeat (non-critical if fails)
if git push origin "$BRANCH" --quiet 2>/dev/null; then
    echo "Heartbeat updated for $TASK_ID at $HEARTBEAT_TIME" >&2
    exit 0
else
    # If push fails, just pull and try once more
    git pull --rebase origin "$BRANCH" --quiet 2>/dev/null || true
    if git push origin "$BRANCH" --quiet 2>/dev/null; then
        echo "Heartbeat updated for $TASK_ID at $HEARTBEAT_TIME (retry)" >&2
        exit 0
    else
        echo "WARNING: Could not push heartbeat (task may have been released)" >&2
        git reset --hard HEAD~1 --quiet
        exit 3
    fi
fi
