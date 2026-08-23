# HIGHBASE Customer Recommendation AI

FastAPI product recommendations and a customer-facing business chatbot powered by the local Ollama model `qwen3:8b`. The default data is synthetic demo data; product URLs and metrics are not production catalog data.

## Features

- EDA, cleaning, feature engineering, sales analytics, trends, RFM, co-purchases, and inventory intelligence.
- Explainable recommendations that exclude out-of-stock products.
- Ollama chat with validated, read-only tools: `search_products`, `check_inventory`, `get_product_details`, `get_analytics_summary`, `get_offers`, `get_trending_products`, and `get_database_overview`.
- Structured chat facts for prices, synthetic offers, offer validity, availability, and recent sales-growth trends.
- Short-lived in-memory sessions and a browser UI.
- JSON storage by default, with a MongoDB repository adapter.
- Deterministic fallback responses when Ollama is unavailable.

The model never receives a database connection or arbitrary query access. It can only call registered business tools.

## Architecture

```text
Browser/API → FastAPI → ChatOrchestrator → Ollama qwen3:8b
                              │                 │
                         SessionStore      ToolRegistry
                                                  │
                                           DatabaseTools
                                                  │
                                        JSON/Mongo repository
```

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- Ollama (optional; required for model-powered answers)
- Docker Desktop (optional; for MongoDB)

## Setup

```bash
cd HighBase_Inerview
cp .env.example .env
uv sync
uv run python scripts/generate_dummy_data.py
```

The generated collections are written to `data/` as JSON files.

## Ollama setup

```bash
ollama pull qwen3:8b
ollama list
```

Default `.env` values:

```env
LLM_MODEL=qwen3:8b
LLM_BASE_URL=http://localhost:11434/v1
LLM_TIMEOUT_SECONDS=1
```

The app uses Ollama's OpenAI-compatible `/v1/chat/completions` endpoint. Change `LLM_MODEL` to another pulled model if needed. If Ollama is stopped or unavailable, deterministic fallback behavior remains available.

## Run

```bash
uv run uvicorn app.main:app --reload
```

Open the chat UI at [http://localhost:8000/ui](http://localhost:8000/ui) or API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

## Data pipeline

```bash
curl -X POST http://localhost:8000/api/v1/data/seed
curl http://localhost:8000/api/v1/data/eda
curl -X POST http://localhost:8000/api/v1/data/clean
curl http://localhost:8000/api/v1/analytics/summary
```

Seed regenerates demo collections. Clean updates the active store and writes snapshots under `data/raw/` and `data/clean/`.

## Chat API

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Which coffee products are in stock?"}'
```

Useful questions include: “What categories exist?”, “Show top-selling products”, “Do we have milk under 5 BHD?”, “What offers are available?”, “What products are trending?”, and “How many products and orders are in the database?”.

Create, reuse, and delete a session:

```bash
curl -X POST http://localhost:8000/api/v1/chat/session
curl -X POST http://localhost:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"SESSION_ID","message":"What about products under 5 BHD?"}'
curl -X DELETE http://localhost:8000/api/v1/chat/session/SESSION_ID
```

Sessions are bounded, process-local, and expire after `CHAT_SESSION_TTL_SECONDS`; they are not persisted.

## API routes

| Route | Purpose |
|---|---|
| `GET /health` | Application health |
| `POST /data/seed` | Generate demo collections |
| `GET /data/eda` | Pre-cleaning data quality report |
| `POST /data/clean` | Clean data |
| `GET /data/pipeline/latest` | Latest pipeline run |
| `GET /analytics/summary` | Aggregate analytics |
| `POST /recommendations` | Explainable recommendations |
| `POST /chat` | Chatbot endpoint |
| `POST /chat/session` | Create session |
| `DELETE /chat/session/{session_id}` | Delete session |
| `GET /api/v1/db/overview` | Safe collection counts |
| `GET /ui` | Browser chat |

Data and chat routes are also available under `/api/v1` where applicable.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `STORAGE_BACKEND` | `json` | `json` or `mongo` |
| `DATA_PATH` | `data` | JSON directory |
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB URI |
| `MONGODB_DATABASE` | `highbase_mvp` | MongoDB database |
| `LLM_MODEL` | `qwen3:8b` | Ollama model |
| `LLM_BASE_URL` | `http://localhost:11434/v1` | Model endpoint |
| `LLM_TIMEOUT_SECONDS` | `1` | Request timeout |
| `CHAT_SESSION_TTL_SECONDS` | `1800` | Session TTL |
| `CHAT_MAX_HISTORY` | `12` | Messages retained per session |

## MongoDB with Docker

JSON is the default and needs no database service. To start the optional stack:

```bash
docker compose up --build
```

For MongoDB, set `STORAGE_BACKEND=mongo`, `MONGO_URI=mongodb://mongo:27017`, and `MONGODB_DATABASE=highbase_mvp`.

## Tests

```bash
uv run pytest -q
uv run python -m compileall -q app
```

## Project layout

```text
app/main.py              FastAPI routes and static UI serving
app/container.py         Dependency composition
app/agent.py             Ollama client and recommendation fallback
app/chat/                Session memory and chat orchestration
app/tools/               Validated read-only database tools
app/repositories/        JSON and MongoDB adapters
app/analytics/           Business analytics
app/recommendations/     Explainable ranking
app/pipeline/            EDA, cleaning, and feature engineering
app/static/              Browser chat UI
scripts/                 Demo data generation
tests/                   Automated tests
```

## Limitations

This is a local MVP. It does not include authentication, tenant isolation, customer-specific purchase history, catalog synchronization, cart/order creation, persistent conversations, scheduled ingestion, or production monitoring. The chatbot is read-only and uses synthetic data.
