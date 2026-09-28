from app.integrations.base import BaseIntegration
from app.integrations.github import GitHubIntegration
from app.integrations.gmail import GmailIntegration
from app.integrations.slack import SlackIntegration
from app.integrations.hubspot import HubSpotCRMIntegration
from app.integrations.crm import UniversalCRMIntegration

def get_integration_adapter(provider: str, workspace_id: str, credentials: dict) -> BaseIntegration:
    p = provider.lower()
    if p == "github":
        return GitHubIntegration(workspace_id, credentials)
    elif p in ["gmail", "google"]:
        return GmailIntegration(workspace_id, credentials)
    elif p == "slack":
        return SlackIntegration(workspace_id, credentials)
    elif p in ["hubspot", "crm", "salesforce", "pipedrive", "zoho", "notion", "custom_crm"]:
        return UniversalCRMIntegration(workspace_id, credentials)
    else:
        # Graceful fallback to Universal CRM / custom integration
        return UniversalCRMIntegration(workspace_id, credentials)

__all__ = ["BaseIntegration", "GitHubIntegration", "GmailIntegration", "SlackIntegration", "HubSpotCRMIntegration", "UniversalCRMIntegration", "get_integration_adapter"]


