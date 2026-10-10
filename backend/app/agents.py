"""
Thin wrappers around the Google Gemini API for the two agent roles:
Debater and Judge. Kept deliberately simple — orchestration logic lives
in orchestrator.py, not here.
"""

import json
import os

from google import genai
from google.genai import types

from .personas import PERSONAS, JUDGE_SYSTEM_PROMPT


def _get_client() -> genai.Client:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set in the environment.")
    return genai.Client(api_key=api_key)


class Debater:
    def __init__(self, debater_id: str, persona_id: str, stance: str, model: str):
        self.id = debater_id
        self.persona = PERSONAS[persona_id]
        self.stance = stance  # e.g. "FOR the motion" / "AGAINST the motion"
        self.model = model

    def system_prompt(self, topic: str) -> str:
        return (
            f"{self.persona.system_prompt}\n\n"
            f"DEBATE TOPIC: {topic}\n"
            f"YOUR ASSIGNED STANCE: You are arguing {self.stance}.\n\n"
            "CRITICAL: Always respond to the specific claim your opponent "
            "just made in their most recent turn. Quote or paraphrase their "
            "exact point before countering it. Do not just restate your own "
            "previous argument in new words. Never break character or "
            "mention that you are an AI."
        )

    async def take_turn(self, topic: str, transcript: list[dict], round_num: int) -> str:
        """
        transcript: list of {"speaker": debater_id, "text": str} for prior turns.
        Returns the debater's new turn as plain text.
        """
        client = _get_client()

        if not transcript:
            user_msg = (
                f"This is round {round_num}. Open the debate with your "
                f"opening argument for your stance."
            )
        else:
            history = "\n\n".join(
                f"[{turn['speaker']}]: {turn['text']}" for turn in transcript
            )
            user_msg = (
                f"This is round {round_num}. Here is the debate so far:\n\n"
                f"{history}\n\n"
                "Respond now: directly engage the opponent's most recent "
                "point, then advance your own case."
            )

        response = await client.aio.models.generate_content(
            model=self.model,
            contents=user_msg,
            config=types.GenerateContentConfig(
                system_instruction=self.system_prompt(topic),
                max_output_tokens=400,
            ),
        )
        return response.text.strip()


class Judge:
    def __init__(self, model: str):
        self.model = model

    async def score_round(
        self, topic: str, debater_a_id: str, debater_b_id: str, round_transcript: list[dict]
    ) -> dict:
        client = _get_client()

        transcript_text = "\n\n".join(
            f"[{turn['speaker']}]: {turn['text']}" for turn in round_transcript
        )
        user_msg = (
            f"Debate topic: {topic}\n"
            f"Debater A id: {debater_a_id}\n"
            f"Debater B id: {debater_b_id}\n\n"
            f"This round's turns:\n\n{transcript_text}\n\n"
            "Score this round now, following the exact JSON schema."
        )

        response = await client.aio.models.generate_content(
            model=self.model,
            contents=user_msg,
            config=types.GenerateContentConfig(
                system_instruction=JUDGE_SYSTEM_PROMPT,
                max_output_tokens=500,
            ),
        )
        raw = response.text.strip()
        # Defensive parse: strip accidental markdown fences if the model adds them
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "scores": {
                    debater_a_id: {"logic": 0, "evidence": 0, "rebuttal": 0, "note": "judge parse error"},
                    debater_b_id: {"logic": 0, "evidence": 0, "rebuttal": 0, "note": "judge parse error"},
                },
                "round_winner": None,
                "parse_error": raw,
            }
