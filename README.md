# SaltBitter

SaltBitter is an innovative open-source toolkit designed for efficient data management and visualization, leveraging modern technologies for high performance and scalability.

## Features

- **Backend**: Built with FastAPI and Python for fast data processing.
- **Frontend**: Utilizes React with TypeScript for a dynamic user interface.
- **Data Visualization**: Employs D3.js and Plotly for interactive, compelling visuals.
- **Database**: Powered by PostgreSQL for robust data handling.
- **Deployment**: Docker and Kubernetes on AWS for seamless scaling.
- **Testing**: Comprehensive testing with PyTest for the backend and Jest with React Testing Library for the frontend.

## Use Cases

1. **Real-Time Data Analysis**: Ideal for financial analytics and IoT dashboards needing instant data visualization.
2. **Custom Data Dashboards**: Build tailored dashboards for business intelligence with interactive insights.
3. **Scalable Web Applications**: Deploy applications that manage and visualize large datasets efficiently.
4. **AI-Powered Insights**: Integrate machine learning for predictive analytics and deeper insights.

## Getting Started

1. **Clone the Repository**: 
   ```bash
   git clone https://github.com/vmatresu/saltbitter.git
   cd saltbitter
   ```

2. **Install Dependencies**: 
   - **Backend**: Set up a virtual environment and install the required Python packages.
   - **Frontend**: Navigate to the frontend directory and run `npm install`.

3. **Run the Application**: 
   - **Backend**: Start the FastAPI server.
   - **Frontend**: Use `npm start` to launch the React application.

4. **Deployment**: 
   - Utilize Docker and Kubernetes on AWS for deployment.

## Websites

- **saltbitter.com**: Main site for project information, documentation, and updates.
- **saltbitter.org**: Community platform for engagement, forums, and contributor resources.

## AI Agent Orchestration Framework

SaltBitter includes a cutting-edge multi-agent AI development system for autonomous, parallel software development.

### Framework Overview

The agent orchestration system enables multiple AI agents to collaborate on software development tasks using Git-native coordination and file-based state management.

#### Agent Types
- **Coordinator**: Task distribution and monitoring
- **Planner**: Architecture decisions and task decomposition
- **Coder**: Feature implementation (1-8 parallel instances)
- **Reviewer**: Code quality validation and approval
- **Tester**: Automated test execution and reporting

### Quick Start - Agent Framework

#### 1. Initialize the Framework
```bash
python .agents/init.py --max-workers 8
```

#### 2. Configure Settings (Optional)
Edit `.agents/config.yml` to customize:
- Maximum parallel workers
- Testing requirements
- Quality thresholds
- Git workflow settings

#### 3. Create Tasks
Add tasks to `.agents/tasks/queue.json`:
```json
{
  "pending": [
    {
      "id": "TASK-001",
      "title": "Implement user authentication",
      "description": "Add JWT-based authentication system",
      "priority": 8,
      "dependencies": [],
      "required_capabilities": ["python", "fastapi", "postgresql"],
      "estimated_complexity": "medium"
    }
  ]
}
```

#### 4. Start the Coordinator

**Single Coordination Cycle:**
```bash
python .agents/coordinator.py --spawn-workers --prioritize
```

**Continuous Daemon Mode:**
```bash
python .agents/coordinator.py --daemon
```

**Using GitHub Actions (Recommended):**
The coordinator runs automatically every 5 minutes via GitHub Actions when tasks are added to the queue.

### Agent Framework Features

#### File-Based Coordination
- **No External Dependencies**: Uses Git as distributed lock mechanism
- **Atomic Task Claims**: First commit wins, losers retry
- **Status Tracking**: Real-time agent status in `.agents/status/`
- **Audit Trail**: Complete history in Git log

#### GitHub Integration
- **Automated Testing**: Every feature branch push triggers tests
- **Quality Gates**: PRs require passing tests, coverage, linting
- **Auto-Review**: Reviewer agent validates code quality
- **Progress Updates**: Test results posted to agent status

#### Parallel Execution
- Up to 8 concurrent coder agents (configurable)
- Independent work on separate feature branches
- Automatic conflict detection and resolution
- Efficient resource utilization

### Monitoring Agent Activity

#### Check Agent Status
```bash
# View all agent statuses
cat .agents/registry.json

# View specific agent status
cat .agents/status/coder-001.md

# Generate status report
python .agents/coordinator.py --report
```

#### View Logs
```bash
# Coordinator logs
tail -f .agents/logs/coordinator.log

# Specific agent logs
tail -f .agents/logs/coder-001.log
```

### Managing Agents

#### Scale Workers
```bash
# Scale to 10 workers
python .agents/coordinator.py --scale-workers 10

# Scale down to 3 workers
python .agents/coordinator.py --scale-workers 3
```

#### Shutdown Agents
```bash
# Graceful shutdown (5min grace period)
python .agents/coordinator.py --shutdown --grace-period 300

# Force shutdown
python .agents/coordinator.py --shutdown --force
```

### Agent Development Workflow

1. **Task Creation**: Add task to queue with requirements
2. **Automatic Claim**: Idle agent claims highest priority task
3. **Branch Creation**: Agent creates `feature/TASK-{id}-{slug}` branch
4. **Implementation**: Agent implements feature incrementally
5. **Testing**: Continuous testing with coverage validation
6. **Review**: Reviewer agent validates quality
7. **Merge**: Automated merge after approval
8. **Completion**: Task marked complete, agent returns to idle

### Project Context for Agents

All agents read `AGENTS.md` for:
- Code standards and style guide
- Testing requirements
- Architecture patterns
- Integration points
- Completion criteria

Update `AGENTS.md` as your project evolves to ensure agents follow current best practices.

### GitHub Actions Workflows

The framework includes four automated workflows:

1. **agent-orchestrator.yml**: Runs coordinator every 5 minutes
2. **feature-test.yml**: Tests every feature branch push
3. **merge-gate.yml**: Quality gate for PRs to main
4. **agent-cleanup.yml**: Daily cleanup of timed-out agents

### Configuration Files

- `.agents/config.yml`: System configuration
- `.agents/registry.json`: Active agent registry
- `.agents/tasks/queue.json`: Task queue
- `AGENTS.md`: Universal project context

### Requirements

**Python Dependencies:**
```bash
pip install pyyaml
```

**Optional (for full functionality):**
```bash
pip install pytest pytest-cov pytest-asyncio ruff mypy bandit safety
```

**GitHub CLI (for PR creation):**
```bash
# macOS
brew install gh

# Linux
sudo apt install gh
```

### Advanced Usage

#### Custom Agent Capabilities
Edit `.agents/config.yml` to define custom capabilities:
```yaml
capabilities:
  available:
    - python
    - fastapi
    - react
    - typescript
    - custom-domain-knowledge
```

#### Task Dependencies
Tasks can depend on other tasks:
```json
{
  "id": "TASK-002",
  "title": "Password reset flow",
  "dependencies": ["TASK-001"],
  ...
}
```

#### Priority Management
Higher priority tasks are claimed first (1-10 scale, 10 = highest):
```json
{
  "priority": 9,
  ...
}
```

### Troubleshooting

**Agents not claiming tasks:**
- Check `.agents/registry.json` for active agents
- Verify tasks match agent capabilities
- Check dependencies are met

**Tests failing in CI:**
- Review `.agents/status/{agent-id}.md` for details
- Check GitHub Actions logs
- Verify local tests pass

**Merge conflicts:**
- Coordinator detects conflicts automatically
- Planner agent creates resolution tasks
- Manual intervention may be needed for complex conflicts

### Security Considerations

- Never commit `.env` files with secrets
- Use GitHub Secrets for sensitive credentials
- Agents respect `.gitignore` patterns
- All agent actions are auditable via Git history

## Contribution

We welcome contributions! Please fork the repository and submit a pull request.

For agent-assisted development:
1. Add your task to `.agents/tasks/queue.json`
2. Let agents implement, test, and review
3. Human approval for final merge (recommended)

## License

This project is licensed under the MIT License. See the LICENSE file for details.
