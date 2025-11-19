# Example: Using .agents-core for a Todo App

This example demonstrates how to configure `.agents-core` for a completely different project type (a simple todo application).

## Portability Test

The **same framework** works for:
- ✅ Dating Platform (complex, AI-powered, compliance-heavy)
- ✅ Todo App (simple, CRUD, straightforward)
- ✅ Crypto Exchange (high-performance, real-time)
- ✅ Any other software project

Only `config/*.toon` files change!

---

## Configuration Example: Todo App

### config/project.toon

```toon
project:
 id: todo-app
 name: Simple Todo Application
 tagline: Clean and fast task management
 version: 1.0.0
 status: planning

mission:
 primary: Build the simplest, fastest todo app
 approach: Focus on speed and simplicity
 north_star_metric: 1-second task creation

business_goals[3]:
 Launch MVP in 4 weeks
 Support 10,000 users
 Mobile-first design

user_stories[8]{id,role,action,benefit,priority}:
 US-001,user,create a todo,track my tasks,10
 US-002,user,mark todo as complete,see progress,10
 US-003,user,edit a todo,fix mistakes,9
 US-004,user,delete a todo,remove unwanted tasks,9
 US-005,user,filter todos by status,focus on active items,8
 US-006,user,set due dates,meet deadlines,7
 US-007,user,organize todos in lists,categorize work,6
 US-008,user,search todos,find specific tasks,5

technical_constraints:
 stack:
  backend: Node.js 20 + Express
  frontend: React 18 + TypeScript
  database: PostgreSQL 15
  infrastructure: Vercel (serverless)

 performance:
  api_response_p95_ms: 100
  page_load_ms: 800

 security:
  authentication: JWT
  encryption: HTTPS only

quality_standards:
 code_coverage_min_percent: 80
 required_checks[5]:
  All tests passing
  Linting clean (ESLint)
  Type checking clean (TypeScript)
  Build succeeds
  No security vulnerabilities

success_metrics[3]{metric,target}:
 Daily active users,1000
 Task creation latency,< 1 second
 User satisfaction,> 4.5/5

implementation_phases:
 phase_1_mvp:
  duration_weeks: 4
  deliverables[4]:
   User authentication
   CRUD operations for todos
   Basic frontend
   Deployment to Vercel

metadata:
 created_at: 2025-11-19T00:00:00Z
 created_by: product-owner-agent
 next_step: architect-creates-tasks
```

### config/tech-stack.toon

```toon
tech_stack:
 description: Todo App Technology Stack
 version: 1.0.0

backend:
 language: Node.js 20
 framework: Express.js 4.18
 orm: Prisma
 testing:
  framework: Jest
  coverage_tool: Jest --coverage
 linter: ESLint
 type_checker: TypeScript tsc
 formatter: Prettier

frontend:
 language: TypeScript 5.0+
 framework: React 18
 styling: TailwindCSS 3.0
 state_management: React Context + Hooks
 routing: React Router 6
 testing:
  framework: Jest + React Testing Library
  coverage_tool: Jest --coverage
 linter: ESLint
 formatter: Prettier
 build_tool: Vite

database:
 primary: PostgreSQL 15
 migrations: Prisma Migrate
 connection_pooling: Prisma

infrastructure:
 hosting: Vercel (serverless)
 database_hosting: Vercel Postgres
 ci_cd: GitHub Actions
 monitoring: Vercel Analytics

api_design:
 style: REST
 versioning: /api/v1/
 documentation: OpenAPI 3.0
 authentication: JWT Bearer tokens

dependencies:
 backend_key_packages[5]:
  express
  prisma
  jsonwebtoken
  bcrypt
  jest

 frontend_key_packages[6]:
  react
  react-dom
  react-router-dom
  typescript
  tailwindcss
  vite

metadata:
 created_at: 2025-11-19T00:00:00Z
```

### config/quality-standards.toon

```toon
quality_standards:
 description: Todo App Quality Requirements
 version: 1.0.0

test_coverage:
 backend_minimum_percent: 80
 frontend_minimum_percent: 75

linting:
 backend:
  tool: ESLint
  config: .eslintrc.json
  enforcement: Zero errors allowed

 frontend:
  tool: ESLint
  config: .eslintrc.json
  enforcement: Zero errors allowed

formatting:
 tool: Prettier
 enforcement: Auto-format on commit

type_checking:
 tool: TypeScript compiler
 mode: strict
 enforcement: Zero type errors

security_scanning:
 backend:
  tool: npm audit
  enforcement: No high vulnerabilities

 frontend:
  tool: npm audit
  enforcement: No high vulnerabilities

performance_requirements:
 api:
  response_time_p95_ms: 100

 frontend:
  lighthouse_performance_score: 95
  first_contentful_paint_ms: 800

ci_cd_requirements:
 all_checks_must_pass[5]:
  Backend tests
  Frontend tests
  Linting (both)
  Type checking
  Build succeeds

metadata:
 created_at: 2025-11-19T00:00:00Z
```

### config/workflows.toon

(Usually no changes needed - use default git-flow)

### config/team.toon

(Usually no changes needed - use default roles)

---

## What the Architect Would Create

After running `claude start/architect.toon`, the architect would generate:

### state/todo-app/architecture.toon

```toon
architecture:
 name: Todo App Architecture
 style: Monolith with REST API

layers[3]{name,tech,purpose}:
 frontend,React+TypeScript,User interface
 backend,Node.js+Express,REST API
 data,PostgreSQL+Prisma,Data persistence

components[4]{name,responsibility,apis}:
 auth_service,User authentication,"POST /api/auth/register POST /api/auth/login"
 todo_service,Todo CRUD operations,"GET/POST/PUT/DELETE /api/todos"
 list_service,List management,"GET/POST/PUT/DELETE /api/lists"
 user_service,User profile management,"GET/PUT /api/users/{id}"

data_models[3]{table,key_fields}:
 users,"id,email,password_hash,created_at"
 todos,"id,user_id,title,description,completed,due_date,created_at"
 lists,"id,user_id,name,created_at"

dependencies:
 todo_service: [auth_service]
 list_service: [auth_service]
 user_service: [auth_service]

infrastructure:
 hosting: Vercel (serverless functions)
 database: Vercel Postgres
 cdn: Vercel Edge Network
 monitoring: Vercel Analytics

api_design:
 style: REST
 endpoints[12]:
  POST /api/auth/register
  POST /api/auth/login
  GET /api/todos
  POST /api/todos
  GET /api/todos/{id}
  PUT /api/todos/{id}
  DELETE /api/todos/{id}
  GET /api/lists
  POST /api/lists
  GET /api/lists/{id}
  PUT /api/lists/{id}
  DELETE /api/lists/{id}

metadata:
 created_at: 2025-11-19T00:00:00Z
 created_by: architect-agent
```

### state/todo-app/tasks/TASK-001.toon

```toon
task:
 id: TASK-001
 project: todo-app
 title: Implement user authentication system
 type: feature
 priority: 10
 status: ready

description:
 summary: Build JWT-based authentication
 details: |
  - POST /api/auth/register (create user)
  - POST /api/auth/login (return JWT)
  - Password hashing with bcrypt
  - JWT middleware for protected routes

acceptance_criteria[5]:
 Registration endpoint creates user and returns 201
 Login returns valid JWT token
 Passwords hashed with bcrypt
 JWT middleware validates tokens
 Unit test coverage ≥80%

dependencies:
 required[0]:
 blocks[3]:
  TASK-002
  TASK-003
  TASK-004

context:
 files_to_create[4]:
  backend/routes/auth.js
  backend/models/User.js
  backend/middleware/auth.js
  backend/tests/auth.test.js

technical_details:
 database_tables[1]:
  users(id SERIAL PK,email VARCHAR UNIQUE,password_hash VARCHAR,created_at TIMESTAMP)
 api_endpoints[2]:
  POST /api/auth/register
  POST /api/auth/login
 dependencies[2]:
  jsonwebtoken
  bcrypt

metadata:
 created_by: architect-agent
 created_at: 2025-11-19T00:00:00Z
 estimated_hours: 4
 complexity: medium
```

### state/todo-app/tasks/TASK-002.toon

```toon
task:
 id: TASK-002
 project: todo-app
 title: Implement todo CRUD operations
 type: feature
 priority: 9
 status: pending

description:
 summary: Build REST API for todo management
 details: |
  - GET /api/todos (list user's todos)
  - POST /api/todos (create new todo)
  - GET /api/todos/{id} (get single todo)
  - PUT /api/todos/{id} (update todo)
  - DELETE /api/todos/{id} (delete todo)
  - PATCH /api/todos/{id}/complete (mark complete)

acceptance_criteria[6]:
 All CRUD endpoints implemented
 Todos filtered by authenticated user
 Validation on required fields
 Tests for all endpoints
 Coverage ≥80%
 Error handling for not found

dependencies:
 required[1]:
  TASK-001

context:
 files_to_create[3]:
  backend/routes/todos.js
  backend/models/Todo.js
  backend/tests/todos.test.js

metadata:
 estimated_hours: 5
 complexity: medium
```

---

## Task Breakdown (Generated by Architect)

The architect would create ~8 tasks:

1. **TASK-001**: Authentication (Priority 10, Ready)
2. **TASK-002**: Todo CRUD (Priority 9, Pending - depends on TASK-001)
3. **TASK-003**: List Management (Priority 8, Pending)
4. **TASK-004**: Frontend Auth UI (Priority 9, Pending)
5. **TASK-005**: Frontend Todo UI (Priority 9, Pending)
6. **TASK-006**: Search & Filter (Priority 6, Pending)
7. **TASK-007**: Due Date Reminders (Priority 5, Pending)
8. **TASK-008**: Deploy to Vercel (Priority 7, Pending)

---

## Comparison: Dating Platform vs Todo App

| Aspect | Dating Platform | Todo App |
|--------|----------------|----------|
| **Complexity** | High (AI, compliance, real-time) | Low (CRUD, simple state) |
| **Backend** | Python + FastAPI | Node.js + Express |
| **Database** | PostgreSQL + Redis | PostgreSQL only |
| **Infrastructure** | AWS (ECS, RDS, S3, CloudFront) | Vercel (serverless) |
| **Tasks** | 25 tasks | 8 tasks |
| **Dependencies** | Complex (many blockers) | Simple (linear) |
| **Quality Bar** | 85% coverage, strict security | 80% coverage, standard |
| **Timeline** | 6 months | 4 weeks |

**Same Framework**: Only `config/*.toon` changed!

---

## Running the Example

```bash
# 1. Copy framework
cp -r .agents-core /path/to/todo-app/

# 2. Copy example configs
cd /path/to/todo-app
cp .agents-core/EXAMPLE-TODO-APP.md config-example.md
# Edit config/project.toon, config/tech-stack.toon per above

# 3. Run architect
claude .agents-core/start/architect.toon

# 4. Verify output
ls state/todo-app/tasks/
# Should see TASK-001.toon through TASK-008.toon

# 5. Run engineer
claude .agents-core/start/engineer.toon
# Claims TASK-001, implements auth, creates PR

# 6. Continue until all tasks done
```

---

## Portability Verified

This example proves:

✅ **Framework is truly portable** - same code works for different projects
✅ **Configuration-driven** - only edit `config/*.toon`
✅ **Tech stack agnostic** - Python or Node, FastAPI or Express, AWS or Vercel
✅ **Scalable** - works for 8 tasks or 800 tasks
✅ **Role-based** - same agent roles regardless of project

---

**Framework**: .agents-core v1.0.0
**Example**: Todo App (minimal configuration)
**Purpose**: Demonstrate portability
