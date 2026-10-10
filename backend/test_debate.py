"""
Headless smoke test — run the debate loop in the terminal, no server, no UI.
This is the fastest way to validate the orchestration logic and tune the
personas before wiring up streaming/frontend.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python test_debate.py
"""

import asyncio

from app.orchestrator import run_debate


async def main():
    topic = "Cities should ban private cars from downtown cores"

    print(f"\n=== DEBATE: {topic} ===\n")

    async for event in run_debate(
        topic=topic,
        persona_a_id="utilitarian",
        persona_b_id="romantic",
        rounds=2,
    ):
        if event["type"] == "turn":
            print(f"--- Round {event['round']} | {event['persona']} ({event['speaker']}) ---")
            print(event["text"])
            print()
        elif event["type"] == "score":
            print(f"[Judge — Round {event['round']}]")
            print(event["result"])
            print()
        elif event["type"] == "done":
            print("=== FINAL RESULT ===")
            print("Tally:", event["final_tally"])
            print("Round wins:", event["round_wins"])
            print("Overall winner:", event["overall_winner"])


if __name__ == "__main__":
    asyncio.run(main())
