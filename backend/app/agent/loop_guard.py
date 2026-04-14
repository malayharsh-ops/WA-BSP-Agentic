"""
Loop prevention for the Priya agent.

Rules:
1. If the same user message hash appears 3+ times in a session → escalate.
2. If the conversation has cycled on the same qualification stage for 5+ turns → escalate.
"""

import hashlib
import re


_MAX_REPEAT_COUNT = 3
_MAX_STAGE_CYCLES = 5


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _hash(text: str) -> str:
    return hashlib.sha256(_normalize(text).encode()).hexdigest()[:16]


class LoopGuard:
    def __init__(self, session: dict):
        self._session = session
        session.setdefault("loop_hashes", [])
        session.setdefault("loop_stage_turns", 0)
        session.setdefault("loop_last_stage", None)

    def check(self, user_message: str) -> bool:
        """
        Returns True if a loop is detected (caller should escalate).
        Mutates session in place with updated counters.
        """
        h = _hash(user_message)
        hashes: list = self._session["loop_hashes"]
        hashes.append(h)

        # Rule 1: exact message repeated ≥ 3 times
        if hashes.count(h) >= _MAX_REPEAT_COUNT:
            return True

        # Rule 2: same stage for too many consecutive turns
        current_stage = self._session.get("stage", "QUALIFYING")
        last_stage = self._session["loop_last_stage"]
        if current_stage == last_stage:
            self._session["loop_stage_turns"] += 1
        else:
            self._session["loop_stage_turns"] = 1
            self._session["loop_last_stage"] = current_stage

        if self._session["loop_stage_turns"] >= _MAX_STAGE_CYCLES:
            return True

        return False
