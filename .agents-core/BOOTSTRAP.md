# .agents-core Bootstrap Guide

**Initialize multi-agent coordination in any Git repository in 3 steps.**

## What is .agents-core?

A **portable framework** that enables LLM agents (Claude, GPT-4, etc.) to autonomously develop software by coordinating through Git commits. No databases, no servers, just Git + TOON files.

**Key Concept**: Agents work like human developers, claiming tasks, implementing features, creating PRs, and completing work—all coordinated via atomic Git operations.

---

## Quick Start (5 Minutes)

### Step 1: Copy Framework to Your Repository

```bash
# Copy .agents-core directory to your project
cp -r /path/to/.agents-core /path/to/your-project/

cd /path/to/your-project
```

### Step 2: Configure Your Project

Edit **ONLY these 5 files** in `config/`:

#### 2a. `config/project.toon`

Define what you're building:

```toon
project:
 id: my-awesome-app
 name: My Awesome App
 tagline: A revolutionary new application
 version: 1.0.0
 status: planning

mission:
 primary: Build the best task management app
 approach: Simple, fast, and beautiful
 north_star_metric: 10,000 daily active users

business_goals[3]:
 Launch MVP in 3 months
 Achieve 85% test coverage
 Support 1000 concurrent users

user_stories[3]{id,role,action,benefit,priority}:
 US-001,user,create tasks,organize my work,10
 US-002,user,mark tasks complete,track progress,9
 US-003,user,set due dates,meet deadlines,8
```

#### 2b. `config/tech-stack.toon`

Specify your technology stack:

```toon
backend:
 language: Python 3.11+
 framework: FastAPI 0.104+
 database: PostgreSQL 15
 testing: pytest

frontend:
 language: TypeScript 5.0+
 framework: React 18
 styling: TailwindCSS
 testing: Jest
```

#### 2c. `config/quality-standards.toon`

Set your quality requirements (or use defaults):

```toon
test_coverage:
 backend_minimum_percent: 85
 frontend_minimum_percent: 70

linting:
 backend_tool: ruff
 frontend_tool: ESLint
```

#### 2d. `config/workflows.toon`

Configure Git workflow (or use defaults):

```toon
branching_strategy: git-flow

branches:
 coordination_branch:
  name: develop  # Agents coordinate here

 feature_branches:
  prefix: feature/TASK-
```

#### 2e. `config/team.toon`

(Usually no changes needed - defines available agent roles)

### Step 3: Run the Architect Agent

```bash
# Invoke architect to create tasks
claude .agents-core/start/architect.toon
```

The architect will:
1. Read `config/project.toon`
2. Design system architecture
3. Create `state/my-awesome-app/architecture.toon`
4. Generate task files: `state/my-awesome-app/tasks/TASK-001.toon`, `TASK-002.toon`, etc.
5. Commit everything to Git

**Done!** Your project now has a backlog of ready-to-implement tasks.

---

## Running Agents

### Software Engineer Agent

Claim and implement tasks:

```bash
claude .agents-core/start/engineer.toon
```

The engineer will:
1. Find highest priority ready task
2. Claim it atomically (Git first-commit-wins)
3. Create feature branch
4. Implement code + tests
5. Send heartbeats during work
6. Create PR
7. Mark complete after merge

### Code Reviewer Agent

Review pull requests:

```bash
claude .agents-core/start/reviewer.toon
# Provide PR number when prompted
```

The reviewer will:
1. Check all acceptance criteria
2. Review code quality
3. Verify tests and coverage
4. Check security
5. Approve or request changes

---

## Project Flow Diagram

```
1. Human creates config/project.toon
   ↓
2. Architect Agent creates architecture + tasks
   ↓
3. Engineer Agents claim tasks in parallel
   ↓ (each engineer)
   - Claim task atomically (Git push)
   - Implement on feature branch
   - Create PR → develop
   - Mark complete after merge
   ↓
4. Reviewer Agent reviews PRs
   ↓
5. Merge → Dependent tasks auto-unlock
   ↓
6. Repeat steps 3-5 until all tasks done
   ↓
7. Release: develop → main
```

---

## Directory Structure Explained

```
.agents-core/
├── config/                    # YOUR SETTINGS (edit these)
│   ├── project.toon           # What you're building
│   ├── tech-stack.toon        # Languages, frameworks
│   ├── quality-standards.toon # Coverage, linters
│   ├── workflows.toon         # Git branching strategy
│   └── team.toon              # Agent roles
│
├── core/                      # FRAMEWORK (don't edit)
│   ├── protocols/             # Task lifecycle, Git coordination
│   ├── templates/             # Empty schemas for tasks, etc.
│   └── roles/                 # Agent behavior definitions
│
├── scripts/                   # HELPERS (optional)
│   ├── claim-task.sh          # Atomic task claiming
│   ├── complete-task.sh       # Mark task done
│   ├── heartbeat-task.sh      # Update heartbeat
│   └── release-stalled.sh     # Release stale tasks
│
├── state/                     # DYNAMIC (Git-tracked)
│   └── {project-id}/          # Created by architect
│       ├── architecture.toon  # System design
│       ├── tasks/             # Available tasks
│       ├── claimed/           # In-progress tasks
│       └── completed/         # Done tasks
│
├── start/                     # ENTRY POINTS
│   ├── product-owner.toon     # Define requirements
│   ├── architect.toon         # Design & create tasks
│   ├── engineer.toon          # Implement tasks
│   └── reviewer.toon          # Review PRs
│
├── BOOTSTRAP.md               # This file
├── VERSION.toon               # Framework version
└── framework_manifest.toon    # File inventory
```

---

## How It Works

### Atomic Task Claiming (Race-Condition Free)

Multiple agents can run simultaneously. Git's atomic push ensures only one claims each task:

```
Engineer A:
 1. git pull
 2. mv state/proj/tasks/TASK-001.toon state/proj/claimed/
 3. git commit
 4. git push ✓ SUCCESS (first to push wins!)

Engineer B (at same time):
 1. git pull
 2. mv state/proj/tasks/TASK-001.toon state/proj/claimed/
 3. git commit
 4. git push ✗ CONFLICT (Engineer A got there first)
 5. git reset, pull, try TASK-002 instead
```

### Dependency Management

Tasks can depend on other tasks:

```toon
task:
 id: TASK-005
 title: Implement user profiles
 status: pending  # Not ready yet

dependencies:
 required[1]:
  TASK-001  # Authentication must complete first
```

When TASK-001 completes, TASK-005 automatically updates to `status: ready`.

### Heartbeats Prevent Stalled Work

If an agent crashes or network fails:

```bash
# Engineer sends heartbeat every 10 minutes
./scripts/heartbeat-task.sh TASK-001 agent-123

# If no heartbeat for 30 minutes:
# Orchestrator runs release-stalled.sh
# Task moves back to state/{project}/tasks/
# Another engineer can claim it
```

---

## Advanced Usage

### Adding a New Agent Role

1. Create `core/roles/security-auditor.toon`:

```toon
role: Security Auditor Agent
responsibility: Perform security reviews on code

workflow[5]:
 1. Read PR and task file
 2. Run security scans (bandit, npm audit)
 3. Manual code review for vulnerabilities
 4. Check compliance requirements
 5. Approve or flag issues
```

2. Create `start/security-auditor.toon`:

```toon
agent_entry_point:
 role: Security Auditor Agent

initialization:
 step_1_load_role_definition:
  read: core/roles/security-auditor.toon
```

3. Update `config/team.toon`:

```toon
available_roles[5]:
 security_auditor:
  responsibility: Security reviews
  prompt: core/roles/security-auditor.toon
  entry_point: start/security-auditor.toon
```

### Customizing for Different Project Types

**Mobile App**:
```toon
# config/tech-stack.toon
mobile:
 framework: React Native + Expo
 language: TypeScript
```

**Data Pipeline**:
```toon
# config/tech-stack.toon
backend:
 language: Python 3.11+
 framework: Apache Airflow
 processing: Pandas + Polars
```

**Microservices**:
```toon
# config/project.toon
architecture_style: microservices

# Architect creates separate projects
state/
├── auth-service/
├── user-service/
├── payment-service/
```

---

## Portability Test

The framework is truly portable. Test it:

```bash
# Initialize in a Todo App
cd ~/todo-app
cp -r /path/to/.agents-core .
# Edit config/project.toon (define todo app requirements)
claude .agents-core/start/architect.toon
# → Creates todo-app tasks

# Initialize in a Crypto Exchange
cd ~/crypto-exchange
cp -r /path/to/.agents-core .
# Edit config/project.toon (define trading platform requirements)
claude .agents-core/start/architect.toon
# → Creates crypto-exchange tasks
```

**Same framework, different projects!**

---

## Observability

Monitor progress:

```bash
# Count tasks by status
echo "Ready: $(ls state/{project}/tasks/*.toon 2>/dev/null | wc -l)"
echo "Claimed: $(ls state/{project}/claimed/*.toon 2>/dev/null | wc -l)"
echo "Completed: $(ls state/{project}/completed/*.toon 2>/dev/null | wc -l)"

# View agent activity
git log --grep="\[AGENT-" --oneline

# View specific agent
git log --grep="agent-123"

# Check dependencies
grep -r "dependencies.required" state/{project}/tasks/
```

---

## Troubleshooting

### "No ready tasks available"

**Problem**: All tasks claimed or have unmet dependencies

**Solution**:
```bash
# Check task status
ls state/{project}/tasks/     # Should have files
ls state/{project}/claimed/   # Agents working on these

# Check dependencies
grep "status:" state/{project}/tasks/TASK-*.toon
```

### "Task already claimed by another agent"

**Problem**: Race condition (another agent claimed first)

**Solution**: Expected behavior! Agent will try next task automatically.

### "Agent not finding project"

**Problem**: Project directory doesn't exist in `state/`

**Solution**: Run architect agent first to create project structure.

---

## Migration from Existing .agents

If you have an existing `.agents/` directory:

```bash
# 1. Backup existing
mv .agents .agents-backup

# 2. Copy new framework
cp -r /path/to/.agents-core .

# 3. Extract config from old system
# - Copy project spec to config/project.toon
# - Copy tech preferences to config/tech-stack.toon

# 4. Migrate tasks
cp -r .agents-backup/projects/*/tasks/* .agents-core/state/{project}/tasks/
```

---

## Success Criteria

You've successfully bootstrapped when:

- [ ] `config/*.toon` files reflect your project
- [ ] Architect created `state/{project}/architecture.toon`
- [ ] Architect created task files in `state/{project}/tasks/`
- [ ] Engineer can claim tasks
- [ ] PRs get created and merged
- [ ] Tasks move through lifecycle (ready → claimed → completed)
- [ ] Dependent tasks auto-unlock

---

## Support

- **Framework documentation**: `core/protocols/*.toon`, `core/roles/*.toon`
- **Examples**: See `core/templates/*.toon`
- **Issues**: GitHub repository issues
- **Customization**: All in `config/*.toon` - edit freely!

---

## License

MIT License - Free to use, modify, and distribute.

---

**Version**: 1.0.0
**Last Updated**: 2025-11-19
**Framework**: .agents-core portable multi-agent coordination
