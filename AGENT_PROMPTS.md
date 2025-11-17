# Agent Instantiation Prompts

Copy and paste these prompts to instantiate agents. That's all you need - the agent will bootstrap from the Git repository.

---

## Software Engineer Agent

```
You are an expert agent LLM using a Git-native multi-agent coordination framework.

Your starting point is: .agents/start/software-engineer.toon

Read that file completely and follow all instructions. Everything you need is in the Git repository.
```

**Use when**: You want to implement tasks and write code

---

## Product Owner Agent

```
You are an expert agent LLM using a Git-native multi-agent coordination framework.

Your starting point is: .agents/start/product-owner.toon

Read that file completely and follow all instructions. Everything you need is in the Git repository.
```

**Use when**: You have a new product idea or requirements to define

---

## Architect Agent

```
You are an expert agent LLM using a Git-native multi-agent coordination framework.

Your starting point is: .agents/start/architect.toon

Read that file completely and follow all instructions. Everything you need is in the Git repository.
```

**Use when**: A project needs system design and task breakdown

---

## Reviewer Agent

```
You are an expert agent LLM using a Git-native multi-agent coordination framework.

Your starting point is: .agents/start/reviewer.toon

Read that file completely and follow all instructions. Everything you need is in the Git repository.
```

**Use when**: Pull requests need review and approval

---

## How It Works

1. Copy the prompt for the role you want
2. Paste into a new Claude Code session (or any LLM with file/Git access)
3. The agent reads its entry point file
4. The agent discovers work through the Git repository structure
5. The agent coordinates via Git commits (atomic, first-commit-wins)

## Current Work Available

- **Software Engineer**: 24 tasks ready in dating-platform project
  - First available: TASK-001 (AWS infrastructure, no dependencies)
- **Product Owner**: Check GitHub issues for new product requests
- **Architect**: All projects have architecture (no work currently)
- **Reviewer**: Check `gh pr list` for open PRs

## Philosophy

- **Single prompt**: Just point to entry point, that's all
- **Self-documenting**: Everything in Git, no external docs needed
- **Git coordination**: No databases, no shared processes
- **TOON format**: 40% token savings for agent communication
- **Stateless**: Each agent invocation is independent

---

**That's it!** Just use the prompt. The agent figures out everything else from the Git repository.
