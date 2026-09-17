import logging

from app.database import database
from app.schemas import Anomaly, AnomalyResponse


logger = logging.getLogger(__name__)

PRIORITY_SEVERITY_MAP = {
    "Critical": "critical",
    "High": "high",
    "Medium": "medium",
    "Low": "low",
}


class AnomalyService:
    def get_reference_date(self) -> str:
        result = database.execute_scalar(
            "SELECT MAX(created_at) FROM tickets"
        )
        if not result:
            raise RuntimeError("No tickets found in the database.")
        return result

    def detect_unresolved_high_priority(self) -> list[Anomaly]:
        reference_date = self.get_reference_date()

        rows = database.execute_query(
            """
            SELECT ticket_id, priority, status, created_at
            FROM tickets
            WHERE priority IN ('High', 'Critical')
              AND status IN ('Open', 'Escalated')
              AND (
                  julianday(:reference_date) - julianday(created_at)
              ) * 24 > 24
            """,
            {"reference_date": reference_date},
        )

        anomalies = []
        for row in rows:
            anomalies.append(
                Anomaly(
                    ticket_id=row["ticket_id"],
                    reason=(
                        f"Unresolved {row['priority']} ticket "
                        f"older than 24 hours"
                    ),
                    severity=PRIORITY_SEVERITY_MAP.get(
                        row["priority"], "medium"
                    ),
                    details={
                        "priority": row["priority"],
                        "status": row["status"],
                        "created_at": row["created_at"],
                    },
                )
            )

        return anomalies

    def detect_long_resolution(self) -> list[Anomaly]:
        stats = database.execute_query(
            """
            SELECT resolution_time_hrs
            FROM tickets
            WHERE resolution_time_hrs IS NOT NULL
            """
        )

        values = sorted(
            row["resolution_time_hrs"] for row in stats
        )

        if len(values) < 4:
            return []

        q1 = values[len(values) // 4]
        q3 = values[(3 * len(values)) // 4]
        iqr = q3 - q1
        threshold = q3 + 1.5 * iqr

        rows = database.execute_query(
            """
            SELECT ticket_id, priority, resolution_time_hrs
            FROM tickets
            WHERE resolution_time_hrs > :threshold
            """,
            {"threshold": threshold},
        )

        anomalies = []
        for row in rows:
            anomalies.append(
                Anomaly(
                    ticket_id=row["ticket_id"],
                    reason=(
                        f"Abnormally long resolution time "
                        f"({row['resolution_time_hrs']:.1f} hrs, "
                        f"threshold {threshold:.1f} hrs)"
                    ),
                    severity="high",
                    details={
                        "resolution_time_hrs": row["resolution_time_hrs"],
                        "threshold": round(threshold, 2),
                        "priority": row["priority"],
                    },
                )
            )

        return anomalies

    def detect_long_response(self) -> list[Anomaly]:
        stats = database.execute_query(
            """
            SELECT response_time_hrs
            FROM tickets
            WHERE response_time_hrs IS NOT NULL
            """
        )

        values = sorted(
            row["response_time_hrs"] for row in stats
        )

        if len(values) < 4:
            return []

        q1 = values[len(values) // 4]
        q3 = values[(3 * len(values)) // 4]
        iqr = q3 - q1
        threshold = q3 + 1.5 * iqr

        rows = database.execute_query(
            """
            SELECT ticket_id, response_time_hrs
            FROM tickets
            WHERE response_time_hrs > :threshold
            """,
            {"threshold": threshold},
        )

        anomalies = []
        for row in rows:
            anomalies.append(
                Anomaly(
                    ticket_id=row["ticket_id"],
                    reason=(
                        f"Abnormally long response time "
                        f"({row['response_time_hrs']:.1f} hrs)"
                    ),
                    severity="medium",
                    details={
                        "response_time_hrs": row["response_time_hrs"],
                        "threshold": round(threshold, 2),
                    },
                )
            )

        return anomalies

    def detect_low_rating(self) -> list[Anomaly]:
        average_resolution_time = database.execute_scalar(
            """
            SELECT AVG(resolution_time_hrs)
            FROM tickets
            WHERE resolution_time_hrs IS NOT NULL
            """
        )

        if average_resolution_time is None:
            return []

        average_resolution_time = float(average_resolution_time)

        rows = database.execute_query(
            """
            SELECT ticket_id, customer_rating, resolution_time_hrs
            FROM tickets
            WHERE customer_rating IS NOT NULL
              AND customer_rating < 2
              AND resolution_time_hrs > :average
            """,
            {"average": average_resolution_time},
        )

        anomalies = []
        for row in rows:
            anomalies.append(
                Anomaly(
                    ticket_id=row["ticket_id"],
                    reason=(
                        f"Low rating ({row['customer_rating']}) "
                        f"with resolution time above average "
                        f"({row['resolution_time_hrs']:.1f} hrs)"
                    ),
                    severity="high",
                    details={
                        "customer_rating": row["customer_rating"],
                        "resolution_time_hrs": row["resolution_time_hrs"],
                        "average_resolution_time": round(
                            average_resolution_time, 2
                        ),
                    },
                )
            )

        return anomalies

    def detect_escalated_unresolved(self) -> list[Anomaly]:
        rows = database.execute_query(
            """
            SELECT ticket_id, priority, created_at
            FROM tickets
            WHERE status = 'Escalated'
              AND resolution_time_hrs IS NULL
            """
        )

        anomalies = []
        for row in rows:
            anomalies.append(
                Anomaly(
                    ticket_id=row["ticket_id"],
                    reason="Escalated ticket still unresolved",
                    severity="critical",
                    details={
                        "priority": row["priority"],
                        "created_at": row["created_at"],
                    },
                )
            )

        return anomalies

    def detect_all(self) -> AnomalyResponse:
        logger.info("Running anomaly detection...")

        anomalies: list[Anomaly] = []
        anomalies.extend(self.detect_unresolved_high_priority())
        anomalies.extend(self.detect_long_resolution())
        anomalies.extend(self.detect_long_response())
        anomalies.extend(self.detect_low_rating())
        anomalies.extend(self.detect_escalated_unresolved())

        by_severity: dict[str, int] = {}
        for anomaly in anomalies:
            by_severity[anomaly.severity] = (
                by_severity.get(anomaly.severity, 0) + 1
            )

        logger.info(
            "Detected %d anomalies across %d tickets.",
            len(anomalies),
            len({a.ticket_id for a in anomalies}),
        )

        return AnomalyResponse(
            total_anomalies=len(anomalies),
            by_severity=by_severity,
            anomalies=anomalies,
        )


anomaly_service = AnomalyService()