"""
Core orchestration loop for a debate.

Designed as an async generator that YIELDS structured events as they
happen, so the API layer (main.py) can stream them straight to the
frontend over SSE without buffering the whole debate first. This is the
piece that matters most for the "live" feel of the demo.

Event shapes (all dicts with a "type" key):
  {"type": "turn", "speaker": id, "round": n, "text": str}
  {"type": "score", "round": n, "result": <judge JSON>}
  {"type": "done", "final_tally": {...}}
"""

import os

from .agents import Debater, Judge
from .personas import PERSONAS


async def run_debate(
    topic: str,
    persona_a_id: str,
    persona_b_id: str,
    rounds: int = 3,
):
    debater_a = Debater(
        debater_id="debater_a",
        persona_id=persona_a_id,
        stance="FOR the motion",
        model=os.getenv("DEBATER_A_MODEL", "gemini-2.0-flash"),
    )
    debater_b = Debater(
        debater_id="debater_b",
        persona_id=persona_b_id,
        stance="AGAINST the motion",
        model=os.getenv("DEBATER_B_MODEL", "gemini-2.0-flash"),
    )
    judge = Judge(model=os.getenv("JUDGE_MODEL", "gemini-2.0-flash"))

    full_transcript: list[dict] = []
    tally = {"debater_a": {"logic": 0, "evidence": 0, "rebuttal": 0}, "debater_b": {"logic": 0, "evidence": 0, "rebuttal": 0}}
    wins = {"debater_a": 0, "debater_b": 0}

    for round_num in range(1, rounds + 1):
        round_transcript = []

        # Debater A speaks
        text_a = await debater_a.take_turn(topic, full_transcript, round_num)
        turn_a = {"speaker": "debater_a", "text": text_a}
        full_transcript.append(turn_a)
        round_transcript.append(turn_a)
        yield {"type": "turn", "speaker": "debater_a", "persona": PERSONAS[persona_a_id].name, "round": round_num, "text": text_a}

        # Debater B responds, now able to see A's latest point
        text_b = await debater_b.take_turn(topic, full_transcript, round_num)
        turn_b = {"speaker": "debater_b", "text": text_b}
        full_transcript.append(turn_b)
        round_transcript.append(turn_b)
        yield {"type": "turn", "speaker": "debater_b", "persona": PERSONAS[persona_b_id].name, "round": round_num, "text": text_b}

        # Judge scores this round
        result = await judge.score_round(topic, "debater_a", "debater_b", round_transcript)
        if "scores" in result:
            for did in ("debater_a", "debater_b"):
                s = result["scores"].get(did, {})
                for axis in ("logic", "evidence", "rebuttal"):
                    tally[did][axis] += s.get(axis, 0)
            winner = result.get("round_winner")
            if winner in wins:
                wins[winner] += 1
        yield {"type": "score", "round": round_num, "result": result}

    yield {
        "type": "done",
        "final_tally": tally,
        "round_wins": wins,
        "overall_winner": max(wins, key=wins.get) if wins["debater_a"] != wins["debater_b"] else "tie",
    }
