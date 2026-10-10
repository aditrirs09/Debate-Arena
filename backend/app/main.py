import json

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from .orchestrator import run_debate
from .personas import PERSONAS

app = FastAPI(title="Debate Arena API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before deploying publicly
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/personas")
async def list_personas():
    return [
        {"id": p.id, "name": p.name, "tagline": p.tagline} for p in PERSONAS.values()
    ]


@app.get("/api/debate/stream")
async def stream_debate(
    topic: str,
    persona_a: str = "utilitarian",
    persona_b: str = "romantic",
    rounds: int = 3,
):
    """
    SSE endpoint. Frontend connects with EventSource and receives one
    event per debate turn / score / completion, in order, as they're
    generated — no waiting for the full debate to finish.
    """

    async def event_generator():
        async for event in run_debate(topic, persona_a, persona_b, rounds):
            yield {"event": event["type"], "data": json.dumps(event)}

    return EventSourceResponse(event_generator())


@app.get("/api/health")
async def health():
    return {"status": "ok"}
