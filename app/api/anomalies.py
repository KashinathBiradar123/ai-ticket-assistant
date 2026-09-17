import logging

from fastapi import APIRouter, HTTPException, Query

from app.schemas import AnomalyResponse
from app.services.anomaly_service import anomaly_service


logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/anomalies", response_model=AnomalyResponse)
def get_anomalies(
    severity: str | None = Query(
        default=None,
        description="Filter by severity: critical, high, medium, low",
    ),
) -> AnomalyResponse:
    try:
        result = anomaly_service.detect_all()
    except Exception as exc:
        logger.exception("Anomaly detection failed.")
        raise HTTPException(status_code=500, detail=str(exc))

    if severity:
        filtered = [
            a for a in result.anomalies
            if a.severity.lower() == severity.lower()
        ]
        by_severity = {}
        for anomaly in filtered:
            by_severity[anomaly.severity] = (
                by_severity.get(anomaly.severity, 0) + 1
            )
        return AnomalyResponse(
            total_anomalies=len(filtered),
            by_severity=by_severity,
            anomalies=filtered,
        )

    return result