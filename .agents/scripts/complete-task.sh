#!/bin/bash
# Mark a task as completed and move to completed/
# Usage: ./complete-task.sh <task-id> <agent-id> [pr-url] [branch-name]

set -e

TASK_ID="$1"
AGENT_ID="$2"
PR_URL="${3:-}"
BRANCH="${4:-}"

if [ -z "$TASK_ID" ] || [ -z "$AGENT_ID" ]; then
    echo "Usage: $0 <task-id> <agent-id> [pr-url] [branch-name]" >&2
    exit 1
fi

CLAIMED_FILE=".agents/claimed/$TASK_ID.toon"

if [ ! -f "$CLAIMED_FILE" ]; then
    echo "Error: Task $TASK_ID not found in claimed/" >&2
    exit 1
fi

# Verify this agent owns the task
if ! grep -q "claimed_by: $AGENT_ID" "$CLAIMED_FILE"; then
    echo "Error: Task $TASK_ID is not claimed by $AGENT_ID" >&2
    exit 1
fi

# Move to completed/
mv "$CLAIMED_FILE" ".agents/completed/$TASK_ID.toon"

# Add completion metadata
cat >> ".agents/completed/$TASK_ID.toon" <<EOF

completion:
 status: completed
 completed_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
 completed_by: $AGENT_ID
EOF

if [ -n "$PR_URL" ]; then
    echo " pr_url: $PR_URL" >> ".agents/completed/$TASK_ID.toon"
fi

if [ -n "$BRANCH" ]; then
    echo " branch: $BRANCH" >> ".agents/completed/$TASK_ID.toon"
fi

# Commit and push
git pull --rebase origin main --quiet 2>/dev/null || true
git add ".agents/completed/$TASK_ID.toon" ".agents/claimed/" 2>/dev/null || true
git commit -m "[AGENT-COMPLETE] $AGENT_ID completed $TASK_ID" --quiet
git push origin main --quiet

echo "✓ Task $TASK_ID marked as completed"
