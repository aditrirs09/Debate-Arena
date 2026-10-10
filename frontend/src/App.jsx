import { useEffect, useRef, useState } from "react";

const SIDE_LABELS = { debater_a: "For", debater_b: "Against" };

export default function App() {
  const [personas, setPersonas] = useState([]);
  const [topic, setTopic] = useState(
    "Cities should ban private cars from downtown cores"
  );
  const [personaA, setPersonaA] = useState("utilitarian");
  const [personaB, setPersonaB] = useState("romantic");
  const [rounds, setRounds] = useState(3);

  const [status, setStatus] = useState("idle"); // idle | running | done | error
  const [turns, setTurns] = useState([]); // {speaker, round, text, persona}
  const [scores, setScores] = useState([]); // {round, result}
  const [currentRound, setCurrentRound] = useState(0);
  const [finalTally, setFinalTally] = useState(null);
  const [error, setError] = useState(null);
  const sourceRef = useRef(null);

  useEffect(() => {
    fetch("/api/personas")
      .then((r) => r.json())
      .then(setPersonas)
      .catch(() => {
        // Fallback list so the UI still renders if the backend isn't up yet
        setPersonas([
          { id: "utilitarian", name: "The Utilitarian", tagline: "" },
          { id: "contrarian", name: "The Contrarian Skeptic", tagline: "" },
          { id: "literalist", name: "The Literal Engineer", tagline: "" },
          { id: "romantic", name: "The Romantic Idealist", tagline: "" },
          { id: "historian", name: "The Historian", tagline: "" },
        ]);
      });
  }, []);

  function startDebate() {
    if (sourceRef.current) sourceRef.current.close();
    setTurns([]);
    setScores([]);
    setFinalTally(null);
    setError(null);
    setCurrentRound(1);
    setStatus("running");

    const params = new URLSearchParams({
      topic,
      persona_a: personaA,
      persona_b: personaB,
      rounds: String(rounds),
    });
    const source = new EventSource(`/api/debate/stream?${params}`);
    sourceRef.current = source;

    source.addEventListener("turn", (e) => {
      const data = JSON.parse(e.data);
      setCurrentRound(data.round);
      setTurns((prev) => [...prev, data]);
    });

    source.addEventListener("score", (e) => {
      const data = JSON.parse(e.data);
      setScores((prev) => [...prev, data]);
    });

    source.addEventListener("done", (e) => {
      const data = JSON.parse(e.data);
      setFinalTally(data);
      setStatus("done");
      source.close();
    });

    source.onerror = () => {
      setError(
        "Lost connection to the debate stream. Make sure the backend is running on :8000 and your ANTHROPIC_API_KEY is set."
      );
      setStatus("error");
      source.close();
    };
  }

  const personaName = (id) =>
    personas.find((p) => p.id === id)?.name ?? id;

  // Tug-of-war fill: how much of the total judge score debater_a currently holds
  const tugPct = (() => {
    if (scores.length === 0) return 50;
    let a = 0,
      b = 0;
    for (const s of scores) {
      const sc = s.result?.scores;
      if (!sc) continue;
      for (const axis of ["logic", "evidence", "rebuttal"]) {
        a += sc.debater_a?.[axis] ?? 0;
        b += sc.debater_b?.[axis] ?? 0;
      }
    }
    if (a + b === 0) return 50;
    return Math.round((a / (a + b)) * 100);
  })();

  return (
    <div className="arena">
      <div className="arena-header">
        <h1>Debate Arena</h1>
        <p>
          Two AI personas argue opposite sides of a motion. A third agent
          judges every round on logic, evidence, and rebuttal.
        </p>
      </div>

      <div className="setup">
        <label htmlFor="topic">Motion to debate</label>
        <input
          id="topic"
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          disabled={status === "running"}
        />

        <div className="side-pickers">
          <div>
            <label className="side-a-label">For</label>
            <select
              value={personaA}
              onChange={(e) => setPersonaA(e.target.value)}
              disabled={status === "running"}
            >
              {personas.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
          <div className="vs-glyph">vs</div>
          <div>
            <label className="side-b-label">Against</label>
            <select
              value={personaB}
              onChange={(e) => setPersonaB(e.target.value)}
              disabled={status === "running"}
            >
              {personas.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <label htmlFor="rounds">Rounds</label>
        <select
          id="rounds"
          value={rounds}
          onChange={(e) => setRounds(Number(e.target.value))}
          disabled={status === "running"}
        >
          {[1, 2, 3, 4, 5].map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>

        <button
          className="start-btn"
          onClick={startDebate}
          disabled={status === "running" || !topic.trim()}
        >
          {status === "running" ? "Debate in progress..." : "Start debate"}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {status !== "idle" && (
        <>
          <div className="round-strip">
            Round {Math.min(currentRound, rounds)} of {rounds}
          </div>
          <div className="tug">
            <div className="tug-fill" style={{ width: `${tugPct}%` }} />
          </div>

          <div className="duel">
            <div className="side-column side-a">
              <div className="side-header">
                <span className="side-name">{personaName(personaA)}</span>
                <span className="side-stance">For</span>
              </div>
              {turns
                .filter((t) => t.speaker === "debater_a")
                .map((t, i) => (
                  <div className="turn-card" key={`a-${i}`}>
                    <div className="turn-round-tag">Round {t.round}</div>
                    {t.text}
                  </div>
                ))}
              {status === "running" &&
                turns.filter((t) => t.speaker === "debater_a").length <
                  currentRound && (
                  <div className="thinking">
                    <span />
                    <span />
                    <span />
                  </div>
                )}
            </div>

            <div className="side-column side-b">
              <div className="side-header">
                <span className="side-name">{personaName(personaB)}</span>
                <span className="side-stance">Against</span>
              </div>
              {turns
                .filter((t) => t.speaker === "debater_b")
                .map((t, i) => (
                  <div className="turn-card" key={`b-${i}`}>
                    <div className="turn-round-tag">Round {t.round}</div>
                    {t.text}
                  </div>
                ))}
              {status === "running" &&
                turns.filter((t) => t.speaker === "debater_b").length <
                  turns.filter((t) => t.speaker === "debater_a").length && (
                  <div className="thinking">
                    <span />
                    <span />
                    <span />
                  </div>
                )}
            </div>
          </div>

          {scores.map((s, i) => {
            const sc = s.result?.scores;
            if (!sc) return null;
            return (
              <div className="judge-card" key={i}>
                <div className="judge-title">Judge — round {s.round}</div>
                <div className="judge-scores">
                  <div>
                    {["logic", "evidence", "rebuttal"].map((axis) => (
                      <div className="axis-row" key={axis}>
                        <span>{axis}</span>
                        <span>{sc.debater_a?.[axis] ?? "-"}</span>
                      </div>
                    ))}
                  </div>
                  <div>
                    {["logic", "evidence", "rebuttal"].map((axis) => (
                      <div className="axis-row" key={axis}>
                        <span>{axis}</span>
                        <span>{sc.debater_b?.[axis] ?? "-"}</span>
                      </div>
                    ))}
                  </div>
                  {sc.debater_a?.note && (
                    <div className="judge-note">For: {sc.debater_a.note}</div>
                  )}
                  {sc.debater_b?.note && (
                    <div className="judge-note">
                      Against: {sc.debater_b.note}
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {finalTally && (
            <div className="verdict">
              <div className="verdict-label">Overall winner</div>
              <div className="verdict-winner">
                {finalTally.overall_winner === "tie"
                  ? "It's a tie"
                  : personaName(
                      finalTally.overall_winner === "debater_a"
                        ? personaA
                        : personaB
                    )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
