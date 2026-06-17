"""Meta WhatsApp Cloud API provider.

Docs: https://developers.facebook.com/docs/whatsapp/cloud-api

Sends to individual phone numbers (Meta's official API cannot post to groups).
Credentials come from env vars, never the DB:

    WHATSAPP_API_TOKEN        permanent system-user access token
    WHATSAPP_PHONE_NUMBER_ID  the sender phone-number id
    WHATSAPP_API_VERSION      graph API version (default v21.0)
"""

import os

import requests

from app.services.whatsapp.base import WhatsAppProvider, SendResult, WhatsAppError

GRAPH_BASE = "https://graph.facebook.com"
# Transient HTTP statuses worth retrying.
_RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}


class MetaCloudProvider(WhatsAppProvider):
    name = "meta"

    def __init__(
        self,
        token: str | None = None,
        phone_number_id: str | None = None,
        api_version: str | None = None,
        timeout: int = 30,
    ):
        self.token = token or os.getenv("WHATSAPP_API_TOKEN")
        self.phone_number_id = phone_number_id or os.getenv(
            "WHATSAPP_PHONE_NUMBER_ID"
        )
        self.api_version = api_version or os.getenv("WHATSAPP_API_VERSION", "v21.0")
        self.timeout = timeout

        if not self.token or not self.phone_number_id:
            raise WhatsAppError(
                "Meta provider not configured: set WHATSAPP_API_TOKEN and "
                "WHATSAPP_PHONE_NUMBER_ID.",
                retryable=False,
            )

    # ─── internals ──────────────────────────────────────────────────────────

    @property
    def _url(self) -> str:
        return f"{GRAPH_BASE}/{self.api_version}/{self.phone_number_id}/messages"

    def _post(self, payload: dict) -> SendResult:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        try:
            resp = requests.post(
                self._url, json=payload, headers=headers, timeout=self.timeout
            )
        except requests.RequestException as exc:
            # Network-level failure — always worth a retry.
            raise WhatsAppError(f"network error: {exc}", retryable=True) from exc

        if resp.status_code == 200:
            body = resp.json()
            msg_id = (body.get("messages") or [{}])[0].get("id")
            return SendResult(success=True, provider_msg_id=msg_id)

        # Error: surface Meta's message and classify retryability.
        try:
            err = resp.json().get("error", {})
            detail = err.get("message", resp.text)
        except ValueError:
            detail = resp.text
        retryable = resp.status_code in _RETRYABLE_STATUS
        raise WhatsAppError(
            f"Meta API {resp.status_code}: {detail}", retryable=retryable
        )

    # ─── public ─────────────────────────────────────────────────────────────

    def send_text(self, to: str, message: str) -> SendResult:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": message},
        }
        return self._post(payload)

    def send_template(
        self, to: str, template_name: str, lang: str, params: list[str]
    ) -> SendResult:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": lang},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": p} for p in params
                        ],
                    }
                ],
            },
        }
        return self._post(payload)
