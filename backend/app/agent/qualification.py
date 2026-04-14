"""
Lead qualification scoring.
Pure function — no side effects — safe to call after every bot turn.
"""

HANDOFF_THRESHOLD = 70


def score_lead(collected: dict) -> int:
    """
    Score a lead 0–100 based on collected qualification data.

    Args:
        collected: Dict with keys matching Lead model fields.

    Returns:
        Integer score 0–100.
    """
    score = 0

    # Volume ≥ 50 MT or ≥ 500 bags → +30
    volume_raw = collected.get("volume_mt", "")
    if volume_raw:
        try:
            volume = float(str(volume_raw).split()[0].replace(",", ""))
            if volume >= 50:
                score += 30
            elif volume >= 20:
                score += 15
        except (ValueError, IndexError):
            pass

    # Timeline ≤ 30 days → +25
    timeline = collected.get("timeline_days")
    if timeline is not None:
        try:
            days = int(timeline)
            if days <= 30:
                score += 25
            elif days <= 60:
                score += 10
        except (ValueError, TypeError):
            pass

    # Decision maker confirmed → +20
    if collected.get("is_decision_maker") is True:
        score += 20

    # Commercial or infrastructure project → +15
    project_type = (collected.get("project_type") or "").lower()
    if project_type in ("commercial", "infrastructure"):
        score += 15
    elif project_type == "residential":
        score += 5

    # Contact info / name present → +10
    if collected.get("name"):
        score += 10

    return min(score, 100)


def stage_from_score(score: int) -> str:
    if score >= HANDOFF_THRESHOLD:
        return "HOT"
    elif score >= 30:
        return "WARM"
    elif score > 0:
        return "NEW"
    return "NEW"


def extract_collected(session: dict) -> dict:
    """Pull the collected qualification fields from a session dict."""
    return session.get("collected", {})
