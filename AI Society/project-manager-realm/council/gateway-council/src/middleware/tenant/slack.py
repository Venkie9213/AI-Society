import json
import urllib.parse
import httpx
from typing import Optional
from fastapi import Request
from src.middleware.tenant.base import TenantExtractor
from src.config.settings import settings

class SlackTenantExtractor(TenantExtractor):
    async def extract(self, request: Request) -> Optional[str]:
        if not request.url.path.startswith("/webhooks/slack"):
            return None

        body_bytes = getattr(request.state, "body", await request.body())
        if not body_bytes:
            return None

        team_id = self._extract_slack_team_id(body_bytes, request.headers.get("Content-Type", ""))
        if not team_id:
            return None

        return await self._map_team_to_tenant(team_id)

    async def _map_team_to_tenant(self, team_id: str) -> str:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.workspace_council_url}/api/v1/tenants/{team_id}"
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("id")
        except Exception:
            pass
        return f"tenant_{team_id}"

    def _extract_slack_team_id(self, body: bytes, content_type: str) -> Optional[str]:
        try:
            if "application/x-www-form-urlencoded" in content_type:
                payload = urllib.parse.parse_qs(body.decode("utf-8"))
                if "payload" in payload:
                    interactive_data = json.loads(payload["payload"][0])
                    return interactive_data.get("team", {}).get("id")
                return payload.get("team_id", [None])[0]
            else:
                data = json.loads(body.decode("utf-8"))
                return data.get("team_id") or data.get("team", {}).get("id")
        except Exception:
            return None
