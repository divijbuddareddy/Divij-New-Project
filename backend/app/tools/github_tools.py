from pydantic import BaseModel, Field
from typing import List, Optional
from app.tools.registry import registry

class GitHubSearchPRsInput(BaseModel):
    repo: str = Field(description="The repository name, e.g. acme-corp/web-app")
    state: Optional[str] = Field(default="all", description="State: open, closed, all")
    limit: Optional[int] = Field(default=10, description="Max PRs to retrieve")

class GitHubCreateIssueInput(BaseModel):
    repo: str = Field(description="The target repository")
    title: str = Field(description="Title of the issue")
    body: str = Field(description="Markdown body describing incident/root cause")
    labels: Optional[List[str]] = Field(default=["bug", "ops"], description="Labels to attach")

@registry.register(
    name="github_search_prs",
    description="Search pull requests, commits and review status in a repository.",
    provider="github",
    is_write=False,
    risk_level="low",
    schema=GitHubSearchPRsInput
)
async def github_search_prs(repo: str, state: str = "all", limit: int = 10):
    return {
        "prs": [
            {"number": 138, "title": "Refactor Stripe Webhook and Checkout Payload Validation", "state": "merged", "author": "alex.dev"}
        ]
    }

@registry.register(
    name="github_create_issue",
    description="Create a new issue in a GitHub repository.",
    provider="github",
    is_write=True,
    risk_level="medium",
    schema=GitHubCreateIssueInput
)
async def github_create_issue(repo: str, title: str, body: str, labels: Optional[List[str]] = None):
    # Registered write action
    return {
        "status": "proposed_action",
        "action_type": "github_create_issue",
        "parameters": {"repo": repo, "title": title, "body": body, "labels": labels or ["bug"]}
    }
