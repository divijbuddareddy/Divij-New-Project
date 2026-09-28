# StartupOps AI — REST & SSE API Reference

## Base URL
`/api/v1`

## Authentication
Bearer token in `Authorization: Bearer <JWT_TOKEN>` with header `X-Workspace-Id: <WORKSPACE_ID>`.

---

### 1. Workspace & Auth
- `POST /api/v1/auth/register` — Register user account.
- `POST /api/v1/auth/login` — Authenticate and receive JWT.
- `GET /api/v1/workspaces` — List workspaces for the authenticated user.
- `POST /api/v1/workspaces` — Create a new workspace.
- `GET /api/v1/workspaces/{id}` — Retrieve workspace details.

### 2. Integrations
- `GET /api/v1/integrations` — List connected integration accounts and their sync statuses.
- `POST /api/v1/integrations/{provider}/connect` — Start OAuth flow or connect credentials for provider (`github`, `gmail`, `slack`).
- `POST /api/v1/integrations/{provider}/sync` — Trigger immediate synchronization for provider.
- `POST /api/v1/integrations/{provider}/seed` — Seed realistic test data for acceptance scenarios.

### 3. Agent Execution & Chat
- `POST /api/v1/agent/runs` — Dispatch user command to the LangGraph Supervisor Agent.
- `GET /api/v1/agent/runs/{id}` — Retrieve run status, plan, step trace, and generated output.
- `GET /api/v1/agent/runs/{id}/stream` — Server-Sent Events (SSE) stream of real-time agent execution events.

### 4. Signals & Intelligence
- `GET /api/v1/signals` — Fetch detected operational signals, anomalies, and cross-system patterns.
- `POST /api/v1/signals/detect` — Trigger manual signal detection scan.

### 5. Investigations
- `GET /api/v1/investigations` — List active and archived investigations.
- `POST /api/v1/investigations` — Initiate a cross-system investigation for a topic or signal.
- `GET /api/v1/investigations/{id}` — Get comprehensive investigation details (timeline, evidence items, hypotheses, action plans).

### 6. Action & Approval Lifecycle
- `GET /api/v1/action-plans/{id}` — Fetch action plan with associated discrete actions.
- `GET /api/v1/actions/pending` — Fetch all actions awaiting human review across the workspace.
- `POST /api/v1/actions/{id}/approve` — Approve an action for execution.
- `POST /api/v1/actions/{id}/reject` — Reject a proposed action with reason.
- `POST /api/v1/actions/{id}/execute` — Trigger execution of an approved action and invoke Verifier.

### 7. Audit & Observability
- `GET /api/v1/audit` — Query immutable workspace audit trail with filtering by actor, action type, and date range.
- `GET /api/v1/health` — System health check, DB connection, and provider latency diagnostics.
