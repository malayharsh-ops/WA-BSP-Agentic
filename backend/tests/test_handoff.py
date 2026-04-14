"""
Tests for the handoff queue API.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


@pytest.mark.asyncio
async def test_list_queue_empty(client):
    with patch("app.api.handoff.get_db") as mock_db:
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await client.get("/handoff/queue")

    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_accept_handoff(client):
    from unittest.mock import MagicMock

    mock_handoff = MagicMock()
    mock_handoff.id = "hid-1"
    mock_handoff.accepted_at = None
    mock_handoff.conversation_id = "conv-1"
    mock_handoff.conversation.lead = MagicMock()

    with patch("app.api.handoff.get_db") as mock_db, \
         patch("app.api.handoff._get_handoff", AsyncMock(return_value=mock_handoff)):
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await client.post("/handoff/hid-1/accept", json={"agent_id": "agent-001"})

    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"


@pytest.mark.asyncio
async def test_cannot_accept_already_accepted(client):
    from unittest.mock import MagicMock

    mock_handoff = MagicMock()
    mock_handoff.accepted_at = datetime.utcnow()

    with patch("app.api.handoff._get_handoff", AsyncMock(return_value=mock_handoff)), \
         patch("app.api.handoff.get_db") as mock_db:
        mock_session = AsyncMock()
        mock_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await client.post("/handoff/hid-1/accept", json={"agent_id": "agent-001"})

    assert resp.status_code == 400
