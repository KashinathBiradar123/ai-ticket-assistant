# AI Ticket Assistant

![Architecture Diagram](docs/architecture.png)

AI-powered customer support ticket analytics system. Ask questions in natural language, detect anomalies, and explore 500 support tickets via REST API and a web UI.

## Features

- **Natural Language Querying** — Ask questions in plain English, get SQL-backed answers
- **Text-to-SQL Pipeline** — LLM generates SQL, validates it, executes it, and explains results
- **Anomaly Detection** — 5 rule-based detectors
- **REST API** — FastAPI with 4 endpoints
- **Web UI** — Streamlit with 3 tabs
- **SQL Safety** — Whitelist validation (SELECT only, tickets table only)
- **LLM Fallback** — Groq (primary) + Ollama (local fallback)
- **One-command start** — `python run.py`

## Architecture

The system is organized into three layers:

1. **Data Layer** — CSV → Pandas ingestion → SQLite queryable database
2. **Query Layer** — NL question → LLM → SQL validation → execution → LLM answer synthesis
3. **Anomaly Engine** — Rule-based and statistical detection (5 detectors)
4. **API/UI Layer** — FastAPI REST API + Streamlit UI

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
git clone https://github.com/KashinathBiradar123/ai-ticket-assistant.git
cd ai-ticket-assistant

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your GROQ_API_KEY

python -m app.ingest
