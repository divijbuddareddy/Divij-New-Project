# StartupOps AI — Security Policy & Controls

## 1. Threat Model & Principles
StartupOps AI processes high-privilege credentials and sensitive operational communications (email, code repos, Slack channels). It follows these non-negotiable security rules:

1. **Zero Unapproved Writes**: No external write (posting message, creating issue, sending email, modifying repo) may be executed autonomously by LLM output. All writes must pass through the `Action & Approval Engine`.
2. **Untrusted Data Boundary**: All raw strings originating from external systems (GitHub issue body, email subject/body, Slack message) are tagged as `<untrusted_external_content>` and sanitized before being presented to LLMs to prevent Indirect Prompt Injection.
3. **Tenant & Workspace Isolation**: Every API endpoint validates tenant identity. No user can access or query resources from a workspace they are not an active member of.
4. **Token Encryption at Rest**: Provider OAuth tokens and secrets are encrypted with AES-256-GCM before database persistence.
5. **SSRF & Egress Protection**: Web tool execution and outbound calls validate target hostnames against an allowlist and reject loopback/RFC-1918 private IP addresses.
6. **Immutable Audit Logging**: All sensitive actions (authentication, token refresh, tool invocation, human approval, action execution, policy violation) produce tamper-evident audit logs.

## 2. Risk Classification Matrix

| Risk Level | Definition | Examples | Approval Requirement |
|---|---|---|---|
| **LOW** | Read-only queries, draft generation without dispatch | Fetch PRs, Read email threads, Draft Slack preview | No explicit approval required (informational) |
| **MEDIUM** | Internal notifications, non-destructive issues | Post to internal Slack channel, Create GitHub tracking issue | Single workspace member approval |
| **HIGH** | Outbound external communication, status updates | Send external email to customer, Merge PR, Close incident | Admin / Lead explicit approval with parameter diff |
| **CRITICAL** | Production data mutation, token rotation, secret changes | Revoke tokens, destructive repository updates | Workspace Admin dual-factor confirmation |
