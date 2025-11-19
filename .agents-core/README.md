# .agents-core: Portable Multi-Agent Coordination Framework

**Drop-in framework for enabling LLM agents to autonomously develop software via Git coordination.**

[![Version](https://img.shields.io/badge/version-1.0.0-blue)](VERSION.toon)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![TOON](https://img.shields.io/badge/format-TOON-purple)](https://github.com/toon-format/toon)

---

## What is .agents-core?

A **framework** that allows multiple AI agents (Claude, GPT-4, etc.) to work together on software projects by coordinating through Git commits. No databases, no servers, no complex infrastructure—just Git + TOON files.

**Key Innovation**: Agents are stateless and autonomous. They claim tasks atomically (first-commit-wins), implement features, create PRs, and complete work—all coordinated via Git's atomic operations.

---

## Quick Start (3 Commands)

```bash
# 1. Copy framework to your project
cp -r .agents-core /path/to/your-project/

# 2. Configure your project
cd /path/to/your-project
# Edit config/project.toon (define what you're building)
# Edit config/tech-stack.toon (specify technologies)

# 3. Run the architect to create tasks
claude .agents-core/start/architect.toon
```

**Done!** Your project now has a backlog of tasks that agents can implement.

📖 **[Read the full Bootstrap Guide](BOOTSTRAP.md)** for complete setup instructions.

---

## How It Works

```
1. Product Owner Agent → Defines requirements (config/project.toon)
2. Architect Agent → Designs system + creates task breakdown
3. Software Engineer Agents → Claim tasks, implement, create PRs (in parallel)
4. Reviewer Agent → Reviews PRs, approves or requests changes
5. Repeat until all tasks complete
```

**Atomic Coordination**: Git's atomic push ensures only one agent claims each task (first-commit-wins pattern).

**Stateless Agents**: Each agent invocation is independent. All context loaded from Git files.

**Parallel Execution**: Multiple engineers work simultaneously on independent tasks.

---

## Features

✅ **Portable**: Copy `.agents-core/` to **any** repository to enable multi-agent coordination
✅ **Git-Native**: All coordination through Git commits (no external database)
✅ **TOON Format**: 40% fewer tokens than JSON for agent context
✅ **Role-Based**: Product Owner → Architect → Engineers → Reviewers
✅ **Stateless**: Each agent invocation independent, full context from Git
✅ **Parallel**: Multiple agents work simultaneously on independent tasks
✅ **Dependencies**: Automatic task unlocking when dependencies complete
✅ **Zero Infrastructure**: No database, no servers, just Git

---

## Framework Structure

```
.agents-core/
├── config/                    # USER EDITS: Project configuration
│   ├── project.toon           # What you're building
│   ├── tech-stack.toon        # Technologies (Python/Node/Go, etc)
│   ├── quality-standards.toon # Coverage, linters, security
│   ├── workflows.toon         # Git branching strategy
│   └── team.toon              # Agent roles
│
├── core/                      # FRAMEWORK LOGIC (don't edit)
│   ├── protocols/             # Task lifecycle, Git coordination
│   ├── templates/             # Schemas for tasks, projects
│   └── roles/                 # Agent behavior definitions
│
├── scripts/                   # HELPERS (optional)
│   ├── claim-task.sh          # Atomic task claiming
│   ├── complete-task.sh       # Mark task complete
│   ├── heartbeat-task.sh      # Update heartbeat
│   └── release-stalled.sh     # Release stale tasks
│
├── state/                     # DYNAMIC (Git-tracked)
│   └── {project}/             # Created by architect
│       ├── architecture.toon  # System design
│       ├── tasks/             # Available tasks
│       ├── claimed/           # In-progress
│       └── completed/         # Done
│
└── start/                     # ENTRY POINTS
    ├── product-owner.toon     # Define requirements
    ├── architect.toon         # Design & create tasks
    ├── engineer.toon          # Implement features
    └── reviewer.toon          # Review PRs
```

---

## Example Projects

### Dating Platform (Complex)
- **Tech**: Python + FastAPI + PostgreSQL + React
- **Features**: AI companions, matching algorithm, compliance (GDPR, EU AI Act)
- **Tasks**: 25 tasks, 6-month timeline
- **Config**: See existing `.agents/` in this repository

### Todo App (Simple)
- **Tech**: Node.js + Express + React
- **Features**: Basic CRUD, lists, search
- **Tasks**: 8 tasks, 4-week timeline
- **Config**: See [EXAMPLE-TODO-APP.md](EXAMPLE-TODO-APP.md)

### Same Framework, Different Projects!
Only `config/*.toon` files change. Core framework remains identical.

---

## Portability Test

The framework is **100% portable**:

```bash
# Initialize in Todo App
cd ~/todo-app
cp -r .agents-core .
# Edit config/project.toon → "Todo App requirements"
claude .agents-core/start/architect.toon
# → Creates todo-app tasks

# Initialize in Crypto Exchange
cd ~/crypto-exchange
cp -r .agents-core .
# Edit config/project.toon → "Trading platform requirements"
claude .agents-core/start/architect.toon
# → Creates crypto-exchange tasks
```

**Proven**: Used for dating platform (25 tasks), easily adapts to todo app (8 tasks), crypto exchange, e-commerce, data pipelines, etc.

---

## Atomic Task Claiming (Race-Free)

Multiple agents can run simultaneously. Git's atomic push ensures only one claims each task:

```bash
# Engineer A
git pull
mv state/proj/tasks/TASK-001.toon state/proj/claimed/
git commit && git push  # ✓ SUCCESS

# Engineer B (same time)
git pull
mv state/proj/tasks/TASK-001.toon state/proj/claimed/
git commit && git push  # ✗ CONFLICT (A won)
git reset && git pull   # Try TASK-002 instead
```

---

## Success Criteria

| Criterion | Status | Implementation |
|-----------|--------|----------------|
| **Portability** | ✅ | Drop into any repo, edit `config/*.toon` |
| **Scalability** | ✅ | Add roles by creating `core/roles/{new-role}.toon` |
| **Autonomy** | ✅ | Agents self-assign from task pool |
| **No App Logic** | ✅ | Zero dating-app code in framework |
| **Parallelization** | ✅ | Multiple agents work simultaneously |
| **Dependencies** | ✅ | Automatic unlocking when deps complete |

---

## Documentation

- **[BOOTSTRAP.md](BOOTSTRAP.md)** - Complete initialization guide
- **[VERSION.toon](VERSION.toon)** - Framework version and changelog
- **[framework_manifest.toon](framework_manifest.toon)** - File inventory
- **[EXAMPLE-TODO-APP.md](EXAMPLE-TODO-APP.md)** - Portability demonstration

### Per-Directory READMEs
- **[config/](config/)** - Configuration files
- **[core/protocols/](core/protocols/)** - Coordination protocols
- **[core/roles/](core/roles/)** - Agent role definitions
- **[core/templates/](core/templates/)** - File templates
- **[scripts/](scripts/README.md)** - Helper scripts
- **[start/](start/README.md)** - Agent entry points
- **[state/](state/README.md)** - Dynamic task state

---

## Key Concepts

### 1. Stateless Agents
Each agent invocation is independent. All context loaded from Git files. No memory between invocations.

### 2. Atomic Operations
Git's atomic push prevents race conditions. First agent to push wins, others retry.

### 3. Task Lifecycle
```
ready → claimed → completed
  ↑         ↓
  └─────────┘ (on timeout)
```

### 4. Dependencies
Tasks can depend on others. Automatic unlocking when dependencies complete.

### 5. Heartbeats
Agents send heartbeats every 10-15 minutes. Tasks without heartbeat for 30+ minutes auto-released.

---

## Adding New Agent Roles

Want a Security Auditor? Data Engineer? UX Designer?

```bash
# 1. Define role behavior
core/roles/security-auditor.toon

# 2. Create entry point
start/security-auditor.toon

# 3. Update team config
config/team.toon

# 4. Done! Invoke with:
claude start/security-auditor.toon
```

---

## Technology Stack

- **Language**: TOON (Token-Oriented Object Notation)
- **Coordination**: Git (2.0+)
- **LLMs**: Claude Sonnet 4, Opus 4, GPT-4
- **Platforms**: GitHub, GitLab, Bitbucket
- **Infrastructure**: None (Git is the only infrastructure)

---

## Observability

Monitor progress:

```bash
# Count tasks by status
echo "Ready: $(ls state/{project}/tasks/*.toon | wc -l)"
echo "Claimed: $(ls state/{project}/claimed/*.toon | wc -l)"
echo "Completed: $(ls state/{project}/completed/*.toon | wc -l)"

# View agent activity
git log --grep="\[AGENT-"

# View claims
git log --grep="\[AGENT-CLAIM\]"

# View completions
git log --grep="\[AGENT-COMPLETE\]"
```

---

## Advantages

| Feature | Traditional | .agents-core |
|---------|-------------|--------------|
| **Coordination** | Database + API | Git commits |
| **State** | PostgreSQL, Redis | TOON files in Git |
| **Agents** | Stateful workers | Stateless invocations |
| **Scalability** | Need infrastructure | Just add agents |
| **Observability** | Logs + dashboards | Git log |
| **Cost** | Database + servers | $0 infrastructure |
| **Portability** | Custom per project | Copy `.agents-core/` |

---

## License

MIT License - Free to use, modify, and distribute.

---

## Contributing

This framework was extracted from the [SaltBitter dating platform](https://github.com/vmatresu/saltbitter) to make it portable and reusable.

Contributions welcome! Areas for improvement:
- Additional agent roles (security, UX, data engineering)
- Additional protocols (e.g., automated testing, deployment)
- More examples (mobile apps, data pipelines, etc.)
- Better observability tools
- Integration with CI/CD platforms

---

## Version

**Current**: 1.0.0 (2025-11-19)

See [VERSION.toon](VERSION.toon) for changelog.

---

## Repository

**Source**: https://github.com/vmatresu/saltbitter

**Framework**: `.agents-core/` directory

---

## Questions?

- 📖 Read [BOOTSTRAP.md](BOOTSTRAP.md) for setup guide
- 📝 See [framework_manifest.toon](framework_manifest.toon) for file inventory
- 💡 Check [EXAMPLE-TODO-APP.md](EXAMPLE-TODO-APP.md) for portability demo
- 🔍 Explore `core/protocols/*.toon` for deep dive

---

**Built with**: Claude Sonnet 4 + Git + TOON
**Paradigm**: Git-native stateless multi-agent coordination
**Status**: Production-ready ✅
