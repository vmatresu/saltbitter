# Agent Entry Points

This directory contains entry points for invoking different agent roles in the multi-agent coordination framework.

## Available Agent Roles

### 1. Product Owner Agent
**Entry Point**: `start/product-owner.toon`

**Responsibility**: Define project requirements and acceptance criteria

**When to use**: At project inception, when creating a new project specification

**Input**: Business goals, user needs, requirements document, or GitHub issue

**Output**: `config/project.toon`

**Invocation**:
```bash
claude start/product-owner.toon
```

---

### 2. Architect Agent
**Entry Point**: `start/architect.toon`

**Responsibility**: Design system architecture and create task breakdown

**When to use**: After Product Owner creates project specification

**Input**: `config/project.toon`

**Output**:
- `state/{project-id}/architecture.toon`
- `state/{project-id}/tasks/TASK-*.toon`

**Invocation**:
```bash
claude start/architect.toon
```

---

### 3. Software Engineer Agent
**Entry Point**: `start/engineer.toon`

**Responsibility**: Implement features with comprehensive tests

**When to use**: After Architect creates tasks, when ready tasks are available

**Input**: `state/{project-id}/claimed/TASK-{id}.toon`

**Output**:
- Code implementation
- Tests
- Pull request

**Invocation**:
```bash
claude start/engineer.toon
```

The engineer agent will:
1. Find available ready tasks
2. Claim highest priority task atomically
3. Implement functionality
4. Create PR
5. Mark complete after merge

---

### 4. Reviewer Agent
**Entry Point**: `start/reviewer.toon`

**Responsibility**: Code review and quality assurance

**When to use**: After Software Engineer creates a pull request

**Input**: Pull request number

**Output**: Review comments, approval/rejection

**Invocation**:
```bash
claude start/reviewer.toon
# When prompted, provide the PR number to review
```

---

## Typical Project Flow

```
1. Product Owner Agent
   ↓ Creates config/project.toon

2. Architect Agent
   ↓ Creates architecture + task breakdown

3. Software Engineer Agents (parallel)
   ↓ Claim tasks, implement, create PRs

4. Reviewer Agent
   ↓ Review PRs, approve or request changes

5. Merge & Complete
   ↓ Tasks marked complete, dependents unblocked

6. Repeat steps 3-5 until all tasks done
```

## How Entry Points Work

Each entry point:

1. **Loads the role definition** from `core/roles/{role}.toon`
2. **Loads configuration** from `config/*.toon` files
3. **Syncs with Git** to get latest state
4. **Executes the workflow** defined in the role
5. **Updates state via Git** commits

## Configuration Required

Before invoking agents, ensure these configuration files exist:

- `config/project.toon` - Project specification (created by Product Owner)
- `config/tech-stack.toon` - Technology stack
- `config/quality-standards.toon` - Quality requirements
- `config/workflows.toon` - Git workflow and branching strategy
- `config/team.toon` - Team structure and roles

## Adding New Agent Roles

To add a new agent role:

1. Create `core/roles/{new-role}.toon` with role definition
2. Create `start/{new-role}.toon` as entry point
3. Update `config/team.toon` to include the new role
4. Document the role in this README

## Helper Scripts

Located in `scripts/`:

- `claim-task.sh` - Atomically claim a task
- `complete-task.sh` - Mark task as completed
- `heartbeat-task.sh` - Update task heartbeat
- `release-stalled.sh` - Release stalled tasks

Engineers can use these scripts or perform Git operations directly.

## Learn More

- Framework overview: `../BOOTSTRAP.md`
- Role definitions: `../core/roles/*.toon`
- Protocols: `../core/protocols/*.toon`
- Configuration: `../config/*.toon`
