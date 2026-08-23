# HIGHBASE — Your Smarter Sales Assistant

> Turn business data into better buying decisions.

HIGHBASE is an AI-powered sales assistant for shop owners, restaurants, cafés, mini markets, caterers, and hotels. Ask a simple question and get a clear answer about products, prices, inventory, offers, sales performance, and what is trending.

Powered by FastAPI, trusted business-data tools, and local Ollama AI (`qwen3:8b`), HIGHBASE connects friendly conversation with reliable product intelligence.

> **Demo note:** This project currently uses synthetic HIGHBASE data. Product URLs, offers, stock, and business metrics are demonstration data—not a live catalog.

## What HIGHBASE offers

### A helpful business conversation

Chat naturally instead of searching through spreadsheets or dashboards. HIGHBASE understands questions such as:

- “Which coffee products are in stock?”
- “What is the price of Highbase Coffee 1?”
- “What offers are available?”
- “What products are trending?”
- “Show me products under 5 BHD.”
- “How many orders are in the database?”

It handles greetings and follow-up questions naturally, while staying focused on HIGHBASE business information.

### Product discovery and recommendations

Find relevant products using product names, categories, budgets, and availability. Recommendations are explainable, include reasons and links, and exclude products that are out of stock.

### Inventory visibility

Check stock status and quantities before making a decision. Missing or zero stock is reported clearly instead of being treated as available.

### Offers and pricing

See current synthetic offers with the regular price, discounted price, discount percentage, eligibility, description, and validity date. Price questions return structured product facts rather than vague chatbot guesses.

### Trend discovery

Discover products and categories gaining momentum through recent sales growth. Trend results include growth values and a clear “Trending” label.

### Business intelligence

Explore aggregate sales, categories, orders, revenue-related metrics, co-purchases, RFM signals, inventory, and database collection counts through chat or API endpoints.

### Safe, grounded answers

The assistant cannot execute arbitrary database queries. It can only use approved read-only tools, and it must use returned data for prices, stock, offers, trends, and sales facts. Unrelated questions receive a friendly redirect instead of an invented answer.

## Why it is useful

```text
Ask naturally → Retrieve trusted business facts → Understand the answer → Act faster
```

HIGHBASE brings the practical benefits of a sales dashboard into a simple customer-service conversation:

- Less time searching through data.
- Faster product and stock checks.
- Clearer purchasing decisions.
- Explainable recommendations instead of black-box rankings.
- One friendly interface for catalog and business questions.

## Product capabilities

- EDA, data cleaning, feature engineering, sales analytics, trends, RFM, co-purchases, and inventory intelligence.
- Explainable recommendations with availability, score, reasons, and product URLs.
- Offers with discount, offer price, validity, eligibility, and description.
- Ollama chat with validated tools: `search_products`, `check_inventory`, `get_product_details`, `get_analytics_summary`, `get_offers`, `get_trending_products`, and `get_database_overview`.
- Structured product facts for prices, offers, availability, stock, trends, and freshness.
- Browser chat UI with loading states, retry handling, and product cards.
- Short-lived chat sessions and deterministic fallback when Ollama is unavailable.
- JSON storage by default, with a MongoDB repository adapter.

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
