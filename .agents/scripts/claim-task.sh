#!/bin/bash
# Atomically claim a task using Git's first-commit-wins mechanism
# Usage: ./claim-task.sh <agent-id> [project-id] [branch]
#
# Best Practice: Agents work on 'develop' branch for coordination
# Production code is merged to 'main' only after review

set -e

AGENT_ID="${1:-agent-$(date +%s)-$RANDOM}"
PROJECT="${2:-dating-platform}"  # Default to dating-platform
BRANCH="${3:-develop}"  # Default to develop branch for agent coordination
TASK_FILE=""
TASK_PROJECT=""

# Find first available task across all projects (or specific project)
if [ -n "$PROJECT" ]; then
    # Search specific project
    PROJECTS="$PROJECT"
else
    # Search all projects
    PROJECTS=$(ls -1 .agents/projects/ | grep -v README.md | grep '\.toon$' | sed 's/\.toon$//')
fi

# Find highest priority ready task
for proj in $PROJECTS; do
    for file in .agents/projects/$proj/tasks/TASK-*.toon; do
        if [ -f "$file" ]; then
            # Check if task is ready (not blocked)
            STATUS=$(grep "status:" "$file" | awk '{print $2}')
            if [ "$STATUS" = "ready" ]; then
                PRIORITY=$(grep "priority:" "$file" | awk '{print $2}')
                if [ -z "$TASK_FILE" ] || [ "$PRIORITY" -gt "$MAX_PRIORITY" ]; then
                    TASK_FILE="$file"
                    TASK_PROJECT="$proj"
                    MAX_PRIORITY="$PRIORITY"
                fi
            fi
        fi
    done
done

if [ -z "$TASK_FILE" ]; then
    echo "No ready tasks available" >&2
    exit 1
fi

TASK_ID=$(basename "$TASK_FILE" .toon)

echo "Attempting to claim $TASK_ID from $TASK_PROJECT project (priority: $MAX_PRIORITY) on branch $BRANCH" >&2

# Fetch latest branches from origin
git fetch origin "$BRANCH" 2>/dev/null || true

# Ensure we're on the correct branch (create from origin if doesn't exist)
if git checkout "$BRANCH" 2>/dev/null; then
    echo "Switched to existing branch $BRANCH" >&2
elif git checkout -b "$BRANCH" "origin/$BRANCH" 2>/dev/null; then
    echo "Created branch $BRANCH from origin/$BRANCH" >&2
else
    git checkout -b "$BRANCH"
    echo "Created new branch $BRANCH" >&2
fi

# Atomic claim via git commit
git pull --rebase origin "$BRANCH" 2>/dev/null || true

# Check if task still exists after pull
if [ ! -f "$TASK_FILE" ]; then
    echo "Task was claimed by another agent during pull" >&2
    exit 2
fi

# Create claimed directory if it doesn't exist
mkdir -p ".agents/claimed/$TASK_PROJECT"

# Move file to claimed/
mv "$TASK_FILE" ".agents/claimed/$TASK_PROJECT/$TASK_ID.toon"

# Add claim metadata with heartbeat
CLAIM_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat >> ".agents/claimed/$TASK_PROJECT/$TASK_ID.toon" <<EOF

claim:
 claimed_by: $AGENT_ID
 claimed_at: $CLAIM_TIME
 last_heartbeat: $CLAIM_TIME
 heartbeat_interval_minutes: 10
 stale_threshold_minutes: 30
EOF

# Commit changes
git add ".agents/claimed/$TASK_PROJECT/$TASK_ID.toon" ".agents/projects/$TASK_PROJECT/tasks/" 2>/dev/null || true
git commit -m "[AGENT-CLAIM] $AGENT_ID claimed $TASK_ID from $TASK_PROJECT" --quiet

# First to push wins - this is the atomic operation
if git push origin "$BRANCH" --quiet 2>/dev/null; then
    echo "SUCCESS: Claimed $TASK_ID on branch $BRANCH" >&2
    echo "$TASK_PROJECT/$TASK_ID"
    exit 0
else
    # Someone else got it first, rollback
    git reset --hard HEAD~1 --quiet
    git pull --rebase origin "$BRANCH" --quiet 2>/dev/null || true
    echo "CONFLICT: Task already claimed by another agent" >&2
    exit 2
fi
