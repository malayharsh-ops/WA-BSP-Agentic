"""
Meta WhatsApp Cloud API client.

Docs: https://developers.facebook.com/docs/whatsapp/cloud-api
"""

import httpx
from app.config import settings

WA_BASE = "https://graph.facebook.com/v19.0"


class WhatsAppClient:
    def __init__(self):
        self._phone_id = settings.meta_phone_number_id
        self._token = settings.meta_whatsapp_token
        self._headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def send_text(self, to: str, body: str) -> dict:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body, "preview_url": False},
        }
        return await self._post(payload)

    async def send_template(
        self,
        to: str,
        template_name: str,
        language_code: str = "en",
        components: list | None = None,
    ) -> dict:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components or [],
            },
        }
        return await self._post(payload)

    async def mark_read(self, message_id: str) -> dict:
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        return await self._post(payload)

    async def _post(self, payload: dict) -> dict:
        url = f"{WA_BASE}/{self._phone_id}/messages"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers=self._headers)
            resp.raise_for_status()
            return resp.json()


# Module-level singleton
wa_client = WhatsAppClient()
