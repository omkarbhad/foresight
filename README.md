# Foresight — AI Multi-Agent Scenario Simulator

Foresight is an AI-powered scenario simulation platform. Describe any event — a geopolitical crisis, market shock, product recall, or PR disaster — and Foresight spins up 5–20 AI agents (journalists, analysts, governments, markets, consumers, etc.) that react, influence each other, and play out the scenario over multiple rounds. You get a full timeline of how events would unfold, with sentiment trajectories and influence chains.

Multiple scenarios run in a **shared simulation** — each scenario generates its own agents, then all agents interact across rounds. Cross-scenario influence is tracked and visualized, revealing how events compound each other (e.g. a military conflict amplifying an oil price shock).

## How It Works

1. **Describe scenarios** — Enter one or more events (e.g. "USA attacks Iran", "Oil prices spike 40%"). Use commas to separate multiple scenarios.
2. **Configure rounds** — Choose 3–8 rounds. Each round represents a time window (Hour 0–2, Day 1–2, Week 1, etc.).
3. **Per-scenario agent generation** — Claude generates 8–12 agents per scenario, tailored to that scenario's domain. In multi-scenario simulations, agent pools are merged into a shared simulation with cross-scenario influence starting empty and emerging organically.
4. **Real-world data grounding** — Before the simulation starts, the engine fetches live data from NewsAPI, Reddit, Twitter/X, and Finnhub to brief agents on current real-world context.
5. **Watch it unfold** — Each round, every agent receives the scenario, their persona, compressed history, influence context (tagged with source scenario), and current metrics. They produce structured actions (articles, social posts, policy statements, market moves, etc.).
6. **Dynamic entity discovery** — After each round, agent outputs are analyzed for newly mentioned entities. Real-world data is fetched for each entity, and new agents are generated with backstories grounded in that data. These new agents join the next round.
7. **Cross-scenario tracking** — Every action and influence link is tagged with its originating scenario. Cross-scenario interactions (e.g. a defense journalist's article influencing an oil trader) are tracked separately and visualized.
8. **Analyze results** — View per-scenario sentiment breakdowns, cross-scenario interaction effects, influence chains, an interactive network graph with scenario clustering, and a round-by-round breakdown of every action.

---

## Architecture

```
┌────────────────────┐     ┌───────────────────────────────────────────────┐
│   Vue 3 Frontend   │────▶│              Flask Backend API                │
│   (Vite, D3.js)    │◀────│                                               │
│   localhost:3000    │     │   ┌────────────────┐  ┌────────────────────┐  │
└────────────────────┘     │   │ CrewAI Engine   │  │  Graph Memory      │  │
                           │   │ (Multi-Agent)   │  │  (Neo4j, optional) │  │
                           │   └───────┬─────────┘  └────────┬───────────┘  │
                           │           │                      │              │
                           │   ┌───────▼──────────────────────▼───────────┐ │
                           │   │            Service Layer                  │ │
                           │   │  Personas │ Influence │ Scenario Data    │ │
                           │   │  Entity Discovery │ Cross-Scenario       │ │
                           │   └───────┬──────────────────────┬───────────┘ │
                           │           │                      │              │
                           │   ┌───────▼─────────────────▼────────────────┐ │
                           │   │   Claude API (Anthropic SDK)              │ │
                           │   │   Agent reasoning + structured output     │ │
                           │   └──────────────────────────────────────────┘ │
                           │                          localhost:5001         │
                           └────────────────────────────────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────────────┐
                    │  Supabase PostgreSQL    │    Neo4j (opt.)    │
                    │  simulations │ tasks    │    Graph memory    │
                    └─────────────────────────────────────────────┘
```

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3, Vue Router, D3.js v7, Axios, Vite |
| Backend | Python 3.11+, Flask, Flask-CORS |
| AI | Claude (Anthropic SDK), CrewAI (multi-agent orchestration) |
| Database | Supabase PostgreSQL (psycopg2) |
| Graph | Neo4j 5 (optional, for cross-simulation memory) |
| Data Sources | NewsAPI, Reddit (PRAW), Twitter/X (Tweepy), Finnhub |
| Infrastructure | Docker, Docker Compose |

---

## Project Structure

```
foresight/
├── package.json                     # Root — concurrently runs frontend + backend
├── .env.example
├── Dockerfile
├── docker-compose.yml               # App + Neo4j
│
├── backend/
│   ├── run.py                       # Entry point
│   ├── pyproject.toml               # Python dependencies
│   ├── migrations/                  # PostgreSQL schema
│   └── app/
│       ├── __init__.py              # Flask app factory
│       ├── config.py                # Environment configuration
│       ├── db.py                    # PostgreSQL connection pool
│       ├── api/
│       │   ├── simulations.py       # POST/GET simulation endpoints
│       │   └── tasks.py             # Async task polling + cancel
│       ├── models/
│       │   ├── simulation.py        # Simulation result persistence
│       │   └── task.py              # In-memory async task manager
│       ├── services/
│       │   ├── crewai_engine.py     # Multi-agent orchestrator + cross-scenario logic
│       │   ├── crewai_agents.py     # Agent defs, dynamic generation, per-scenario budgets
│       │   ├── crewai_tools.py      # Custom tools for agents
│       │   ├── simulation_personas.py # Persona archetypes
│       │   ├── scenario_data_fetcher.py # Real data grounding (News, Reddit, Twitter, Finnhub)
│       │   ├── historical_loader.py # Historical context loading
│       │   ├── influence_matrix.py  # Cross-agent influence modeling (scenario-aware)
│       │   ├── entity_discovery.py  # Between-round entity extraction + data fetching
│       │   ├── graph_memory.py      # Neo4j graph memory (optional)
│       │   ├── graph_schema.py      # Neo4j schema init
│       │   └── graph_tools.py       # Graph query utilities
│       └── utils/
│           ├── claude_client.py     # Anthropic SDK wrapper
│           ├── embeddings.py        # Voyage AI embeddings (optional)
│           ├── logger.py            # File + console logging
│           └── retry.py             # Exponential backoff
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.js / App.vue
        ├── router/index.js
        ├── api/
        │   ├── index.js             # Axios instance
        │   └── simulation.js        # Simulation + task API client
        ├── views/
        │   └── SimulationView.vue   # Main simulation page
        └── components/
            ├── layout/              # AppHeader, AppSidebar, AppLayout
            └── simulation/          # SimulationForm, SimulationTimeline,
                                     # SimulationResults, PersonaCard,
                                     # RoundMetrics, LiveInfluenceGraph
```

---

## Getting Started

### Prerequisites

- **Node.js** >= 18
- **Python** >= 3.11
- **Supabase** account (or any PostgreSQL database)
- **Claude API key** from [Anthropic](https://console.anthropic.com/)

### 1. Clone and Install

```bash
git clone https://github.com/Kartik1745/foresight.git
cd foresight

npm run setup
npm run setup:backend
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Required
CLAUDE_API_KEY=sk-ant-...
DATABASE_URL=postgresql://postgres.xxx:password@aws-0-region.pooler.supabase.com:6543/postgres
```

### 3. Run Migrations

```bash
psql "$DATABASE_URL" -f backend/migrations/001_initial.sql
psql "$DATABASE_URL" -f backend/migrations/002_simulations.sql
psql "$DATABASE_URL" -f backend/migrations/003_simulation_v2.sql
```

### 4. Start

```bash
npm run dev
```

- **Backend** → `http://localhost:5001`
- **Frontend** → `http://localhost:3000`

---

## Simulation Engine

The core of Foresight is a CrewAI-powered multi-agent simulation engine with structured cross-scenario influence tracking.

### Single Scenario

When you submit a single scenario, the engine:

1. **Selects agents** — Claude picks 5–20 agents relevant to the scenario (e.g. a geopolitical crisis gets defense analysts, foreign ministers, oil traders; a product recall gets journalists, consumers, lawyers)
2. **Fetches real-world data** — Queries NewsAPI, Reddit, Twitter/X, and Finnhub for current context, runs sentiment analysis, and builds a briefing for agents
3. **Runs rounds** — Each round, every agent gets the scenario + persona prompt + compressed history + influence context + current metrics, and produces a structured JSON action
4. **Computes influence** — An influence matrix propagates effects between agents (a journalist's article shifts consumer sentiment, a government statement moves markets, etc.)
5. **Discovers entities** — After each round, agent outputs are analyzed for newly mentioned entities not yet represented. Real-world data is fetched for each, and new agents are generated with data-grounded backstories to join the next round
6. **Generates summary** — Claude produces a final executive summary with sentiment trajectories, turning points, and recommended actions

### Multi-Scenario (Cross-Scenario Influence)

When you submit multiple comma-separated scenarios, the engine adds structured cross-scenario dynamics:

1. **Per-scenario agent generation** — Each scenario gets its own Claude call to generate up to 12 agents specific to that domain. Agent keys are deduplicated (prefixed on collision).
2. **Merged simulation pool** — All agents from all scenarios are interleaved into a shared execution order. Cross-scenario influence connections start empty and emerge organically.
3. **Scenario-aware prompts** — Each agent sees the full combined scenario but knows its PRIMARY SCENARIO. Influence context shows `[Scenario: X]` tags so agents understand cross-scenario dynamics.
4. **Structured tracking** — Every action is tagged with its originating scenario. Every influence log entry records `from_scenario`, `to_scenario`, and `cross_scenario: true/false`.
5. **Per-scenario metrics** — Round metrics include per-scenario sentiment/volume breakdowns and a cross-scenario interaction count.
6. **Entity discovery with scenario assignment** — New entities discovered between rounds are assigned to the scenario whose agents mentioned them most.
7. **Cross-scenario summary** — The final analysis includes per-scenario summaries, cross-scenario dynamics narrative, and interaction effects.

### Agent Budgets

| Mode | Initial Cap | Expansion Cap | Per-Scenario Budget |
|------|------------|---------------|---------------------|
| Single scenario | 30 | 30 | — |
| Multi-scenario | 12 per scenario | 50 total | 12 |

### Dynamic Entity Discovery

After each round (except the last), the engine:

1. **Extracts entities** — Claude analyzes agent outputs for newly mentioned countries, organizations, people, industries not yet represented (up to 5 per round)
2. **Fetches live data** — Parallel queries to NewsAPI, Reddit, Twitter/X, and Finnhub for each entity
3. **Synthesizes briefings** — Claude condenses raw data into ~200-word research briefings with specific facts, quotes, and data points
4. **Generates agents** — New agents are created with backstories grounded in real data, influence connections, and execution order placement
5. **Merges into pool** — New agents join the next round, influence weights are renormalized, and the influence matrix is updated

### Built-in Persona Archetypes (Fallback)

| Persona | Role | Reach | Weight |
|---------|------|-------|--------|
| Journalist | Investigative reporter | 3.0x | 20% |
| Analyst | Senior industry analyst | 2.5x | 15% |
| Influencer | Social media (500K followers) | 5.0x | 15% |
| Consumer | Public/customer voice | 0.5x | 10% |
| Investor | Institutional portfolio manager | 4.0x | 15% |
| Competitor | Rival brand PR | 2.0x | 5% |
| Regulator | Government regulatory body | 6.0x | 10% |
| Brand PR | Crisis response team | 3.5x | 10% |

In dynamic mode (default), Claude generates scenario-specific agents that may include defense analysts, foreign ministers, oil traders, central bankers, humanitarian organizations, military commanders, supply chain managers, and more — whatever the scenario demands.

### Scenario Presets

Quick-start presets are built in: US-Iran Conflict, Russia-Ukraine Escalation, Oil Price Shock, Taiwan Strait Crisis, Market Crash, Climate Summit Failure.

---

## Influence Graph UI

The influence network is rendered as an interactive D3 force-directed graph:

- **Scenario clustering** — Agents from the same scenario are nudged together with convex hull backgrounds
- **Scenario-colored rings** — Each node has an outer ring colored by its scenario
- **Edge types** — Solid lines for within-scenario influence, dashed amber lines for cross-scenario influence
- **Filtering** — Dropdown to show all scenarios, cross-scenario only, or a single scenario
- **Hover tooltips** — Agent name, role, scenario, and interaction stats
- **Interactive** — Draggable nodes, highlight-on-hover for connected edges
- **Legend** — Scenario colors and edge type key

For single-scenario simulations, the graph renders without scenario-specific features.

---

## API

### Simulations
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/simulations` | Start a simulation (returns `task_id`) |
| `GET` | `/api/simulations` | List past simulations |
| `GET` | `/api/simulations/:id` | Get full simulation result |

**POST body:**
```json
{
  "scenarios": ["USA attacks Iran", "Oil prices spike 40%"],
  "config": { "total_rounds": 6 }
}
```

**Result includes** (for multi-scenario):
- `scenario_map` — Index to scenario name mapping
- `agent_scenario_map` — Agent key to scenario mapping
- `influence_log[].from_scenario`, `.to_scenario`, `.cross_scenario`
- `aggregate_metrics.per_scenario_summary`, `.cross_scenario_dynamics`, `.interaction_effects`
- `rounds[].metrics.per_scenario`, `.cross_scenario_interactions`

### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/tasks/:task_id` | Poll task status + progress |
| `POST` | `/api/tasks/:task_id/cancel` | Cancel a running simulation |
| `GET` | `/api/tasks` | List all tasks |

---

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CLAUDE_API_KEY` | Yes | — | Anthropic API key |
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `CLAUDE_MODEL_NAME` | No | `claude-sonnet-4-20250514` | Claude model |
| `NEWS_API_KEY` | No | — | NewsAPI key for real-world data grounding |
| `REDDIT_CLIENT_ID` | No | — | Reddit API client ID |
| `REDDIT_CLIENT_SECRET` | No | — | Reddit API client secret |
| `TWITTER_BEARER_TOKEN` | No | — | Twitter/X API bearer token |
| `FINNHUB_API_KEY` | No | — | Finnhub API key for market data |
| `NEO4J_URI` | No | `bolt://localhost:7687` | Neo4j URI (optional) |
| `NEO4J_USER` | No | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | No | — | Neo4j password |
| `GRAPH_MEMORY_ENABLED` | No | `false` | Enable cross-simulation graph memory |
| `FLASK_PORT` | No | `5001` | Backend port |
| `FLASK_DEBUG` | No | `True` | Debug mode |

---

## Docker

```bash
docker-compose up --build
```

Starts the app (ports 3000 + 5001) and Neo4j (ports 7474 + 7687).

---