#!/bin/bash
# Unblock tasks that have all dependencies completed
# Usage: ./unblock-tasks.sh [project-id]

set -e

if [[ "${OSTYPE:-}" == darwin* ]]; then
  SED_INPLACE=(sed -i '')
else
  SED_INPLACE=(sed -i)
fi

PROJECT="${1:-dating-platform}"
UNBLOCKED=0
CHECKED=0

echo "Checking tasks in project: $PROJECT"
echo "Looking for tasks with completed dependencies..."
echo ""

# Iterate through all blocked tasks
for task_file in .agents/projects/$PROJECT/tasks/TASK-*.toon; do
  [ -f "$task_file" ] || continue

  TASK_ID=$(basename "$task_file" .toon)
  CHECKED=$((CHECKED + 1))

  # Get current status
  CURRENT_STATUS=$(grep "^ status:" "$task_file" | head -1 | awk '{print $2}')

  # Skip if not blocked
  if [ "$CURRENT_STATUS" != "blocked" ]; then
    continue
  fi

  # Extract required dependencies
  DEPS=$(grep -A 20 "^dependencies:" "$task_file" | grep -A 10 "required\[" | grep "TASK-" | sed 's/^[[:space:]]*//' || true)

  # If no dependencies, unblock it
  if [ -z "$DEPS" ]; then
    echo "⚠️  $TASK_ID: marked as blocked but has no dependencies - unblocking"
    "${SED_INPLACE[@]}" 's/^ status: blocked$/ status: ready/' "$task_file"
    UNBLOCKED=$((UNBLOCKED + 1))
    continue
  fi

  # Check if all dependencies are met
  ALL_MET=true
  MISSING_DEPS=""

  while IFS= read -r dep; do
    # Skip empty lines
    [ -z "$dep" ] && continue

    # Check if dependency is completed
    if [ ! -f ".agents/completed/$PROJECT/$dep.toon" ]; then
      ALL_MET=false
      MISSING_DEPS="$MISSING_DEPS $dep"
    fi
  done <<< "$DEPS"

  # Unblock if all dependencies are met
  if [ "$ALL_MET" = true ]; then
    echo "✅ Unblocking $TASK_ID (all dependencies completed)"
    "${SED_INPLACE[@]}" 's/^ status: blocked$/ status: ready/' "$task_file"
    UNBLOCKED=$((UNBLOCKED + 1))
  else
    echo "⏳ $TASK_ID: still waiting for:$MISSING_DEPS"
  fi
done

echo ""
echo "Summary:"
echo "  Tasks checked: $CHECKED"
echo "  Tasks unblocked: $UNBLOCKED"

exit 0
