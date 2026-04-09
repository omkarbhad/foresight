<p align="center">
  <img src="frontend/public/favicon.svg" width="48" height="48" alt="Foresight" />
</p>

<h1 align="center">Foresight</h1>

<p align="center">
  AI multi-agent scenario simulator. Describe any event and watch AI agents react in real-time.
</p>

<p align="center">
  <img src="frontend/public/preview.png" alt="Foresight preview" width="800" />
</p>

---

Describe a geopolitical crisis, market shock, or any event. Foresight spins up AI agents — journalists, analysts, governments, markets, militaries, NGOs — that react, influence each other, and play out the scenario over multiple rounds. You get a live influence graph, action feed, sentiment trajectories, and a full analysis.

Multiple scenarios can run in a shared simulation. Each generates its own agents, then all agents interact across rounds. Cross-scenario influence is tracked and visualized.

## Getting Started

### Prerequisites

- Node.js >= 18
- Python >= 3.11
- PostgreSQL (or [Supabase](https://supabase.com))

### Install

```bash
git clone https://github.com/Kartik1745/foresight.git
cd foresight

# Install frontend + root dependencies
npm run setup

# Set up Python backend
npm run setup:backend
```

### Configure

```bash
cp .env.example .env
```

Edit `.env` with your database URL. LLM provider and API keys can be configured via the in-app Settings panel or in `.env`:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/foresight
LLM_PROVIDER=openrouter
LLM_API_KEY=sk-or-...
```

### Database

Run migrations against your PostgreSQL database:

```bash
psql "$DATABASE_URL" -f backend/migrations/001_initial.sql
psql "$DATABASE_URL" -f backend/migrations/002_simulations.sql
psql "$DATABASE_URL" -f backend/migrations/003_simulation_v2.sql
```

### Run

```bash
npm run dev
```

Opens **frontend** at `http://localhost:3000` and **backend** at `http://localhost:5001`.

### Docker

```bash
docker-compose up --build
```

Starts the app (ports 3000 + 5001) and Neo4j (ports 7474 + 7687).

## How It Works

1. **Enter scenarios** — one or more events, comma-separated
2. **Agent generation** — Claude generates 8-12 agents per scenario tailored to the domain
3. **Real-world grounding** — fetches live data from NewsAPI, Reddit, Twitter/X, Finnhub
4. **Simulation rounds** — each round, every agent receives scenario context, influence from other agents, and produces structured actions
5. **Entity discovery** — after each round, new entities are extracted and expanded into additional agents with real-data backstories
6. **Cross-scenario tracking** — in multi-scenario mode, all influence links are tagged with source/target scenario
7. **Analysis** — sentiment trajectories, turning points, influence chains, and recommended actions

## Architecture

```
Frontend (Vue 3 + Vite + D3.js)
    |
    v
Backend (Flask + Python 3.11)
    |
    +-- LLM (Anthropic / OpenRouter / OpenAI via LiteLLM)
    +-- PostgreSQL (simulations, tasks, settings)
    +-- Neo4j (optional graph memory)
    +-- Data Sources (NewsAPI, Reddit, Twitter/X, Finnhub)
```

## Project Structure

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

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/simulations` | Start a simulation (returns `task_id`) |
| `GET` | `/api/simulations` | List past simulations |
| `GET` | `/api/simulations/:id` | Get full simulation result |
| `GET` | `/api/tasks/:task_id` | Poll task status + progress |
| `POST` | `/api/tasks/:task_id/cancel` | Cancel a running simulation |
| `GET` | `/api/settings` | Get current settings |
| `POST` | `/api/settings` | Update LLM provider, API keys, data source keys |
| `POST` | `/api/settings/test-llm` | Test LLM connection |

## Configuration

All LLM and data source settings can be configured via the in-app Settings panel. Alternatively, set them in `.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `LLM_PROVIDER` | No | `anthropic`, `openrouter`, or `openai` |
| `LLM_MODEL` | No | Model name (e.g. `openrouter/auto`) |
| `LLM_API_KEY` | No | API key for the selected provider |
| `NEWS_API_KEY` | No | NewsAPI key for real-world data |
| `REDDIT_CLIENT_ID` | No | Reddit API client ID |
| `REDDIT_CLIENT_SECRET` | No | Reddit API client secret |
| `TWITTER_BEARER_TOKEN` | No | Twitter/X API bearer token |
| `FINNHUB_API_KEY` | No | Finnhub API key for market data |
| `NEO4J_URI` | No | Neo4j URI (optional graph memory) |
| `NEO4J_PASSWORD` | No | Neo4j password |
| `GRAPH_MEMORY_ENABLED` | No | Enable cross-simulation graph memory |

## License

[MIT](LICENSE)
