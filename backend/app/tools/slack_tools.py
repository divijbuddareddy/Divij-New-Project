from pydantic import BaseModel, Field
from typing import Optional
from app.tools.registry import registry

class SlackSearchMessagesInput(BaseModel):
    query: str = Field(description="Query to search messages in workspace")

class SlackPostMessageInput(BaseModel):
    channel: str = Field(description="Slack channel e.g. #incident-room")
    text: str = Field(description="Message body to post")

@registry.register(
    name="slack_search_messages",
    description="Search messages across Slack channels.",
    provider="slack",
    is_write=False,
    risk_level="low",
    schema=SlackSearchMessagesInput
)
async def slack_search_messages(query: str):
    return {"query": query, "messages_found": 5}

@registry.register(
    name="slack_post_message",
    description="Post an incident notification or operational message to a Slack channel.",
    provider="slack",
    is_write=True,
    risk_level="medium",
    schema=SlackPostMessageInput
)
async def slack_post_message(channel: str, text: str):
    return {
        "status": "proposed_action",
        "action_type": "slack_post_message",
        "parameters": {"channel": channel, "text": text}
    }
