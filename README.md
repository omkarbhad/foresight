<p align="center">
  <img src="frontend/public/favicon.svg" width="96" height="96" alt="Foresight" />
</p>

<h1 align="center">Foresight</h1>

<p align="center">
  <b>A multi-agent scenario simulator — describe an event, watch AI agents react, influence each other, and play it out round-by-round.</b>
</p>

<p align="center">
  <a href="#-why-foresight">Why</a> ·
  <a href="#-features">Features</a> ·
  <a href="#-quick-start">Quick Start</a> ·
  <a href="#-how-it-works">How It Works</a> ·
  <a href="#-api-reference">API</a> ·
  <a href="#-roadmap">Roadmap</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Vue-3-42b883?logo=vuedotjs&logoColor=white" alt="Vue 3" />
  <img src="https://img.shields.io/badge/Vite-5-646cff?logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/D3.js-graph-f9a03c?logo=d3dotjs&logoColor=white" alt="D3.js" />
  <img src="https://img.shields.io/badge/Python-3.11-3776ab?logo=python&logoColor=white" alt="Python 3.11" />
  <img src="https://img.shields.io/badge/Flask-API-000?logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/CrewAI-multi--agent-ef4444" alt="CrewAI" />
  <img src="https://img.shields.io/badge/LiteLLM-provider--agnostic-8b5cf6" alt="LiteLLM" />
  <img src="https://img.shields.io/badge/PostgreSQL-Neo4j-336791?logo=postgresql&logoColor=white" alt="PostgreSQL + Neo4j" />
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License" />
</p>

<p align="center">
  <img src="frontend/public/preview.png" alt="Foresight preview" width="820" />
</p>

---

## ✨ Why Foresight?

Most "AI simulation" demos are a single LLM roleplaying every character in one prompt. That's fiction, not simulation. **Foresight is a real multi-agent system** — each agent is its own LLM call with its own context, its own memory of prior rounds, and its own influence links to the other agents in the scene.

- **Agents are grounded in real data.** Each agent's backstory and stance come from live NewsAPI, Reddit, Twitter/X, and Finnhub fetches — not invented from thin air.
- **The scenario evolves.** Between rounds, an entity-discovery pass extracts new actors that emerged in the last round and spawns them as fresh agents with their own real-data backstories.
- **Cross-scenario influence is tracked.** Run multiple scenarios in one simulation and watch agents from different crises nudge each other through a visualized influence graph.
- **Structured, not free-text.** Every agent action returns typed output (sentiment, influence target, action type) so you get a trajectory, not a wall of roleplay.

> Unlike "GPT roleplays world leaders" demos, **Foresight runs a structured, grounded, multi-round crew where agents react to each other and to the real world** — with a live D3 influence graph, sentiment trajectories, and a full post-run analysis.

---

## 📑 Table of Contents

<details>
<summary>Click to expand</summary>

- [✨ Why Foresight?](#-why-foresight)
- [🎯 Purpose-Built for Scenario Exploration (vs Alternatives)](#-purpose-built-for-scenario-exploration-vs-alternatives)
- [🔭 Features](#-features)
- [🧰 Tech Stack](#-tech-stack)
- [🧠 How It Works](#-how-it-works)
- [🏗 Architecture](#-architecture)
- [🚀 Quick Start](#-quick-start)
- [🔑 Configuration](#-configuration)
- [🌐 API Reference](#-api-reference)
- [📁 Project Structure](#-project-structure)
- [🗺 Roadmap](#-roadmap)
- [🤝 Contributing](#-contributing)
- [📜 License](#-license)
- [🙏 Acknowledgments](#-acknowledgments)

</details>

---

## 🎯 Purpose-Built for Scenario Exploration (vs Alternatives)

There are many ways to think about "what if X happens?" None of them do the job Foresight does — each was built for a different question:

| Tool / Approach | What it answers | Where Foresight differs |
|---|---|---|
| **ChatGPT "roleplay as world leaders"** | "Write me a story about X" | Single prompt, no persistence, no influence graph, no real-world grounding, no structured output |
| **CrewAI / AutoGen / LangGraph** (frameworks) | "How do I wire agents together?" | Those are *frameworks*; Foresight is a **domain-specific simulator** built on top, with real-world grounding, entity discovery, and cross-scenario influence already wired in |
| **Metaculus / Manifold** (prediction markets) | "What do humans think will happen?" | Crowdsourced probabilities; Foresight runs **structured agent reasoning** you can inspect round-by-round |
| **Scenario-planning consultancies** | "Pay us to run a workshop" | $$$, slow, opaque. Foresight is **instant, reproducible, and open-source** |
| **Monte Carlo / agent-based econ models** | "Simulate 10k runs of a narrow system" | Great for narrow numeric systems; Foresight is **open-ended, LLM-reasoned, and cross-domain** (geopolitics + markets + media in one run) |
| **Foresight (this project)** | *"What second-order effects spill out from this event, and who reacts to whom?"* | Grounded agents · influence graph · entity discovery · cross-scenario coupling · structured output |

### Why a generic multi-agent framework would miss the point

You *could* wire this up in raw CrewAI or LangGraph. Foresight does four things on top that a generic framework does not:

1. **Real-world grounding at agent-gen time.** Before any round runs, [`scenario_data_fetcher.py`](backend/app/services/scenario_data_fetcher.py) pulls live NewsAPI / Reddit / Twitter / Finnhub signals and injects them into each agent's backstory. Agents know the actual current state of the world, not a training-cutoff hallucination.
2. **Entity discovery between rounds.** [`entity_discovery.py`](backend/app/services/entity_discovery.py) scans each round's outputs for new actors that emerged ("a new opposition party forms", "a hedge fund takes a position") and spawns them as fresh agents with their own real-data backstories before the next round. The cast grows organically.
3. **An influence matrix, not a chat log.** [`influence_matrix.py`](backend/app/services/influence_matrix.py) tracks directional influence between every pair of agents, which is what drives the D3 graph and the post-run influence chain analysis. Without it you just have unrelated monologues.
4. **Cross-scenario coupling.** Multiple scenarios in one simulation share the same agent pool, so a market shock and a geopolitical crisis can spill into each other's influence graph. No generic framework gives you this for free.

### Honest trade-offs

**Foresight is not a forecasting oracle.** It will not tell you what *will* happen — LLM agents don't have that kind of calibration, and no structured prompting fixes that. What it *is* good at is **exposing second-order effects you hadn't considered**: who reacts, who gets ignored, which actors amplify each other, where narratives diverge.

- Use **Metaculus / Manifold** if you want calibrated probability estimates.
- Use a **domain-specific numeric model** if you're simulating a narrow system (supply chain, epidemiology, trading book).
- Use **Foresight** when you want to rapidly explore *"who reacts to this and how do those reactions collide?"* across a messy, multi-actor, cross-domain scenario.

---

## 🔭 Features

### 🤖 Multi-Agent Simulation
- **8–12 agents per scenario** — auto-generated, domain-tailored
- **Per-agent roles** — journalists, analysts, governments, markets, militaries, NGOs
- **Per-round structured actions** — not free-text roleplay, typed output with sentiment + influence targets
- **CrewAI orchestration** via [`crewai_engine.py`](backend/app/services/crewai_engine.py)

### 🌍 Real-World Grounding
- **NewsAPI** for recent headlines and framing
- **Reddit** for grassroots sentiment and emerging narratives
- **Twitter / X** for high-velocity signals
- **Finnhub** for market data when scenarios touch finance
- Injected at agent-generation time so backstories reflect **the actual current state of the world**

### 🔗 Influence Graph
- **D3 force-directed layout** in the browser
- **Directional edges** show *who influenced whom* each round
- **Cross-scenario links** highlighted when multi-scenario mode is on
- Click any node to inspect the agent's actions and sentiment trajectory

### 🧬 Entity Discovery
- After every round, a discovery pass extracts **new actors that emerged** in the previous round
- Each new entity becomes a fresh agent with its own real-data backstory
- The simulation **grows its cast organically** as the scenario unfolds

### 📊 Post-Run Analysis
- **Sentiment trajectories** per agent over time
- **Turning points** — rounds where aggregate sentiment flips
- **Influence chains** — who kicked off which cascade
- **Recommended actions** — agent-derived, not oracular predictions

### 🔌 Provider-Agnostic LLMs
- Unified client via **LiteLLM** — Anthropic, OpenRouter, OpenAI, and more
- Swap providers in the in-app **Settings panel** — no restart
- API keys live in settings *or* `.env`

### 🧠 Optional Graph Memory
- **Neo4j** (optional) — persistent cross-simulation knowledge graph
- Enables long-running world-state that carries across separate simulation runs

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Vue 3 · Vite · D3.js (force-directed graph) · Axios |
| **Backend** | Python 3.11 · Flask REST API |
| **Multi-Agent Engine** | CrewAI (wrapped in `crewai_engine.py`) |
| **LLM Gateway** | LiteLLM — Anthropic · OpenRouter · OpenAI |
| **Database** | PostgreSQL (simulations, tasks, settings) |
| **Graph Memory** | Neo4j (optional, cross-simulation memory) |
| **Data Grounding** | NewsAPI · Reddit · Twitter/X · Finnhub |
| **Deployment** | Docker + docker-compose (app + Neo4j) |

---

## 🧠 How It Works

```
 1. User enters scenarios (one or more, comma-separated)
              │
              ▼
 2. Data fetchers pull live context
     NewsAPI · Reddit · Twitter/X · Finnhub
              │
              ▼
 3. Agent generation — Claude crafts 8–12 agents per scenario
     (journalists, analysts, governments, markets, NGOs…)
              │
              ▼
 4. Round loop ──────────────┐
     For each agent:         │
       • read scenario state │
       • read influence from │
         other agents        │
       • emit typed action   │
              │              │
              ▼              │
 5. Entity discovery ────────┤
     extracts new actors     │
     and spawns fresh agents │
              │              │
              ▼              │
 6. Influence matrix update  │
     directional links are   │
     added to the graph      │
              │              │
              └──── next round
              │
              ▼
 7. Final analysis
     sentiment · turning points · influence chains · recommended actions
```

---

## 🏗 Architecture

```
Frontend (Vue 3 + Vite + D3.js)
    │
    │  REST + polling
    ▼
Backend (Flask + Python 3.11)
    │
    ├── CrewAI engine ──────▶  LiteLLM  ──▶  Anthropic / OpenRouter / OpenAI
    │
    ├── Real-world fetchers ─▶  NewsAPI · Reddit · Twitter · Finnhub
    │
    ├── Influence matrix
    │
    ├── Entity discovery
    │
    ├── PostgreSQL  ◀──────────  simulations · tasks · settings
    │
    └── Neo4j (optional) ◀────  cross-simulation graph memory
```

**Key design decisions**

- 🧱 **CrewAI is wrapped, not exposed.** [`crewai_engine.py`](backend/app/services/crewai_engine.py) gives Foresight a stable surface so the underlying framework can be swapped without touching the UI or API.
- 📡 **Grounding happens at agent-gen time, not runtime.** Real-world data is fetched once per scenario, baked into backstories, and cached — so rounds stay fast and reproducible.
- 🧾 **Typed agent outputs.** Actions are structured (sentiment, target, action type) which is what makes the D3 graph, trajectories, and influence chains possible at all.
- 🔌 **Provider-agnostic via LiteLLM.** Users swap LLMs in the Settings panel — no redeploy, no code change.
- 💾 **Postgres for state, Neo4j for memory.** Two databases by design: relational state for simulations and tasks, graph memory for cross-run knowledge.

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+
- **Python** 3.11+
- **PostgreSQL** (or [Supabase](https://supabase.com))
- *(optional)* **Neo4j** for cross-simulation graph memory

### Install

```bash
git clone https://github.com/Kartik1745/foresight.git
cd foresight

# Install frontend + root deps
npm run setup

# Set up Python backend
npm run setup:backend
```

### Configure

```bash
cp .env.example .env
```

Edit `.env` with your database URL. LLM provider and API keys can be set in the in-app Settings panel *or* in `.env`:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/foresight
LLM_PROVIDER=openrouter
LLM_API_KEY=sk-or-...
```

### Database migrations

```bash
psql "$DATABASE_URL" -f backend/migrations/001_initial.sql
psql "$DATABASE_URL" -f backend/migrations/002_simulations.sql
psql "$DATABASE_URL" -f backend/migrations/003_simulation_v2.sql
```

### Run

```bash
npm run dev
```

Frontend → [`http://localhost:3000`](http://localhost:3000)
Backend → [`http://localhost:5001`](http://localhost:5001)

### Docker

```bash
docker-compose up --build
```

Starts the app (ports 3000 + 5001) and Neo4j (ports 7474 + 7687).

---

## 🔑 Configuration

All LLM and data-source settings can be configured via the in-app **Settings panel**. Alternatively, set them in `.env`:

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `LLM_PROVIDER` | — | `anthropic` · `openrouter` · `openai` |
| `LLM_MODEL` | — | Model name (e.g. `openrouter/auto`) |
| `LLM_API_KEY` | — | API key for the selected provider |
| `NEWS_API_KEY` | — | NewsAPI key — real-world grounding |
| `REDDIT_CLIENT_ID` | — | Reddit API client ID |
| `REDDIT_CLIENT_SECRET` | — | Reddit API client secret |
| `TWITTER_BEARER_TOKEN` | — | Twitter/X API bearer token |
| `FINNHUB_API_KEY` | — | Finnhub API key for market data |
| `NEO4J_URI` | — | Neo4j URI (optional graph memory) |
| `NEO4J_PASSWORD` | — | Neo4j password |
| `GRAPH_MEMORY_ENABLED` | — | Enable cross-simulation graph memory |

---

## 🌐 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/simulations` | Start a simulation (returns `task_id`) |
| `GET`  | `/api/simulations` | List past simulations |
| `GET`  | `/api/simulations/:id` | Get full simulation result |
| `GET`  | `/api/tasks/:task_id` | Poll task status + progress |
| `POST` | `/api/tasks/:task_id/cancel` | Cancel a running simulation |
| `GET`  | `/api/settings` | Get current settings |
| `POST` | `/api/settings` | Update LLM provider, API keys, data source keys |
| `POST` | `/api/settings/test-llm` | Test LLM connection |

---

## 📁 Project Structure

```
foresight/
├── package.json              # Root — runs frontend + backend concurrently
├── .env.example
├── Dockerfile
├── docker-compose.yml
│
├── backend/
│   ├── run.py                # Entry point
│   ├── pyproject.toml
│   ├── migrations/           # PostgreSQL schema
│   └── app/
│       ├── api/              # REST endpoints (simulations, tasks, settings)
│       ├── models/           # Simulation, Task persistence
│       └── services/
│           ├── crewai_engine.py       # Multi-agent orchestrator
│           ├── crewai_agents.py       # Agent generation + expansion
│           ├── influence_matrix.py    # Cross-agent influence
│           ├── entity_discovery.py    # Between-round entity extraction
│           ├── scenario_data_fetcher.py  # Real-world data grounding
│           ├── graph_memory.py        # Neo4j graph memory (optional)
│           └── llm_client.py          # Unified LLM client (LiteLLM)
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.vue
        ├── main.js
        ├── api/              # Axios API client
        ├── router/
        ├── views/
        │   └── SimulationCanvas.vue
        └── components/canvas/
            ├── TopBar.vue
            ├── SimulationForm.vue
            ├── InfluenceGraph.vue    # D3 force-directed graph
            ├── ActionFeed.vue
            ├── AgentActionCard.vue
            ├── ResultsSummary.vue    # Tabbed results (Summary, Rounds, Events)
            ├── MetricsBar.vue
            ├── SettingsModal.vue
            ├── FloatingAgents.vue
            └── ForesightLogo.vue
```

---

## 🗺 Roadmap

- [x] Multi-agent CrewAI orchestration
- [x] Real-world data grounding (News · Reddit · Twitter · Finnhub)
- [x] Cross-scenario influence tracking
- [x] Between-round entity discovery
- [x] D3 influence graph
- [x] Optional Neo4j graph memory
- [ ] Scenario templates (geopolitics, markets, public health, climate)
- [ ] Replay / time-scrubbing through rounds
- [ ] Export simulation as shareable report (PDF / Markdown)
- [ ] Agent persistence across simulations (long-running "actors")
- [ ] Calibration layer against real-world outcomes
- [ ] Multi-user collaboration on the same simulation

Got an idea? [Open an issue](https://github.com/Kartik1745/foresight/issues) or start a discussion.

---

## 🤝 Contributing

Contributions are what make open source amazing. **Any contribution you make is greatly appreciated.**

1. Fork the project
2. Create your feature branch — `git checkout -b feature/amazing-feature`
3. Commit your changes — `git commit -m 'Add amazing feature'`
4. Push to the branch — `git push origin feature/amazing-feature`
5. Open a Pull Request

👉 New here? Look for [`good first issue`](https://github.com/Kartik1745/foresight/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) labels.

---

## 📜 License

[MIT](LICENSE)

---

## 🙏 Acknowledgments

- [**CrewAI**](https://www.crewai.com) — the multi-agent orchestration framework this is built on
- [**LiteLLM**](https://www.litellm.ai) — provider-agnostic LLM gateway
- [**D3.js**](https://d3js.org) — force-directed influence graph
- [**NewsAPI**](https://newsapi.org) · [**Reddit**](https://www.reddit.com/dev/api) · [**Twitter/X API**](https://developer.x.com) · [**Finnhub**](https://finnhub.io) — real-world grounding
- [**Neo4j**](https://neo4j.com) — optional graph memory

---

<p align="center">
  Built with ❤️ for anyone who wants to stress-test a scenario before reality does.
</p>
