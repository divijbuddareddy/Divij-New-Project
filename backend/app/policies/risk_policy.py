from typing import Dict, Any, Tuple

# Risk Levels: LOW, MEDIUM, HIGH, CRITICAL
RISK_LEVEL_LOW = "low"
RISK_LEVEL_MEDIUM = "medium"
RISK_LEVEL_HIGH = "high"
RISK_LEVEL_CRITICAL = "critical"

ACTION_RISK_MAP = {
    # Read/Search tools
    "github_read_repos": RISK_LEVEL_LOW,
    "github_read_prs": RISK_LEVEL_LOW,
    "github_read_issues": RISK_LEVEL_LOW,
    "gmail_search_threads": RISK_LEVEL_LOW,
    "gmail_read_thread": RISK_LEVEL_LOW,
    "slack_search_messages": RISK_LEVEL_LOW,
    "slack_read_channel": RISK_LEVEL_LOW,

    # Internal writes
    "github_create_issue": RISK_LEVEL_MEDIUM,
    "slack_post_message": RISK_LEVEL_MEDIUM,
    "gmail_create_draft": RISK_LEVEL_LOW,

    # External writes / modifications
    "gmail_send_email": RISK_LEVEL_HIGH,
    "github_merge_pr": RISK_LEVEL_HIGH,
    "github_close_issue": RISK_LEVEL_MEDIUM,
    "system_rotate_credentials": RISK_LEVEL_CRITICAL,
    "system_delete_data": RISK_LEVEL_CRITICAL
}

def calculate_action_risk(provider: str, action_type: str, parameters: Dict[str, Any]) -> Tuple[str, str]:
    """
    Determines the risk classification and rationale for a proposed action.
    """
    key = action_type.lower()
    risk = ACTION_RISK_MAP.get(key, RISK_LEVEL_HIGH)

    # Dynamic risk escalation checks
    if action_type == "gmail_send_email":
        recipients = parameters.get("to", [])
        if isinstance(recipients, str):
            recipients = [recipients]
        if len(recipients) > 5:
            return RISK_LEVEL_HIGH, "High risk: Dispatching email to multiple external recipients."
        return RISK_LEVEL_HIGH, "High risk: Outbound communication directly reaching external email recipient."

    if action_type == "github_create_issue":
        return RISK_LEVEL_MEDIUM, "Medium risk: Creates an open tracking issue in a public/internal repository."

    if action_type == "slack_post_message":
        channel = parameters.get("channel", "")
        if "general" in channel.lower() or "announcements" in channel.lower():
            return RISK_LEVEL_MEDIUM, "Medium risk: Broadcasts update to general team channel."
        return RISK_LEVEL_MEDIUM, "Medium risk: Posts an automated operations notice into team channel."

    return risk, f"Standard risk tier evaluated for action type {action_type}."
