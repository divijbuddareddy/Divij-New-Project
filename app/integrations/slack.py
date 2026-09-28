import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.integrations.base import BaseIntegration

class SlackIntegration(BaseIntegration):
    BASE_URL = "https://slack.com/api"

    def _get_headers(self) -> Dict[str, str]:
        token = self.credentials.get("access_token") or self.credentials.get("token", "")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }

    async def test_connection(self) -> Dict[str, Any]:
        token = self.credentials.get("access_token") or self.credentials.get("token", "")
        if not token:
            return {"success": False, "error": "No Slack Bot/User token provided (e.g. xoxb-...)"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.post(f"{self.BASE_URL}/auth.test", headers=self._get_headers())
                if res.status_code == 200:
                    data = res.json()
                    if data.get("ok"):
                        return {
                            "success": True,
                            "provider": "slack",
                            "team_name": data.get("team"),
                            "bot_user_id": data.get("user_id"),
                            "mode": "live_connected"
                        }
                    return {"success": False, "error": data.get("error", "Slack auth failed")}
                return {"success": False, "error": f"Slack API HTTP {res.status_code}"}
            except Exception as e:
                return {"success": False, "error": f"Slack connection failed: {str(e)}"}

    async def sync_evidence(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Fetches public channels and recent messages to extract live operational evidence.
        """
        token = self.credentials.get("access_token") or self.credentials.get("token", "")
        if not token:
            return []

        evidence = []
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                # 1. Fetch channels
                ch_res = await client.get(f"{self.BASE_URL}/conversations.list?types=public_channel,private_channel&limit=10", headers=self._get_headers())
                if ch_res.status_code == 200 and ch_res.json().get("ok"):
                    channels = ch_res.json().get("channels", [])
                    for ch in channels:
                        ch_id = ch.get("id")
                        ch_name = ch.get("name")
                        
                        # 2. Fetch history
                        hist_res = await client.get(f"{self.BASE_URL}/conversations.history?channel={ch_id}&limit=10", headers=self._get_headers())
                        if hist_res.status_code == 200 and hist_res.json().get("ok"):
                            messages = hist_res.json().get("messages", [])
                            for m in messages:
                                text = m.get("text", "")
                                if not text:
                                    continue
                                ts_float = float(m.get("ts", "0"))
                                msg_dt = datetime.fromtimestamp(ts_float) if ts_float > 0 else datetime.utcnow()
                                
                                evidence.append({
                                    "source": "slack",
                                    "actor": m.get("user") or m.get("bot_id") or "slack_user",
                                    "action": "slack_message_posted",
                                    "object_id": f"slack_{ch_id}_{m.get('ts')}",
                                    "title": f"#{ch_name}: {text[:80]}",
                                    "content_summary": text[:500],
                                    "raw_payload": {
                                        "channel": ch_name,
                                        "channel_id": ch_id,
                                        "ts": m.get("ts")
                                    },
                                    "timestamp": msg_dt
                                })
            except Exception as e:
                print(f"Error syncing Slack live messages: {e}")

        return evidence

    async def execute_action(self, action_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Posts real messages to Slack channel.
        """
        token = self.credentials.get("access_token") or self.credentials.get("token")
        if not token:
            raise ValueError("No Slack token configured to execute write action.")

        channel = parameters.get("channel")
        text = parameters.get("text")
        if not channel or not text:
            raise ValueError("Parameters 'channel' and 'text' are required for Slack message.")

        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                f"{self.BASE_URL}/chat.postMessage",
                headers=self._get_headers(),
                json={"channel": channel, "text": text}
            )
            data = res.json()
            if res.status_code == 200 and data.get("ok"):
                return {
                    "success": True,
                    "channel": data.get("channel"),
                    "ts": data.get("ts"),
                    "message": data.get("message"),
                    "posted_at": datetime.utcnow().isoformat()
                }
            else:
                raise RuntimeError(f"Slack post message failed: {data.get('error') or res.text}")

    async def verify_action(self, action_type: str, parameters: Dict[str, Any], execution_result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "verified": True,
            "verification_method": "slack_api_post_confirmation",
            "channel": execution_result.get("channel"),
            "ts": execution_result.get("ts"),
            "verified_at": datetime.utcnow().isoformat()
        }
