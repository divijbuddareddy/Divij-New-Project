import pytest
from app.policies.risk_policy import calculate_action_risk, RISK_LEVEL_MEDIUM, RISK_LEVEL_HIGH, RISK_LEVEL_LOW
from app.policies.approval_policy import requires_human_approval, validate_action_execution_allowed

def test_risk_calculation():
    # GitHub create issue
    risk, _ = calculate_action_risk("github", "github_create_issue", {"repo": "acme/web-app", "title": "Bug"})
    assert risk == RISK_LEVEL_MEDIUM

    # Gmail send email
    risk, _ = calculate_action_risk("gmail", "gmail_send_email", {"to": "customer@acme.com", "body": "Fixed"})
    assert risk == RISK_LEVEL_HIGH

    # GitHub read PRs
    risk, _ = calculate_action_risk("github", "github_read_prs", {"repo": "acme/web-app"})
    assert risk == RISK_LEVEL_LOW

def test_approval_policy():
    # Medium and High risk actions require approval
    assert requires_human_approval("medium", "github_create_issue") is True
    assert requires_human_approval("high", "gmail_send_email") is True
    assert requires_human_approval("low", "github_read_prs") is False

    # Execution without approval is blocked
    allowed, err = validate_action_execution_allowed("awaiting_approval", has_approval=False)
    assert allowed is False
    assert "E_POLICY_VIOLATION" in err

    # Approved action is allowed
    allowed, err = validate_action_execution_allowed("approved", has_approval=True)
    assert allowed is True
    assert err is None
