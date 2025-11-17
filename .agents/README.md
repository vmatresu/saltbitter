# Multi-Agent Development System (Pure LLM Coordination)

**Complete project development using ONLY LLM agents coordinating through Git + TOON format.**

## Core Concept

```
Product Owner Agent → Architect Agent → Software Engineer Agents → Completion
         ↓                  ↓                     ↓
    Requirements       Task Breakdown        Implementation
         ↓                  ↓                     ↓
     (GitHub)           (GitHub)              (GitHub)
```

**NO databases. NO Python. NO servers. ONLY:**
- LLM agents invoked with prompts
- Git for coordination
- TOON files for state
- Bash helpers for atomic operations (optional - agents can do Git directly)

## Agent Roles

### 1. Product Owner Agent
**Responsibility**: Define requirements and acceptance criteria
**Input**: Business goals, user needs
**Output**: Project spec in `.agents/project.toon`
**Invoked**: Manually or via GitHub issue

### 2. Architect Agent
**Responsibility**: Design system and create task breakdown
**Input**: Project spec
**Output**: Architecture doc + task files (`.agents/tasks/*.toon`)
**Invoked**: After Product Owner completes spec

### 3. Software Engineer Agents (Multiple, Parallel)
**Responsibility**: Implement features, write tests, create PRs
**Input**: Task file from `.agents/tasks/`
**Output**: Code, tests, PR
**Invoked**: Orchestrator finds available task

### 4. Reviewer Agent (Optional)
**Responsibility**: Code review and quality checks
**Input**: Pull request
**Output**: Review comments, approval/rejection
**Invoked**: PR created

## Complete Project Flow

### Phase 1: Project Inception (Product Owner)

**Invocation**: Human creates GitHub issue or manually invokes PO agent

**Prompt**: `.agents/prompts/product-owner.toon`

```toon
role: Product Owner Agent
responsibility: Define project requirements

input.project_name: {from_issue_or_manual}
input.business_goals: {from_issue_body}

tasks[4]:
 1. Create project specification
 2. Define user stories
 3. List acceptance criteria
 4. Identify technical constraints

output.location: .agents/project.toon
output.format: TOON

workflow:
 read_input: GitHub issue or manual input
 analyze: Business requirements and constraints
 create_file: .agents/project.toon
 git_commit: "[PO] Add project specification: {project_name}"
 next_agent: Mention @architect-agent in commit message
```

**PO Agent Output** - `.agents/project.toon`:
```toon
project:
 name: SaltBitter Dating Platform
 version: 1.0.0
 status: planning

business_goals[3]:
 Create modern dating platform
 Focus on meaningful connections
 Privacy-first approach

user_stories[3]{id,role,action,benefit}:
 US-001,user,create profile,find matches
 US-002,user,browse profiles,see potential matches
 US-003,user,send messages,connect with matches

technical_constraints:
 stack: FastAPI + PostgreSQL + React
 hosting: Cloud-native (AWS/GCP)
 compliance: GDPR compliant
 performance: <200ms API response time

metadata:
 created_at: 2025-11-17T15:00:00Z
 created_by: product-owner-agent
 next_step: architect-breakdown
```

### Phase 2: Architecture & Task Breakdown (Architect)

**Invocation**: Architect agent triggered by PO mention or workflow dispatch

**Prompt**: `.agents/prompts/architect.toon`

```toon
role: Architect Agent
responsibility: Design system architecture and create implementation tasks

input.project_spec: .agents/project.toon
input.project_context: AGENTS.md

tasks[5]:
 1. Design system architecture
 2. Identify components and modules
 3. Define task dependencies
 4. Create task files for each feature
 5. Estimate complexity and priority

outputs[2]:
 .agents/architecture.toon
 .agents/tasks/TASK-*.toon

workflow:
 read: .agents/project.toon, AGENTS.md
 design: System architecture and data models
 decompose: Break into implementable tasks
 create: One TASK-*.toon per feature/module
 dependencies: Set task.dependencies based on relationships
 git_commit: "[ARCH] Add architecture and {N} tasks"
 next_step: Ready for Software Engineers
```

**Architect Agent Outputs**:

`.agents/architecture.toon`:
```toon
architecture:
 name: SaltBitter System Design
 style: Microservices with API Gateway

layers[3]{name,tech,purpose}:
 frontend,React+TypeScript,User interface
 backend,FastAPI+Python,Business logic & API
 data,PostgreSQL,Persistent storage

components[5]{name,responsibility,apis}:
 auth_service,User authentication,"POST /auth/register POST /auth/login"
 profile_service,User profiles,"GET/POST /profiles/{id}"
 match_service,Matching algorithm,"GET /matches POST /matches/like"
 message_service,Direct messaging,"GET/POST /messages"
 notification_service,Push notifications,"POST /notifications"

data_models[3]{table,key_fields}:
 users,"id,email,password_hash,created_at"
 profiles,"user_id,name,bio,photos,preferences"
 messages,"id,from_user,to_user,content,sent_at"

dependencies:
 profile_service: [auth_service]
 match_service: [profile_service]
 message_service: [auth_service,profile_service]

metadata:
 created_at: 2025-11-17T15:30:00Z
 created_by: architect-agent
```

`.agents/tasks/TASK-001.toon`:
```toon
task:
 id: TASK-001
 title: Implement user authentication system
 type: feature
 priority: 10
 status: ready

description:
 summary: Build JWT-based auth system
 details: |
  Complete authentication system:
  - POST /api/auth/register (create new user)
  - POST /api/auth/login (return JWT token)
  - POST /api/auth/logout (invalidate token)
  - Password hashing with bcrypt
  - Session management with JWT
  - Token refresh endpoint

acceptance_criteria[6]:
 Registration endpoint creates user and returns 201
 Login returns valid JWT token
 Logout invalidates token
 Passwords hashed with bcrypt (12 rounds)
 Unit test coverage ≥85%
 Integration tests passing

dependencies:
 required[0]:
 blocks[3]:
  TASK-002
  TASK-003
  TASK-004

context:
 files_to_create[4]:
  backend/api/auth.py
  backend/models/user.py
  backend/services/auth_service.py
  tests/test_auth.py
 database_migrations[1]:
  001_create_users_table.sql
 related_docs[2]:
  .agents/architecture.toon
  AGENTS.md

technical_details:
 database_tables[1]:
  users(id UUID PK,email VARCHAR UNIQUE,password_hash VARCHAR,created_at TIMESTAMP)
 api_endpoints[3]:
  POST /api/auth/register
  POST /api/auth/login
  POST /api/auth/logout
 dependencies[2]:
  python-jose[cryptography]
  passlib[bcrypt]

metadata:
 created_by: architect-agent
 created_at: 2025-11-17T15:45:00Z
 estimated_hours: 6
 complexity: medium
```

### Phase 3: Implementation (Software Engineers - Parallel)

**Invocation**: GitHub Actions orchestrator (every 10 min) launches engineer agents

**Prompt**: `.agents/prompts/software-engineer.toon`

```toon
role: Software Engineer Agent
responsibility: Implement features with comprehensive tests

input.task_file: .agents/claimed/{task_id}.toon
input.context: AGENTS.md

workflow[12]:
 1. Claim task (atomic Git operation)
 2. Read task file completely
 3. Read project architecture and standards
 4. Create feature branch: {task.context.branch_prefix}
 5. Implement all functionality per task.description.details
 6. Write comprehensive unit tests
 7. Write integration tests if needed
 8. Run tests locally - must pass
 9. Check coverage - must meet task.acceptance_criteria
 10. Run linters (ruff, mypy, bandit)
 11. Create pull request with clear description
 12. Mark task complete (atomic Git operation)

claiming_task:
 option_1: Call ./agents/scripts/claim-task.sh {agent_id}
 option_2: Do Git operations directly (pull, move file, commit, push)
 both_work: Choose based on preference

code_standards:
 read_from: AGENTS.md
 style: Black formatter, Google docstrings
 types: Full type hints with mypy strict mode
 coverage_min: 85%
 linters[3]:
  ruff
  mypy --strict
  bandit -r

pr_requirements:
 title: "{task.id}: {task.title}"
 body: |
  ## Summary
  {implementation_summary}

  ## Task
  Closes {task.id}
  See .agents/tasks/{task.id}.toon

  ## Changes
  - {list_of_changes}

  ## Testing
  - Unit tests: {coverage}%
  - Integration tests: {pass/fail}

  ## Checklist
  - [x] All acceptance criteria met
  - [x] Tests passing
  - [x] Coverage ≥85%
  - [x] Linting passing
  - [x] Type checking passing

completing_task:
 option_1: Call ./agents/scripts/complete-task.sh {task_id} {agent_id} {pr_url} {branch}
 option_2: Do Git operations directly (add completion metadata, move file, commit, push)
 both_work: Choose based on preference
```

**Engineer Agent Execution** (Example):
```bash
# Engineer Agent 1 invoked by orchestrator
# Reads: .agents/tasks/TASK-001.toon
# Claims atomically (git pull, move file, commit, push)
# File now at: .agents/claimed/TASK-001.toon
# Creates branch: feature/auth-system
# Implements auth endpoints
# Writes tests
# Creates PR #5
# Marks complete (moves to .agents/completed/TASK-001.toon)
```

### Phase 4: Review (Optional)

**Prompt**: `.agents/prompts/reviewer.toon`

```toon
role: Code Reviewer Agent
responsibility: Ensure quality and standards compliance

input.pr_number: {pr_number}
input.task_file: .agents/completed/{task_id}.toon

review_checklist[9]:
 All acceptance criteria from task file met
 Code follows AGENTS.md standards
 Test coverage ≥ task requirements
 No security vulnerabilities (bandit clean)
 No type errors (mypy clean)
 No linting issues (ruff clean)
 Documentation adequate
 Error handling implemented
 Performance acceptable

workflow[6]:
 1. Fetch PR diff and files
 2. Read corresponding task file
 3. Check all acceptance criteria
 4. Review code quality
 5. Run/verify automated checks
 6. Approve or request changes

actions:
 if_all_passing:
  approve_pr: true
  comment: "LGTM - all acceptance criteria met"
  auto_merge: if configured
 if_failing:
  request_changes: true
  comment: {specific_feedback}
  tag: @software-engineer or @architect if critical
```

## Real-World Example: Building SaltBitter

### Step 1: Product Owner Creates Spec
```
Trigger: GitHub issue #1 "Build dating platform"
Agent: Product Owner
Actions:
  - Reads issue body and comments
  - Creates .agents/project.toon with:
    * 15 user stories
    * Technical stack (FastAPI/React/PostgreSQL)
    * Compliance requirements (GDPR)
  - Commits: "[PO] Add SaltBitter project specification"
  - Mentions @architect-agent
Result: .agents/project.toon ready for architecture
```

### Step 2: Architect Designs & Breaks Down
```
Trigger: Architect agent sees PO mention
Agent: Architect
Actions:
  - Reads .agents/project.toon
  - Designs system (5 microservices)
  - Creates .agents/architecture.toon
  - Creates 15 task files:
    * TASK-001: Auth system (priority 10, no deps)
    * TASK-002: User profiles (priority 9, depends TASK-001)
    * TASK-003: Matching algorithm (priority 8, depends TASK-002)
    * ... etc
  - Commits: "[ARCH] Add architecture and 15 implementation tasks"
Result: 15 tasks ready for implementation
```

### Step 3: Orchestrator Launches Engineers
```
Trigger: GitHub Actions cron (every 10 min)
Orchestrator Actions:
  - Scans .agents/tasks/ → finds 3 ready tasks (no unmet dependencies)
  - Launches 3 Software Engineer agent workflows in parallel
  - Each workflow claims one task atomically
```

### Step 4: Engineers Implement (Parallel)
```
Engineer Agent 1:
  Task: TASK-001 (auth)
  Actions:
    - Claims task → .agents/claimed/TASK-001.toon
    - Creates branch: feature/auth-system
    - Implements: auth endpoints, JWT, bcrypt
    - Writes: 45 unit tests, 12 integration tests
    - Coverage: 87%
    - Creates PR #5
    - Completes → .agents/completed/TASK-001.toon
  Duration: 18 minutes

Engineer Agent 2:
  Task: TASK-004 (database setup)
  Actions:
    - Claims task → .agents/claimed/TASK-004.toon
    - Creates PostgreSQL migrations
    - Sets up Alembic
    - Documents schema
    - Creates PR #6
    - Completes
  Duration: 12 minutes

Engineer Agent 3:
  Task: TASK-002 (user profiles)
  Status: BLOCKED (depends on TASK-001)
  Actions: Waits for TASK-001 completion
```

### Step 5: Reviews & Merges
```
Reviewer Agent (PR #5):
  - Checks: All 6 acceptance criteria ✓
  - Tests: 87% coverage ✓
  - Linting: Clean ✓
  - Security: No vulnerabilities ✓
  - Approves PR #5
  - Auto-merges to main

Result: TASK-001 complete, TASK-002 now unblocked
```

### Step 6: Continued Parallel Development
```
Next orchestrator cycle:
  - TASK-002 now ready (dependency met)
  - TASK-005, TASK-006 also ready
  - Launches 3 more engineer agents
  - Cycle repeats until all 15 tasks complete
```

## Directory Structure

```
.agents/
├── README.md                    # This file
├── project.toon                 # Product Owner output
├── architecture.toon            # Architect output
├── config.toon                  # System config
│
├── tasks/                       # Ready to implement
│   ├── TASK-001.toon
│   ├── TASK-002.toon
│   └── ...
│
├── claimed/                     # Being worked on
│   └── TASK-003.toon
│
├── completed/                   # Finished
│   ├── TASK-001.toon
│   └── TASK-002.toon
│
├── prompts/                     # Agent instructions (TOON)
│   ├── product-owner.toon
│   ├── architect.toon
│   ├── software-engineer.toon
│   └── reviewer.toon
│
└── scripts/                     # Optional helpers (agents can use OR ignore)
    ├── claim-task.sh           # Atomic claim helper
    ├── complete-task.sh        # Atomic complete helper
    └── release-stalled.sh      # Timeout recovery
```

## Why Bash Helpers? (Optional)

Agents can do ALL Git operations directly in prompts, BUT bash helpers provide:

**Atomic claiming** - Ensures exactly one agent gets task:
```bash
git pull && mv task && commit && (git push || rollback)
```

**Consistency** - All agents follow same pattern

**Simplicity** - Agents can call `./claim-task.sh` vs writing full Git logic

**Agents are NOT required to use helpers** - they can do Git directly!

## How Agents Are Invoked

### Automated (GitHub Actions)
``yaml
# .github/workflows/agent-executor.yml
- name: Invoke Software Engineer Agent
  run: |
    # Pass task + prompt + context to LLM
    cat .agents/claimed/TASK-001.toon \
        .agents/prompts/software-engineer.toon \
        AGENTS.md | \
    llm-api --model claude-sonnet-4
```

### Manual (Local Development)
```bash
# Human invokes agent
claude-code --files .agents/tasks/TASK-001.toon \
            .agents/prompts/software-engineer.toon \
            AGENTS.md
```

### Via GitHub Issues
```yaml
on:
  issues:
    types: [labeled]
jobs:
  product-owner:
    if: github.event.label.name == 'needs-spec'
    steps:
      - run: |
          gh issue view ${{ github.event.issue.number }} | \
          llm-api --prompt .agents/prompts/product-owner.toon
```

## Monitoring Project Progress

```bash
# Overall status
echo "Tasks ready: $(ls .agents/tasks/*.toon 2>/dev/null | wc -l)"
echo "In progress: $(ls .agents/claimed/*.toon 2>/dev/null | wc -l)"
echo "Completed: $(ls .agents/completed/*.toon 2>/dev/null | wc -l)"

# View project
cat .agents/project.toon

# View architecture
cat .agents/architecture.toon

# Check dependencies
grep -r "depends" .agents/tasks/

# Agent activity
git log --grep="\[PO\]\|\[ARCH\]\|\[SWE\]" --oneline
```

## Key Advantages

✅ **Pure LLM Agents** - No Python workers, just prompt invocations
✅ **Git Coordination** - No database, fully observable
✅ **TOON Format** - 40% fewer tokens than JSON
✅ **Clear Roles** - PO → Architect → Engineers → Reviewers
✅ **Parallel Execution** - Multiple engineers work concurrently
✅ **Dependency Management** - Automatic task unlocking
✅ **Atomic Operations** - Race-free task claiming

---

**Version**: 4.0.0 (Pure LLM Multi-Agent Project Development)
**Format**: [TOON Specification](https://github.com/toon-format/toon)
**Last Updated**: 2025-11-17
