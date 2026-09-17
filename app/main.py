import logging

from fastapi import FastAPI

from app.api import anomalies, health, query


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="AI Ticket Assistant",
    description="AI-powered support ticket analytics system",
    version="1.0.0",
)

app.include_router(query.router, tags=["Query"])
app.include_router(anomalies.router, tags=["Anomalies"])
app.include_router(health.router, tags=["Health"])


@app.get("/")
def root():
    return {
        "name": "AI Ticket Assistant",
        "docs": "/docs",
        "endpoints": {
            "query": "POST /query",
            "anomalies": "GET /anomalies",
            "health": "GET /health",
        },
    }