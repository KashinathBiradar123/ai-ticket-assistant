import logging

from fastapi import APIRouter, HTTPException

from app.schemas import QueryRequest, QueryResponse
from app.services.query_service import query_service


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def ask_question(request: QueryRequest) -> QueryResponse:
    try:
        return query_service.answer_question(request.question)
    except ValueError as exc:
        logger.warning("Validation error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        logger.exception("Query processing failed.")
        raise HTTPException(status_code=500, detail=str(exc))