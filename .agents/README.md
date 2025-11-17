# Git-Native Multi-Agent Coordination (TOON Format)

## Core Principle

**Multiple LLM agents (Claude, GPT-4, etc.) coordinate through Git commits using TOON format - 40% fewer tokens than JSON.**

✅ No daemons | ✅ No databases | ✅ No Python processes
✅ TOON format | ✅ Git atomicity | ✅ Bash scripts only

## Why TOON?

**TOON (Token-Oriented Object Notation)** is designed specifically for LLM prompts:
- **40% fewer tokens** than JSON
- **Human-readable** like YAML
- **Lossless** JSON representation
- **Tabular arrays** for uniform data

Perfect for passing task context to LLM agents!

## Architecture

```
.agents/tasks/*.toon (Pending)
        ↓
GitHub Actions (Orchestrator)
        ↓
Parallel Agent Workflows
        ↓
   ┌────┴────┬────┐
Agent 1  Agent 2  Agent 3
(Claude) (Claude) (Claude)
   ↓        ↓        ↓
Git commit (atomic claim)
   ↓
Work on task
   ↓
Git commit (completion)
```

## Directory Structure

```
.agents/
├── README.md                 # This file
├── config.toon               # Config (TOON format)
├── tasks/                    # Pending tasks
│   └── TASK-*.toon
├── claimed/                  # Active tasks
│   └── TASK-*.toon
├── completed/                # Done tasks
│   └── TASK-*.toon
├── scripts/
│   ├── claim-task.sh         # Atomic claiming
│   ├── complete-task.sh      # Mark complete
│   └── release-stalled.sh    # Timeout recovery
└── prompts/
    ├── coder.toon            # Coder prompt (TOON)
    ├── reviewer.toon         # Reviewer prompt (TOON)
    └── tester.toon           # Tester prompt (TOON)
```

## TOON vs JSON Example

### JSON (verbose, more tokens):
```json
{
  "task": {
    "id": "TASK-001",
    "acceptance_criteria": [
      "Login works",
      "Tests pass"
    ]
  }
}
```

### TOON (compact, fewer tokens):
```toon
task:
 id: TASK-001

task.acceptance_criteria[2]:
 Login works
 Tests pass
```

## Task File Format

See `.agents/tasks/TASK-001.toon`:

```toon
task:
 id: TASK-001
 title: Implement user authentication API
 type: feature
 priority: 8
 status: ready

task.description:
 summary: Create FastAPI endpoints
 details: |
  - POST /api/auth/login
  - POST /api/auth/logout
  - JWT tokens

task.acceptance_criteria[3]:
 Login returns JWT
 Tests 80%+ coverage
 Security scan passes

task.dependencies:
 required[0]:
 soft[0]:

task.context:
 files_to_create[2]:
  backend/api/auth.py
  tests/test_auth.py
 branch_prefix: feature/TASK-001

metadata:
 created_at: 2025-11-17T10:30:00Z
 estimated_complexity: medium
```

## Workflow

### 1. Create Task

```bash
cat > .agents/tasks/TASK-042.toon <<'EOF'
task:
 id: TASK-042
 title: Add user profile endpoint
 type: feature
 priority: 5
 status: ready

task.description:
 summary: GET /api/users/{id}/profile
 details: Return profile with avatar, bio

task.acceptance_criteria[2]:
 Returns 200 for valid user
 Returns 404 for invalid user

task.dependencies:
 required[1]:
  TASK-001

metadata:
 created_at: 2025-11-17T12:00:00Z
EOF

git add .agents/tasks/TASK-042.toon
git commit -m "Add task: User profile"
git push
```

### 2. Orchestrator Auto-Triggers

GitHub Actions (every 10 min or on push):
- Releases stalled tasks
- Counts available tasks
- Triggers agent executors

### 3. Agent Claims Task (Atomic)

```bash
./agents/scripts/claim-task.sh "agent-12345"
```

This script atomically:
1. Finds first available task
2. Moves `.toon` file to `claimed/`
3. Adds claim metadata
4. Git commit + push
5. **First push wins** = race-free

### 4. Agent Executes

Reads:
- Task file (`.agents/claimed/TASK-*.toon`)
- Prompt template (`.agents/prompts/coder.toon`)
- Project context (`AGENTS.md`)

Then implements, tests, creates PR.

### 5. Agent Completes

```bash
./agents/scripts/complete-task.sh TASK-042 agent-12345 PR_URL BRANCH
```

Moves to `completed/` with metadata:
```toon
completion:
 status: completed
 completed_at: 2025-11-17T14:30:00Z
 pr_url: https://github.com/.../pull/5
 branch: feature/TASK-042
```

## Key Features

### ✅ Atomic Claiming
Git's first-commit-wins prevents races. No database needed.

### ✅ Token-Efficient
TOON saves 40% tokens vs JSON. Critical for LLM context.

### ✅ Stateless Agents
Each agent is fresh LLM invocation. No heartbeats.

### ✅ Dependencies
```toon
task.dependencies:
 required[2]:
  TASK-001
  TASK-005
```

### ✅ Timeout Recovery
```bash
./.agents/scripts/release-stalled.sh 30
```

### ✅ Observable
All state in Git. Full history preserved.

## CLI Commands

```bash
# Claim task (local dev)
./.agents/scripts/claim-task.sh "my-agent"

# Complete task
./.agents/scripts/complete-task.sh TASK-001 my-agent PR_URL BRANCH

# Release stalled
./.agents/scripts/release-stalled.sh 30

# Check status
echo "Pending: $(ls .agents/tasks/*.toon 2>/dev/null | wc -l)"
echo "Active: $(ls .agents/claimed/*.toon 2>/dev/null | wc -l)"
echo "Done: $(ls .agents/completed/*.toon 2>/dev/null | wc -l)"
```

## LLM Integration

Edit `.github/workflows/agent-executor.yml`:

### Claude Code
```yaml
- name: Execute with Claude
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: |
    claude-code execute \
      --task-file "${{ steps.task.outputs.task_file }}" \
      --prompt-file "${{ steps.prompt.outputs.prompt_file }}"
```

### GPT-4
```yaml
- name: Execute with GPT-4
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    python scripts/gpt4-agent.py \
      --task "${{ steps.task.outputs.task_file }}"
```

## Advantages

| Feature | This System | Traditional |
|---------|-------------|-------------|
| Format | TOON (40% less) | JSON |
| Atomicity | Git commit | DB transaction |
| State | Files in Git | Database |
| Agents | Stateless LLM | Daemons |
| Observable | Git history | Logs |
| Setup | Git + bash | DB + workers |

## Configuration

`.agents/config.toon`:

```toon
orchestrator:
 max_concurrent_agents: 4
 poll_interval_minutes: 10
 task_timeout_minutes: 30

agents.default:
 model: claude-sonnet-4
 provider: anthropic

quality:
 required_test_coverage: 80
 run_linters: true
```

## Troubleshooting

**Task stuck?**
```bash
./.agents/scripts/release-stalled.sh 30
```

**Cancel task?**
```bash
rm .agents/tasks/TASK-042.toon
git add .agents/ && git commit -m "Cancel" && git push
```

**Prioritize task?**
Rename with lower number:
```bash
mv .agents/tasks/TASK-042.toon .agents/tasks/TASK-001-priority.toon
```

## Monitoring

```bash
# Real-time status
watch 'ls .agents/{tasks,claimed,completed}/*.toon 2>/dev/null | wc -l'

# Git history
git log --grep="AGENT" --oneline

# Claimed task ages
for f in .agents/claimed/*.toon; do
  grep claimed_at $f
done
```

---

**Version**: 3.0.0 (TOON-Based)
**Format**: [TOON Spec](https://github.com/toon-format/toon)
**Last Updated**: 2025-11-17
