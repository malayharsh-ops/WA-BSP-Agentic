"""
Tests for campaign creation and send trigger.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


@pytest.mark.asyncio
async def test_list_campaigns_empty(client):
    with patch("app.api.campaigns.get_db") as mock_db:
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await client.get("/campaigns")

    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_campaign(client):
    mock_campaign = MagicMock()
    mock_campaign.id = "camp-1"
    mock_campaign.name = "April TMT"
    mock_campaign.template_name = "jsw_tmt_v1"
    mock_campaign.language = "hi"
    mock_campaign.status = "DRAFT"
    mock_campaign.scheduled_at = None
    mock_campaign.started_at = None
    mock_campaign.completed_at = None
    mock_campaign.created_at = datetime.utcnow()

    with patch("app.api.campaigns.get_db") as mock_db:
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock(side_effect=lambda obj: None)
        mock_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("app.api.campaigns.Campaign", return_value=mock_campaign):
            resp = await client.post(
                "/campaigns",
                json={"name": "April TMT", "template_name": "jsw_tmt_v1", "language": "hi"},
            )

    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_send_campaign_enqueues_task(client):
    mock_campaign = MagicMock()
    mock_campaign.id = "camp-1"
    mock_campaign.status = "DRAFT"

    with patch("app.api.campaigns.get_db") as mock_db, \
         patch("app.api.campaigns._get_campaign", AsyncMock(return_value=mock_campaign)), \
         patch("app.workers.campaign_tasks.send_campaign_task") as mock_task:
        mock_task.delay = MagicMock()
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await client.post("/campaigns/camp-1/send")

    assert resp.status_code == 200
    assert resp.json()["status"] == "queued"


@pytest.mark.asyncio
async def test_loop_guard_escalates_on_repeat():
    from app.agent.loop_guard import LoopGuard

    session = {
        "loop_hashes": [],
        "loop_stage_turns": 0,
        "loop_last_stage": None,
        "stage": "QUALIFYING",
    }
    guard = LoopGuard(session)

    # Same message 3 times should trigger escalation
    assert guard.check("price kya hai") is False
    assert guard.check("price kya hai") is False
    assert guard.check("price kya hai") is True
