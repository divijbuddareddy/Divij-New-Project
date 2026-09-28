# StartupOps AI — System Architecture & Design

## Overview
StartupOps AI is a multi-agent AI operating layer for tech startups. It correlates cross-functional signals from GitHub, Slack, Gmail, and incident trackers to provide situational awareness, automated investigations, and human-supervised operational actions.

```
+-------------------------------------------------------------------------+
|                              Next.js Frontend                           |
| (Command Center, Investigations, Signals, Approvals, Audit, Settings)  |
+-----------------------------------+-------------------------------------+
                                    | REST / Server-Sent Events / WebSockets
+-----------------------------------v-------------------------------------+
|                         FastAPI Core API Gateway                        |
|  - Tenant Isolation Middleware  - Auth & JWT Validator                  |
|  - Permission & Policy Engine   - Rate Limiter & Security Shields       |
+-----------------+-----------------+-------------------+-----------------+
                  |                 |                   |
+-----------------v----+   +--------v----------+   +----v-----------------+
|  LangGraph Agent Hub |   | Normalized Stream |   |  Storage & Workers   |
| - Supervisor Agent   |   | - GitHub Sync     |   | - PostgreSQL / SQLite|
| - Planner Agent      |   | - Gmail Sync      |   | - pgvector Search    |
| - Investigation Agent|   | - Slack Sync      |   | - Redis Job Queue    |
| - Action Agent       |   | - Evidence Parser |   | - Encrypted Vault    |
| - Verifier Agent     |   | - Anomaly Scorer  |   | - Audit Log Store    |
+----------------------+   +-------------------+   +----------------------+
```

## Agent Collaboration Model
1. **Supervisor Agent**: Parses incoming user commands, identifies intents (query, investigation, action execution), verifies authorization, and orchestrates specialized agents.
2. **Planner Agent**: Generates structured, deterministic multi-step plans with explicit input schemas and expected outputs.
3. **GitHub / Gmail / Slack Agents**: Domain-specific agents equipped with strictly typed read tools and gated write actions.
4. **Investigation Agent**: Traverses the cross-system evidence graph, correlates disparate events (e.g. PR merge -> Slack alerts -> Customer emails), forms hypotheses, and calculates confidence scores.
5. **Signal Agent**: Continuous anomaly detection combining rolling statistical baselines (z-score on event frequencies) with semantic clustering.
6. **Action & Verifier Agents**: Proposes structured action payloads with risk categorization, registers pending approvals, executes approved transactions with idempotency keys, and verifies live outcomes post-execution.

## Data Isolation & Security
- **Multi-Tenancy**: Every entity has a mandatory `workspace_id`. All queries are scoped to the active workspace.
- **Token Security**: Tokens are AES-256-GCM encrypted with tenant-specific salting.
- **Untrusted Input Protection**: External data from emails, commits, and messages are escaped and isolated with XML boundary tags to defend against prompt injection.
