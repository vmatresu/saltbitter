# SaltBitter Projects

This directory contains specifications for individual apps within the SaltBitter collection.

## Active Projects

### 1. Dating Platform (`dating-platform.toon`)
**Status**: Ready for architecture breakdown
**Description**: Psychology-informed ethical dating platform
**Docs**: `docs/dating-platform/`

## Project Structure

Each project gets:
- Project specification: `.agents/projects/{app-name}.toon`
- Architecture: `.agents/projects/{app-name}/architecture.toon`
- Tasks: `.agents/projects/{app-name}/tasks/TASK-*.toon`
- Claimed tasks: `.agents/claimed/{app-name}/TASK-*.toon`
- Completed tasks: `.agents/completed/{app-name}/TASK-*.toon`

## Adding New Projects

1. Product Owner creates `.agents/projects/{app-name}.toon`
2. Architect creates architecture + tasks
3. Software Engineers implement
4. Reviewers validate

---

**Current Focus**: Dating Platform (Phase 1)
