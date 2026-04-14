"""
Tests for the lead qualification scoring function.
"""

import pytest
from app.agent.qualification import score_lead, stage_from_score, HANDOFF_THRESHOLD


def test_empty_collected_returns_zero():
    assert score_lead({}) == 0


def test_high_volume_adds_30():
    score = score_lead({"volume_mt": "100 MT"})
    assert score >= 30


def test_medium_volume_adds_15():
    score = score_lead({"volume_mt": "25"})
    assert score == 15


def test_short_timeline_adds_25():
    score = score_lead({"timeline_days": 14})
    assert score >= 25


def test_medium_timeline_adds_10():
    score = score_lead({"timeline_days": 45})
    assert score == 10


def test_decision_maker_adds_20():
    score = score_lead({"is_decision_maker": True})
    assert score == 20


def test_commercial_project_adds_15():
    score = score_lead({"project_type": "commercial"})
    assert score == 15


def test_residential_adds_5():
    score = score_lead({"project_type": "residential"})
    assert score == 5


def test_name_adds_10():
    score = score_lead({"name": "Ramesh"})
    assert score == 10


def test_hot_lead_triggers_handoff_threshold():
    collected = {
        "volume_mt": "100",
        "timeline_days": 7,
        "is_decision_maker": True,
        "project_type": "commercial",
        "name": "Ramesh Kumar",
    }
    score = score_lead(collected)
    assert score >= HANDOFF_THRESHOLD


def test_score_capped_at_100():
    collected = {
        "volume_mt": "200",
        "timeline_days": 3,
        "is_decision_maker": True,
        "project_type": "infrastructure",
        "name": "Ramesh",
    }
    assert score_lead(collected) <= 100


def test_stage_from_score():
    assert stage_from_score(0) == "NEW"
    assert stage_from_score(29) == "NEW"
    assert stage_from_score(30) == "WARM"
    assert stage_from_score(69) == "WARM"
    assert stage_from_score(70) == "HOT"
    assert stage_from_score(100) == "HOT"
