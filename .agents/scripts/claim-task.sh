#!/bin/bash
# Atomically claim a task using Git's first-commit-wins mechanism
# Usage: ./claim-task.sh <agent-id>

set -e

AGENT_ID="${1:-agent-$(date +%s)-$RANDOM}"
TASK_FILE=""

# Find first available task (highest priority)
for file in .agents/tasks/TASK-*.toon; do
    if [ -f "$file" ]; then
        TASK_FILE="$file"
        break
    fi
done

if [ -z "$TASK_FILE" ]; then
    echo "No tasks available" >&2
    exit 1
fi

TASK_ID=$(basename "$TASK_FILE" .toon)

# Atomic claim via git commit
git pull --rebase origin main 2>/dev/null || true

# Check if task still exists after pull
if [ ! -f "$TASK_FILE" ]; then
    echo "Task was claimed by another agent" >&2
    exit 2
fi

# Move file to claimed/
mv "$TASK_FILE" ".agents/claimed/$TASK_ID.toon"

# Add claim metadata
cat >> ".agents/claimed/$TASK_ID.toon" <<EOF

claim:
 claimed_by: $AGENT_ID
 claimed_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

# Commit changes
git add ".agents/claimed/$TASK_ID.toon" ".agents/tasks/" 2>/dev/null || true
git commit -m "[AGENT-CLAIM] $AGENT_ID claimed $TASK_ID" --quiet

# First to push wins - this is the atomic operation
if git push origin main --quiet 2>/dev/null; then
    echo "SUCCESS: Claimed $TASK_ID" >&2
    echo "$TASK_ID"
    exit 0
else
    # Someone else got it first, rollback
    git reset --hard HEAD~1 --quiet
    git pull --rebase origin main --quiet 2>/dev/null || true
    echo "CONFLICT: Task already claimed by another agent" >&2
    exit 2
fi
