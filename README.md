# Debate Arena

Two LLM agents, each with a distinct persona, debate a motion in real time. A third agent judges every round on logic, evidence, and rebuttal quality.

Built to explore multi-agent orchestration, streaming UI, and prompt engineering for genuinely distinct agent behavior (not just relabeled chatbots).

---

## Architecture

```
frontend (React + Vite)  <--SSE-->  backend (FastAPI)
                                        |
                                        v
                                 orchestrator.py
                                (async generator loop)
                                   /          \
                              Debater A    Debater B  --> Judge
                              (Google Gemini API calls via google-genai)
```

- **Backend** (`/backend`): FastAPI app powered by the `google-genai` SDK. `app/orchestrator.py` is the core engine — an async generator that runs the debate turn-by-turn and yields structured events (`turn`, `score`, `done`) as they happen. `app/main.py` streams those events to the frontend over Server-Sent Events (SSE), so the UI updates live without waiting for the full debate to complete.
- **Frontend** (`/frontend`): React + Vite single-page application. Connects via native `EventSource`, renders each side's turns in facing duel columns with typing indicators, and renders a live round scorecard + dynamic "tug-of-war" momentum bar between rounds.

---

## Features

- **Live Streaming Debate**: Turn-by-turn generation streamed incrementally via Server-Sent Events (SSE).
- **5 Distinct Personas**: Hand-crafted behavioral rules and constraints that prevent agents from converging into bland agreement ("persona bleed").
- **Automated Round-by-Round Adjudication**: Independent Judge agent evaluates Logic, Evidence, and Rebuttal (1–10 each) with narrative critiques.
- **Dynamic Tug-of-War Momentum**: Visual score representation tracking the momentum between the affirmative and negative sides.
- **Configurable Models**: Independent model configuration for Debater A, Debater B, and the Judge via environment variables.

---

## Available Personas

| ID | Name | Core Worldview | Behavioral Signature |
| :--- | :--- | :--- | :--- |
| `utilitarian` | **The Utilitarian** | Aggregate net consequences & utility | Quantifiable metrics, estimated timeframes, rejects intuitive rights |
| `contrarian` | **The Contrarian Skeptic** | Distrust of consensus views | Attacks hidden assumptions, directly rejects concession, sharp tone |
| `literalist` | **The Literal Engineer** | Systems thinking & term precision | Demands concrete definitions, probes edge cases & failure modes |
| `romantic` | **The Romantic Idealist** | Human sanctity, values, & lived experience | Vivid imagery, protects non-quantifiable human values from spreadsheets |
| `historian` | **The Historian** | Precedent, historical cycles, & patterns | Analogous historical precedents, pattern warnings, seasoned perspective |

---

## Setup & Quickstart

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- A Google Gemini API key

---

### Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   - **macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt)**:
     ```cmd
     python -m venv venv
     .\venv\Scripts\activate.bat
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and insert your Gemini API key:
   ```env
   GOOGLE_API_KEY=your-google-api-key-here
   DEBATER_A_MODEL=gemini-3.8-flash
   DEBATER_B_MODEL=gemini-3.8-flash
   JUDGE_MODEL=gemini-3.8-flash
   ```

5. **Run headless test (optional)**:
   Validate the orchestration loop directly in your terminal before launching the server:
   ```bash
   python test_debate.py
   ```

6. **Start the API server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   The backend API will be available at `http://localhost:8000`.

---

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

4. Open the printed localhost URL (default: `http://localhost:5173`). Vite automatically proxies `/api/*` requests to the FastAPI backend on `http://localhost:8000` (see `vite.config.js`).

---

## API Endpoints & SSE Streaming

- **`GET /api/personas`**: Returns the list of available personas with their `id`, `name`, and `tagline`.
- **`GET /api/health`**: Health check returning `{"status": "ok"}`.
- **`GET /api/debate/stream`**: Server-Sent Events (SSE) streaming endpoint.
  - **Query Parameters**:
    - `topic` (string, required): Motion to debate (e.g. *"Cities should ban private cars from downtown cores"*).
    - `persona_a` (string, default: `utilitarian`): Persona ID for the Affirmative side.
    - `persona_b` (string, default: `romantic`): Persona ID for the Negative side.
    - `rounds` (int, default: `3`): Number of debate rounds (1–5).
  - **Streamed Events**:
    - `turn`: Emitted when Debater A or Debater B completes a speech. Payload includes speaker, persona name, round, and text.
    - `score`: Emitted when the Judge scores the round on `logic`, `evidence`, and `rebuttal` with a round winner.
    - `done`: Emitted upon debate completion with `final_tally`, `round_wins`, and `overall_winner`.

---

## Project Structure

```
Debate arena/
├── README.md                   # Project documentation
├── backend/
│   ├── .env                    # Local environment variables (GOOGLE_API_KEY, models)
│   ├── .env.example            # Environment template
│   ├── requirements.txt        # Python dependencies (FastAPI, google-genai, sse-starlette)
│   ├── test_debate.py          # Standalone headless CLI test script
│   └── app/
│       ├── __init__.py
│       ├── main.py             # FastAPI application and SSE route
│       ├── orchestrator.py     # Core asynchronous debate loop & event generator
│       ├── agents.py           # Debater and Judge classes wrapping google-genai
│       └── personas.py         # Persona definitions & Judge scoring prompt
└── frontend/
    ├── package.json            # Frontend dependencies (React, Vite)
    ├── vite.config.js          # Vite config with backend proxy
    ├── index.html              # HTML template
    └── src/
        ├── main.jsx            # React root entry point
        ├── App.jsx             # Debate arena dashboard, state, and SSE stream consumer
        └── index.css           # Styling for duel view, judge cards, and tug-of-war
```

---

## What's Actually Hard About This Project (Interview Discussion Points)

1. **Persona Bleed Mitigation**: Left unconstrained, conversational LLMs rapidly converge into agreeable, homogenizing language within 2 rounds. This is solved with explicit syntactic and behavioral rules per persona (e.g., sentence count limits, mandatory quantitative framing or historical references, and explicit prohibitions against conversational hedging) in `app/personas.py`.
2. **Streaming Multi-Agent State Synchronization**: The orchestrator maintains a cumulative transcript for debaters to contextualize opposing arguments, feeds only round-specific slices to the judge, and yields incremental events over an async generator without buffering in memory (`app/orchestrator.py`).
3. **Structured Judge Output under Streaming**: Enforcing reliable JSON output from the judge agent and defensively stripping Markdown backticks or unexpected formatting so malformed responses never terminate the live SSE stream (`app/agents.py`).

---

## Roadmap

- Persist debates to PostgreSQL + shareable replay URLs
- Live human interjection mid-debate (allow audience questions or rebuttal challenges)
- Dynamic UI model selector (Debater A vs Debater B on different model families)
- Audience live voting compared against the AI judge's verdict
