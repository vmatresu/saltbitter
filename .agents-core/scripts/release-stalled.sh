#!/bin/bash
# Release tasks that have been claimed but show no heartbeat activity
# Usage: ./release-stalled.sh [timeout-minutes] [branch]
#
# Best Practice: Agents work on 'develop' branch for coordination

set -e

TIMEOUT_MINUTES="${1:-30}"
BRANCH="${2:-develop}"  # Default to develop branch

# Calculate cutoff time (macOS and Linux compatible)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CUTOFF=$(date -u -v-${TIMEOUT_MINUTES}M +%Y-%m-%dT%H:%M:%SZ)
else
    # Linux
    CUTOFF=$(date -u -d "$TIMEOUT_MINUTES minutes ago" +%Y-%m-%dT%H:%M:%SZ)
fi

RELEASED=0

# Search all projects
for project_dir in state/*/; do
    [ -d "$project_dir" ] || continue

    PROJECT=$(basename "$project_dir")

    for file in "$project_dir"TASK-*.toon; do
        [ -f "$file" ] || continue

        TASK_ID=$(basename "$file" .toon)

        # Extract last_heartbeat timestamp (fallback to claimed_at if no heartbeat)
        LAST_HEARTBEAT=$(grep "last_heartbeat:" "$file" | awk '{print $2}')

        if [ -z "$LAST_HEARTBEAT" ]; then
            # No heartbeat found, use claimed_at
            LAST_HEARTBEAT=$(grep "claimed_at:" "$file" | awk '{print $2}')
        fi

        if [ -z "$LAST_HEARTBEAT" ]; then
            echo "⚠ Warning: No heartbeat or claimed_at found in $PROJECT/$TASK_ID" >&2
            continue
        fi

        # Compare timestamps (lexicographic comparison works for ISO 8601)
        if [ "$LAST_HEARTBEAT" \< "$CUTOFF" ]; then
            CLAIMED_BY=$(grep "claimed_by:" "$file" | awk '{print $2}')
            echo "Releasing stalled task: $PROJECT/$TASK_ID" >&2
            echo "  Claimed by: $CLAIMED_BY" >&2
            echo "  Last heartbeat: $LAST_HEARTBEAT" >&2
            echo "  Cutoff time: $CUTOFF" >&2

            # Remove claim metadata
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS sed
                sed -i '' '/^claim:/,$d' "$file"
            else
                # Linux sed
                sed -i '/^claim:/,$d' "$file"
            fi

            # Move back to project tasks/
            mv "$file" "state/$PROJECT/tasks/$TASK_ID.toon"

            RELEASED=$((RELEASED + 1))
        fi
    done
done

if [ $RELEASED -gt 0 ]; then
    git checkout "$BRANCH" 2>/dev/null || true
    git pull --rebase origin "$BRANCH" --quiet 2>/dev/null || true
    git add state/ state/ 2>/dev/null || true
    git commit -m "[ORCHESTRATOR] Released $RELEASED stalled tasks (no heartbeat for ${TIMEOUT_MINUTES}m)" --quiet

    if git push origin "$BRANCH" --quiet 2>/dev/null; then
        echo "✓ Released $RELEASED stalled tasks" >&2
    else
        echo "⚠ Warning: Could not push release (someone else may have released them)" >&2
        git reset --hard HEAD~1 --quiet
        exit 1
    fi
else
    echo "✓ No stalled tasks found (checked claimed/* for heartbeats older than ${TIMEOUT_MINUTES}m)" >&2
fi
