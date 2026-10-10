# Debate Arena

Two LLM agents, each with a distinct persona, debate a motion in real time.
A third agent judges every round on logic, evidence, and rebuttal quality.
Built to explore multi-agent orchestration, streaming UI, and prompt
engineering for genuinely distinct agent behavior (not just relabeled
chatbots).

## Architecture

```
frontend (React + Vite)  <--SSE-->  backend (FastAPI)
                                        |
                                        v
                                 orchestrator.py
                                (async generator loop)
                                   /          \
                              Debater A    Debater B  --> Judge
                              (Anthropic API calls)
```

- **Backend** (`/backend`): FastAPI app. `app/orchestrator.py` is the core —
  an async generator that runs the debate turn-by-turn and yields structured
  events (`turn`, `score`, `done`) as they happen. `app/main.py` streams
  those events to the frontend over Server-Sent Events, so the UI updates
  live instead of waiting for the whole debate to finish.
- **Frontend** (`/frontend`): React app. Connects via `EventSource`,
  renders each side's turns in facing columns, and shows a live judge
  scorecard + "tug-of-war" bar between rounds.

## Setup

### Backend
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your real ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000
```

Sanity check the orchestration loop headlessly before touching the UI:
```bash
python test_debate.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Open the printed localhost URL. The Vite dev server proxies `/api/*` to
the backend on port 8000 (see `vite.config.js`).

## What's actually hard about this project (for interviews)

1. **Persona bleed** — left unconstrained, agents converge into agreeable,
   samey text after a couple of rounds. Solved with concrete behavioral
   rules per persona (sentence length, forbidden hedges, what to always
   reference) rather than a vague "act like X" prompt — see
   `app/personas.py`.
2. **Streaming multi-agent state** — the orchestrator must maintain a
   shared transcript both debaters can see, feed the judge only the
   relevant round slice, and stream all of it incrementally without
   buffering — see the async generator in `app/orchestrator.py`.
3. **Structured judge output under streaming** — forcing valid JSON from
   the judge and defensively parsing it (models occasionally wrap JSON in
   markdown fences) so a malformed response never crashes the stream — see
   `Judge.score_round` in `app/agents.py`.

## Roadmap (resume-grade additions, not yet built)

- Persist debates to Postgres + shareable replay URLs
- Live human interjection mid-debate
- Multi-model mode (run Debater A and B on different underlying models)
- Audience voting compared against the judge's verdict
