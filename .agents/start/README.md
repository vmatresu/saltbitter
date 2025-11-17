# Agent Entry Points

This directory contains self-contained entry points for each agent role. To instantiate an agent, simply point it to the appropriate file.

## Usage

### Universal Prompt Template

```
You are an expert agent LLM using a Git-native multi-agent coordination framework.

Your starting point is: .agents/start/{role}.toon

Read that file completely and follow all instructions. Everything you need is in the Git repository.
```

## Available Agent Roles

### Software Engineer
**Entry Point**: `.agents/start/software-engineer.toon`

**Prompt**:
```
You are an expert agent LLM using a Git-native multi-agent coordination framework.

Your starting point is: .agents/start/software-engineer.toon

Read that file completely and follow all instructions. Everything you need is in the Git repository.
```

**What they do**: Claim tasks, implement code, write tests, create PRs

---

### Product Owner
**Entry Point**: `.agents/start/product-owner.toon`

**Prompt**:
```
You are an expert agent LLM using a Git-native multi-agent coordination framework.

Your starting point is: .agents/start/product-owner.toon

Read that file completely and follow all instructions. Everything you need is in the Git repository.
```

**What they do**: Define requirements, create project specifications, set priorities

---

### Architect
**Entry Point**: `.agents/start/architect.toon`

**Prompt**:
```
You are an expert agent LLM using a Git-native multi-agent coordination framework.

Your starting point is: .agents/start/architect.toon

Read that file completely and follow all instructions. Everything you need is in the Git repository.
```

**What they do**: Design system architecture, break down into tasks, set dependencies

---

### Reviewer
**Entry Point**: `.agents/start/reviewer.toon`

**Prompt**:
```
You are an expert agent LLM using a Git-native multi-agent coordination framework.

Your starting point is: .agents/start/reviewer.toon

Read that file completely and follow all instructions. Everything you need is in the Git repository.
```

**What they do**: Review PRs, verify quality standards, approve or request changes

---

## How It Works

1. **Agent reads entry point**: Complete self-contained instructions
2. **Agent explores Git repo**: All coordination through file structure
3. **Agent takes action**: Follows workflow from entry point
4. **Agent coordinates via Git**: Commits, PRs, atomic operations

## Current Project Status

- **dating-platform**: Architecture complete, 24 tasks ready for engineers
- **First available task**: TASK-001 (AWS infrastructure, no dependencies)

## Philosophy

- **Git is the coordination layer**: No databases, no shared processes
- **Entry points are self-documenting**: Agent bootstraps from single file
- **TOON format**: 40% token savings for LLM prompts
- **Atomic operations**: First-commit-wins prevents conflicts
- **Stateless agents**: Each invocation is independent

## Quick Start

To start a Software Engineer agent right now:

```
You are an expert agent LLM using a Git-native multi-agent coordination framework.

Your starting point is: .agents/start/software-engineer.toon

Read that file completely and follow all instructions. Everything you need is in the Git repository.
```

That's it! The agent will read the entry point and self-coordinate through Git.
