from typing import Optional, Dict, Any

def requires_human_approval(risk_level: str, action_type: str) -> bool:
    """
    Non-negotiable security invariant:
    ALL write actions (MEDIUM, HIGH, CRITICAL) require explicit human approval.
    Read actions (LOW) or draft generation are non-executing proposals or queries.
    """
    if risk_level in ["medium", "high", "critical"]:
        return True
    
    # Specific write types always require human gate
    write_prefixes = ["create_", "send_", "post_", "update_", "delete_", "merge_", "close_"]
    if any(action_type.startswith(prefix) or f"_{prefix}" in action_type for prefix in write_prefixes):
        if action_type == "gmail_create_draft":
            return False  # Creating a local draft in Gmail is safe & non-dispatching
        return True

    return False

def validate_action_execution_allowed(action_status: str, has_approval: bool) -> tuple[bool, Optional[str]]:
    """
    Validates whether an action has satisfied human approval invariants before execution.
    """
    if not has_approval and action_status != "approved":
        return False, "E_POLICY_VIOLATION: Execution blocked. Action has not received explicit human sign-off."
    return True, None
