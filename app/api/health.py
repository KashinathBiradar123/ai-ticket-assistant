import logging

from fastapi import APIRouter

from app.config import settings
from app.database import database
from app.llm.client import llm_client
from app.schemas import HealthResponse


logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    database_status = "ok"
    tickets_loaded = 0

    try:
        tickets_loaded = database.execute_scalar(
            "SELECT COUNT(*) FROM tickets"
        ) or 0
    except Exception:
        logger.exception("Database health check failed.")
        database_status = "error"

    llm_available = False
    try:
        llm_available = llm_client.is_available()
    except Exception:
        logger.exception("LLM health check failed.")

    if database_status == "ok" and llm_available:
        status = "healthy"
    elif database_status == "ok":
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        database=database_status,
        tickets_loaded=tickets_loaded,
        llm_provider=settings.llm_provider,
        llm_available=llm_available,
    )