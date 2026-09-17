# AI Ticket Assistant

AI-powered customer support ticket analytics system. Ask questions in natural language, detect anomalies, and explore 500 support tickets via REST API and a web UI.

## Features

- **Natural Language Querying** — Ask questions in plain English, get SQL-backed answers
- **Text-to-SQL Pipeline** — LLM generates SQL, validates it, executes it, and explains results
- **Anomaly Detection** — 5 rule-based detectors
- **REST API** — FastAPI with 4 endpoints
- **Web UI** — Streamlit with 3 tabs
- **SQL Safety** — Whitelist validation (SELECT only, tickets table only)
- **LLM Fallback** — Groq (primary) + Ollama (local fallback)

## Architecture
CSV → Ingestion (Pandas + SQLite) → Queryable Database
↓
┌───────────────┴───────────────┐
↓ ↓
Natural Language Query Anomaly Engine
↓ ↓
LLM (Groq/Ollama) Rule/Stats Detection
↓ ↓
SQL Validation Flags
↓ ↓
SQLite Execution ↓
↓ ↓
LLM Answer Synthesis FastAPI
↓ ↓
└─────────→ FastAPI ←───────────┘
↓
Streamlit UI

## Tech Stack

| Layer | Tool |
|---|---|
| Data | Pandas + SQLite |
| API | FastAPI + Uvicorn |
| LLM | Groq (free tier) |
| LLM Fallback | Ollama |
| UI | Streamlit |
| DB Access | SQLAlchemy |

## Setup

### Prerequisites

- Python 3.10+
- Free Groq API key: https://console.groq.com

### Installation

```bash
git clone <your-repo-url>
cd ai-ticket-assistant

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your GROQ_API_KEY

python -m app.ingest
## Running

### One command (recommended)

```bash
python run.py