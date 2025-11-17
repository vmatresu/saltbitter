#!/bin/bash
# Release tasks that have been claimed but not completed within timeout
# Usage: ./release-stalled.sh [timeout-minutes]

set -e

TIMEOUT_MINUTES="${1:-30}"
CUTOFF=$(date -u -d "$TIMEOUT_MINUTES minutes ago" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || \
         date -u -v-${TIMEOUT_MINUTES}M +%Y-%m-%dT%H:%M:%SZ)

RELEASED=0

for file in .agents/claimed/TASK-*.toon; do
    [ -f "$file" ] || continue

    TASK_ID=$(basename "$file" .toon)

    # Extract claimed_at timestamp
    CLAIMED_AT=$(grep "claimed_at:" "$file" | awk '{print $2}')

    if [ -z "$CLAIMED_AT" ]; then
        echo "⚠ Warning: No claimed_at found in $TASK_ID" >&2
        continue
    fi

    # Compare timestamps (lexicographic comparison works for ISO 8601)
    if [ "$CLAIMED_AT" \< "$CUTOFF" ]; then
        echo "Releasing stalled task: $TASK_ID (claimed at $CLAIMED_AT)" >&2

        # Remove claim metadata
        sed -i '/^claim:/,$d' "$file" 2>/dev/null || sed -i '' '/^claim:/,$d' "$file"

        # Move back to tasks/
        mv "$file" ".agents/tasks/$TASK_ID.toon"

        RELEASED=$((RELEASED + 1))
    fi
done

if [ $RELEASED -gt 0 ]; then
    git pull --rebase origin main --quiet 2>/dev/null || true
    git add .agents/tasks/ .agents/claimed/ 2>/dev/null || true
    git commit -m "[ORCHESTRATOR] Released $RELEASED stalled tasks (timeout: ${TIMEOUT_MINUTES}m)" --quiet
    git push origin main --quiet
    echo "✓ Released $RELEASED stalled tasks"
else
    echo "✓ No stalled tasks found"
fi
