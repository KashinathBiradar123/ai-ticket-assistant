#!/bin/bash

set -e

if [ ! -f ".env" ]; then
    echo "Error: .env not found."
    exit 1
fi

if [ ! -f "data/tickets.db" ]; then
    python -m app.ingest
fi

uvicorn app.main:app --host 0.0.0.0 --port 8000 &
FASTAPI_PID=$!

streamlit run ui/streamlit_app.py --server.port 8501 &
STREAMLIT_PID=$!

echo ""
echo "API:  http://localhost:8000"
echo "UI:   http://localhost:8501"
echo "Docs: http://localhost:8000/docs"
echo ""

trap "kill $FASTAPI_PID $STREAMLIT_PID" EXIT
wait