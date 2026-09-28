# StartupOps AI — Operational Runbooks

## Runbook 1: Cross-System Incident Triaging
1. **Trigger**: Anomaly detection alert in `#alerts-ops` or support ticket surge in Gmail.
2. **Autonomous Scan**: Signal Agent calculates baseline z-score on HTTP 500 error rates and customer complaint frequency.
3. **Investigation Generation**:
   - Trace backwards from the incident timestamp to identify recently merged PRs and production releases.
   - Synthesize evidence graph connecting Git author -> commit diff -> Slack alerts -> customer email impact.
   - Calculate confidence scores for candidate hypotheses.
4. **Action Proposal**: Propose a structured Action Plan containing:
   - Hotfix tracking issue on GitHub.
   - Incident broadcast on Slack `#incident-room`.
   - Customer reassurance draft on Gmail.
5. **Human Approval**: Team leads review parameter diffs in the Approval Center and approve actions individually or in batch.
6. **Execution & Verification**: Action Engine executes approved actions via integration adapters with idempotency protection and executes live API verification.

---

## Runbook 2: Token Rotation & Credential Re-encryption
1. Generate new AES-256-GCM master key.
2. Run database migration script to re-encrypt credentials table.
3. Verify all active integration connection tests pass via `/api/v1/integrations/{provider}/test`.
