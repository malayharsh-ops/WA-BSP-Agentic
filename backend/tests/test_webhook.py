"""
Tests for the Meta WhatsApp webhook endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_verify_webhook_success(client):
    resp = await client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "jsw_verify",
            "hub.challenge": "abc123",
        },
    )
    assert resp.status_code == 200
    assert resp.text == "abc123"


@pytest.mark.asyncio
async def test_verify_webhook_wrong_token(client):
    resp = await client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "abc123",
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_receive_message_status_update(client):
    """Status updates (delivered/read) should return 200 without processing."""
    payload = {
        "entry": [{"changes": [{"value": {"statuses": [{"id": "wamid.1", "status": "delivered"}]}}]}]
    }
    with patch("app.config.settings.meta_app_secret", ""):
        resp = await client.post("/webhook", json=payload)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_receive_text_message(client):
    """Inbound text message triggers bot response."""
    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "919999999999",
                        "id": "wamid.test1",
                        "type": "text",
                        "text": {"body": "Hello, I need TMT bars"},
                    }]
                }
            }]
        }]
    }
    mock_reply = ("Namaste! Main Priya hun JSW ONE MSME se. Aapka project kahan hai?", False)

    with (
        patch("app.config.settings.meta_app_secret", ""),
        patch("app.api.webhook.session_store.get", AsyncMock(return_value={
            "phone": "919999999999", "stage": "QUALIFYING", "messages": [],
            "collected": {}, "loop_hashes": [], "loop_stage_turns": 0,
            "loop_last_stage": None, "score": 0, "language": "en", "loop_escalated": False,
        })),
        patch("app.api.webhook.session_store.save", AsyncMock()),
        patch("app.api.webhook.run_priya", AsyncMock(return_value=mock_reply)),
        patch("app.api.webhook.wa_client.mark_read", AsyncMock()),
        patch("app.api.webhook.wa_client.send_text", AsyncMock()),
        patch("app.api.webhook.get_db") as mock_db,
    ):
        # Use a mock DB that doesn't hit Postgres
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=AsyncMock(scalar_one_or_none=MagicMock(return_value=None)))
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.add = MagicMock()
        mock_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await client.post("/webhook", json=payload)

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
