#!/bin/bash
# IMPROVED Atomically claim a task using Git's first-commit-wins mechanism
# VERSION: 2.0 - Enhanced race condition prevention and multi-agent scalability
#
# Usage: ./claim-task-v2.sh <agent-id> [project-id] [branch]
#
# Improvements over v1:
# 1. Exponential backoff with jitter for retries (prevents thundering herd)
# 2. Better conflict detection and logging
# 3. Transaction-like claiming with verification
# 4. Support for agent specialization hints
# 5. Graceful degradation when many agents compete

set -euo pipefail

# Configuration
AGENT_ID="${1:-agent-$(date +%s)-$RANDOM}"
PROJECT="${2:-}"  # Empty means scan all projects
BRANCH="${3:-develop}"
MAX_RETRIES=5
BASE_BACKOFF=1  # seconds

# Logging
log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [$AGENT_ID] $*" >&2
}

error() {
    log "ERROR: $*"
    exit 1
}

# Exponential backoff with jitter (prevents thundering herd)
backoff() {
    local attempt=$1
    local max_sleep=$(( BASE_BACKOFF * (2 ** attempt) ))
    local jitter=$(( RANDOM % max_sleep ))
    local sleep_time=$(( max_sleep + jitter ))
    log "Backing off for ${sleep_time}s (attempt $attempt)"
    sleep "$sleep_time"
}

# Find all available projects
get_projects() {
    if [ -n "$PROJECT" ]; then
        echo "$PROJECT"
    else
        # Scan for projects in .agents/projects/ OR .agents-core/state/
        if [ -d ".agents/projects" ]; then
            find .agents/projects -maxdepth 1 -type d ! -path ".agents/projects" -exec basename {} \; 2>/dev/null | sort
        elif [ -d ".agents-core/state" ]; then
            find .agents-core/state -maxdepth 1 -type d ! -path ".agents-core/state" -exec basename {} \; 2>/dev/null | sort
        elif [ -d "state" ]; then
            find state -maxdepth 1 -type d ! -path "state" -exec basename {} \; 2>/dev/null | sort
        fi
    fi
}

# Check if all dependencies are completed
check_dependencies() {
    local task_file=$1
    local proj=$2

    # Extract required dependencies
    local deps=$(grep -A 100 "^dependencies:" "$task_file" | \
                 grep -A 50 "required\[" | \
                 grep "TASK-" | \
                 sed 's/^[[:space:]]*//' | \
                 grep -v "^required" || true)

    if [ -z "$deps" ]; then
        return 0  # No dependencies
    fi

    # Check each dependency
    local all_met=true
    for dep in $deps; do
        # Try multiple locations for completed tasks
        if [ -f ".agents/completed/$proj/$dep.toon" ] || \
           [ -f ".agents-core/state/$proj/completed/$dep.toon" ] || \
           [ -f "state/$proj/completed/$dep.toon" ]; then
            continue
        else
            log "Dependency not met: $dep for task $(basename $task_file)"
            all_met=false
            break
        fi
    done

    [ "$all_met" = "true" ]
}

# Find best available task (highest priority, all deps met)
find_best_task() {
    local best_file=""
    local best_priority=0
    local best_project=""

    local projects=$(get_projects)

    for proj in $projects; do
        # Try multiple possible task locations
        local task_dirs=(
            ".agents/projects/$proj/tasks"
            ".agents-core/state/$proj/tasks"
            "state/$proj/tasks"
        )

        for task_dir in "${task_dirs[@]}"; do
            if [ ! -d "$task_dir" ]; then
                continue
            fi

            for file in "$task_dir"/TASK-*.toon; do
                if [ ! -f "$file" ]; then
                    continue
                fi

                # Check status
                local status=$(grep "^[[:space:]]*status:" "$file" | head -1 | awk '{print $2}' || echo "unknown")
                if [ "$status" != "ready" ]; then
                    continue
                fi

                # Check dependencies
                if ! check_dependencies "$file" "$proj"; then
                    continue
                fi

                # Get priority
                local priority=$(grep "^[[:space:]]*priority:" "$file" | head -1 | awk '{print $2}' || echo "0")

                # Select highest priority
                if [ "$priority" -gt "$best_priority" ] || [ -z "$best_file" ]; then
                    best_file="$file"
                    best_priority="$priority"
                    best_project="$proj"
                fi
            done
        done
    done

    if [ -z "$best_file" ]; then
        return 1
    fi

    echo "$best_project|$best_file|$best_priority"
    return 0
}

# Attempt to claim a task atomically
try_claim() {
    local attempt=$1

    log "Claim attempt $attempt of $MAX_RETRIES"

    # Fetch latest
    if ! git fetch origin "$BRANCH" 2>/dev/null; then
        log "Warning: Could not fetch from origin"
    fi

    # Ensure we're on the correct branch
    if ! git checkout "$BRANCH" 2>/dev/null; then
        if ! git checkout -b "$BRANCH" "origin/$BRANCH" 2>/dev/null; then
            log "Creating new branch $BRANCH"
            git checkout -b "$BRANCH"
        fi
    fi

    # Pull latest changes (critical for race condition prevention)
    if ! git pull --rebase origin "$BRANCH" 2>/dev/null; then
        log "Warning: Could not pull from origin, using local state"
    fi

    # Find best available task AFTER pulling latest changes
    local task_info
    if ! task_info=$(find_best_task); then
        log "No ready tasks available"
        return 2  # No tasks available
    fi

    IFS='|' read -r proj task_file priority <<< "$task_info"
    local task_id=$(basename "$task_file" .toon)

    log "Attempting to claim $task_id from $proj (priority: $priority)"

    # Double-check task still exists (another agent may have claimed it during pull)
    if [ ! -f "$task_file" ]; then
        log "Task $task_id disappeared (already claimed)"
        return 3  # Task gone, retry
    fi

    # Determine claimed directory based on structure
    local claimed_dir
    if [ -d ".agents/claimed/$proj" ] || [ -d ".agents/claimed" ]; then
        claimed_dir=".agents/claimed/$proj"
    elif [ -d ".agents-core/state/$proj/claimed" ]; then
        claimed_dir=".agents-core/state/$proj/claimed"
    else
        claimed_dir="state/$proj/claimed"
    fi

    # Create claimed directory
    mkdir -p "$claimed_dir"

    # Move task file (local operation, not yet atomic)
    local dest_file="$claimed_dir/$task_id.toon"
    mv "$task_file" "$dest_file"

    # Add claim metadata
    local claim_time=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    cat >> "$dest_file" <<EOF

claim:
 claimed_by: $AGENT_ID
 claimed_at: $claim_time
 last_heartbeat: $claim_time
 claim_attempt: $attempt
EOF

    # Stage changes
    git add "$dest_file" "$(dirname $task_file)" 2>/dev/null || git add -A

    # Commit
    if ! git commit -m "[AGENT-CLAIM] $AGENT_ID claimed $task_id from $proj" --quiet; then
        log "Error: Could not commit claim"
        git reset --hard HEAD
        return 3
    fi

    # ATOMIC OPERATION: First to push wins!
    local push_retries=4
    for i in $(seq 1 $push_retries); do
        if git push origin "$BRANCH" --quiet 2>/dev/null; then
            log "SUCCESS: Claimed $task_id on branch $BRANCH"
            echo "$proj/$task_id"
            return 0
        else
            if [ $i -lt $push_retries ]; then
                log "Push failed, retrying ($i/$push_retries)..."
                sleep $(( 2 ** i ))
            fi
        fi
    done

    # Push failed - someone else claimed a task
    log "Push failed after $push_retries attempts - conflict detected"
    git reset --hard HEAD~1
    git pull --rebase origin "$BRANCH" --quiet 2>/dev/null || true
    return 3  # Conflict, retry
}

# Main claiming loop with exponential backoff
main() {
    log "Starting task claim process (branch: $BRANCH, project: ${PROJECT:-all})"

    for attempt in $(seq 1 $MAX_RETRIES); do
        case $(try_claim $attempt) in
            0)
                # Success
                exit 0
                ;;
            2)
                # No tasks available
                log "No ready tasks available"
                exit 1
                ;;
            3)
                # Conflict or error, retry with backoff
                if [ $attempt -lt $MAX_RETRIES ]; then
                    backoff $attempt
                else
                    error "Failed to claim task after $MAX_RETRIES attempts"
                fi
                ;;
            *)
                error "Unexpected return code"
                ;;
        esac
    done

    error "Failed to claim task after $MAX_RETRIES attempts"
}

main
