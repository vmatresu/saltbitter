# PR Merge Workflow for Multi-Agent System

## 🔄 **Automated Task Completion (Recommended)**

The multi-agent framework now includes **automatic task completion** when PRs are merged.

### How It Works

1. **Agent creates PR with TASK-XXX in title**
   ```bash
   gh pr create --base develop --title "TASK-002: Implement JWT authentication" --body "..."
   ```

2. **You merge the PR** (to `develop` or `main`)
   ```bash
   # Via GitHub UI or CLI
   gh pr merge 123 --squash
   ```

3. **GitHub Actions automatically:**
   - ✅ Detects the TASK-XXX from PR title/branch/body
   - ✅ Moves task from `.agents/claimed/` or `.agents/tasks/` to `.agents/completed/`
   - ✅ Adds completion metadata (PR URL, timestamp, etc.)
   - ✅ Unblocks dependent tasks (changes `status: blocked` → `status: ready`)
   - ✅ Commits and pushes changes
   - ✅ Comments on the PR confirming completion

### Requirements for Automation

✅ **PR title MUST include `TASK-XXX`**
✅ **PR must be merged (not closed)**
✅ **PR must target `develop` or `main` branch**

---

## 📋 **Manual Completion (If Automation Fails)**

If the GitHub Action doesn't run or fails, manually complete the task:

### Option 1: Use Helper Script

```bash
# On develop branch
git checkout develop
git pull origin develop

# Complete the task
./agents/scripts/complete-task.sh TASK-002 agent-engineer-123 https://github.com/user/repo/pull/8 dating-platform

# This script automatically:
# - Moves task to completed/
# - Adds completion metadata
# - Unblocks dependent tasks
# - Commits and pushes
```

### Option 2: Manual Process

```bash
# 1. Switch to develop
git checkout develop
git pull origin develop

# 2. Move task file
mv .agents/claimed/dating-platform/TASK-002.toon .agents/completed/dating-platform/TASK-002.toon

# Or if task is still in tasks/:
mv .agents/projects/dating-platform/tasks/TASK-002.toon .agents/completed/dating-platform/TASK-002.toon

# 3. Add completion metadata to the task file
cat >> .agents/completed/dating-platform/TASK-002.toon <<EOF

completion:
 status: completed
 completed_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
 completed_by: agent-engineer-123
 pr_url: https://github.com/user/repo/pull/8
 pr_number: 8
 merged_to: develop
EOF

# 4. Unblock dependent tasks
# Check which tasks depend on TASK-002:
grep -l "TASK-002" .agents/projects/dating-platform/tasks/*.toon

# For each blocked task that only depends on completed tasks:
sed -i 's/status: blocked/status: ready/' .agents/projects/dating-platform/tasks/TASK-003.toon

# 5. Commit and push
git add .agents/completed/ .agents/claimed/ .agents/projects/
git commit -m "[COMPLETE] Mark TASK-002 as completed (PR #8)"
git push origin develop
```

---

## ⚠️ **Common Issues & Solutions**

### Issue 1: "Task still shows as claimed/blocked"

**Cause**: PR was merged but task wasn't completed
**Solution**: Run manual completion (see above)

### Issue 2: "GitHub Action didn't run"

**Possible causes:**
- PR title doesn't include `TASK-XXX` ← **Most common**
- PR was closed without merging
- GitHub Actions are disabled
- Workflow file has syntax error

**Solution**: Check PR title format and run manual completion if needed

### Issue 3: "Dependent tasks not unblocked"

**Cause**: Task completion didn't update dependent task statuses
**Solution**: Manually check and update:

```bash
# Find tasks that depend on TASK-002
grep -l "TASK-002" .agents/projects/dating-platform/tasks/*.toon

# Check if all dependencies are complete
# Update status to ready if all dependencies are in completed/
```

---

## 🎯 **Best Practices**

### For Agents

1. **Always include TASK-XXX in PR title**
   ```
   ✅ GOOD: "TASK-002: Implement JWT authentication"
   ❌ BAD:  "Implement authentication system"
   ```

2. **Create PR to `develop` branch**
   ```bash
   gh pr create --base develop --title "TASK-002: ..."
   ```

3. **Wait for automation or manually complete**
   - Check if task moved to `.agents/completed/` after merge
   - If not, run `./agents/scripts/complete-task.sh`

### For Humans Merging PRs

1. **Verify PR title has TASK-XXX**
   - If missing, edit the PR title before merging
   - Or manually complete the task after merge

2. **Merge to `develop` first**
   - Individual tasks merge to `develop`
   - Periodic releases: `develop` → `main`

3. **Verify automation ran**
   - Check for comment from github-actions[bot]
   - Check task moved to `.agents/completed/`
   - If not, run manual completion

---

## 📊 **Workflow Diagram**

```
┌─────────────────────────────────────────────────────────┐
│ Agent Claims Task                                        │
│ .agents/projects/{project}/tasks/TASK-XXX.toon          │
│              ↓                                           │
│ .agents/claimed/{project}/TASK-XXX.toon                 │
└─────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ Agent Implements on Feature Branch                       │
│ feature/TASK-XXX-description                            │
└─────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ Agent Creates PR                                         │
│ Title: "TASK-XXX: Description"                          │
│ Base: develop                                           │
└─────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ Human/Reviewer Merges PR                                 │
└─────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ 🤖 GitHub Action Runs Automatically                     │
│ - Detects TASK-XXX in PR                                │
│ - Moves to .agents/completed/{project}/TASK-XXX.toon    │
│ - Adds completion metadata                              │
│ - Unblocks dependent tasks                              │
│ - Commits and pushes                                    │
│ - Comments on PR                                        │
└─────────────────────────────────────────────────────────┘
                      ↓
              ✅ Task Complete!
```

---

## 🔍 **Troubleshooting Commands**

```bash
# Check task status
ls -la .agents/claimed/dating-platform/
ls -la .agents/completed/dating-platform/
ls -la .agents/projects/dating-platform/tasks/

# Find a specific task
find .agents -name "TASK-002.toon" -type f

# Check task dependencies
grep -A 5 "required\[" .agents/projects/dating-platform/tasks/TASK-003.toon

# Check which tasks are ready
grep "status: ready" .agents/projects/dating-platform/tasks/*.toon

# Check GitHub Action logs
gh run list --workflow=auto-complete-task.yml --limit 5
gh run view <run-id> --log
```

---

## ✅ **Checklist for PR Merge**

- [ ] PR title includes `TASK-XXX`
- [ ] PR is merged to `develop` (not main)
- [ ] GitHub Action comment appears on PR
- [ ] Task file moved to `.agents/completed/`
- [ ] Dependent tasks show `status: ready`
- [ ] If automation failed, manual completion done

---

## 📞 **Need Help?**

- Check GitHub Action logs: `gh run list --workflow=auto-complete-task.yml`
- Verify automation setup: `.github/workflows/auto-complete-task.yml`
- Run manual completion: `./agents/scripts/complete-task.sh`
- Review this guide: `.agents/PR_MERGE_WORKFLOW.md`
