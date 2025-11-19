#!/bin/bash
# Mark a task as completed and move to completed/
# Usage: ./complete-task.sh <task-id> <agent-id> [pr-url] [project-id] [branch]
#
# Best Practice: Agents work on 'develop' branch for coordination

set -e

TASK_ID="$1"
AGENT_ID="$2"
PR_URL="${3:-}"
PROJECT="${4:-dating-platform}"
BRANCH="${5:-develop}"  # Default to develop branch

if [ -z "$TASK_ID" ] || [ -z "$AGENT_ID" ]; then
    echo "Usage: $0 <task-id> <agent-id> [pr-url] [project-id]" >&2
    exit 1
fi

CLAIMED_FILE="state/$PROJECT/$TASK_ID.toon"

if [ ! -f "$CLAIMED_FILE" ]; then
    echo "Error: Task $TASK_ID not found in claimed/$PROJECT/" >&2
    exit 1
fi

# Verify this agent owns the task
OWNER=$(grep "claimed_by:" "$CLAIMED_FILE" | awk '{print $2}')
if [ "$OWNER" != "$AGENT_ID" ]; then
    echo "Error: Task $TASK_ID is claimed by $OWNER, not $AGENT_ID" >&2
    exit 1
fi

# Create completed directory if needed
mkdir -p "state/$PROJECT"

# Move to completed/
mv "$CLAIMED_FILE" "state/$PROJECT/$TASK_ID.toon"

# Add completion metadata
COMPLETED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat >> "state/$PROJECT/$TASK_ID.toon" <<EOF

completion:
 status: completed
 completed_at: $COMPLETED_AT
 completed_by: $AGENT_ID
EOF

if [ -n "$PR_URL" ]; then
    echo " pr_url: $PR_URL" >> "state/$PROJECT/$TASK_ID.toon"
fi

# Commit and push
git checkout "$BRANCH" 2>/dev/null || true
git pull --rebase origin "$BRANCH" --quiet 2>/dev/null || true
git add "state/$PROJECT/$TASK_ID.toon" "state/$PROJECT/" 2>/dev/null || true
git commit -m "[AGENT-COMPLETE] $AGENT_ID completed $PROJECT/$TASK_ID" --quiet

if git push origin "$BRANCH" --quiet 2>/dev/null; then
    echo "✓ Task $PROJECT/$TASK_ID marked as completed at $COMPLETED_AT" >&2

    # Check if this completion unblocks any tasks
    echo "Checking for unblocked tasks..." >&2
    UNBLOCKED=0
    for task_file in state/$PROJECT/tasks/TASK-*.toon; do
        [ -f "$task_file" ] || continue

        # Check if this task was blocking completion
        if grep -q "required.*$TASK_ID" "$task_file" 2>/dev/null; then
            # Check if all dependencies are now met
            BLOCKED=0
            while IFS= read -r dep_task; do
                if [ ! -f "state/$PROJECT/$dep_task.toon" ]; then
                    BLOCKED=1
                    break
                fi
            done < <(grep -A 10 "required\[" "$task_file" | grep "TASK-" | sed 's/^[[:space:]]*//' || true)

            if [ $BLOCKED -eq 0 ]; then
                # Update status to ready
                UNBLOCKED_TASK=$(basename "$task_file" .toon)
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    sed -i '' 's/status: blocked/status: ready/' "$task_file"
                else
                    sed -i 's/status: blocked/status: ready/' "$task_file"
                fi
                echo "  → Unblocked: $UNBLOCKED_TASK" >&2
                UNBLOCKED=$((UNBLOCKED + 1))
            fi
        fi
    done

    if [ $UNBLOCKED -gt 0 ]; then
        git add state/$PROJECT/tasks/
        git commit -m "[AUTO] Unblocked $UNBLOCKED tasks after completing $TASK_ID" --quiet
        git push origin "$BRANCH" --quiet 2>/dev/null || true
        echo "✓ Unblocked $UNBLOCKED tasks" >&2
    fi

    exit 0
else
    echo "⚠ Warning: Could not push completion (conflict with other agent)" >&2
    git reset --hard HEAD~1 --quiet
    exit 1
fi
