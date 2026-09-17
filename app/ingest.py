import logging

import pandas as pd
from sqlalchemy import Float, Text, create_engine, text

from app.config import settings


logger = logging.getLogger(__name__)


def load_data():
    if not settings.csv_full_path.exists():
        raise FileNotFoundError(f"CSV file not found: {settings.csv_full_path}")

    settings.db_full_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        df = pd.read_csv(settings.csv_full_path)

        df.columns = df.columns.str.strip()

        for column in df.select_dtypes(include=["object", "str"]).columns:
            df[column] = df[column].str.strip()

        numeric_columns = [
            "response_time_hrs",
            "resolution_time_hrs",
            "customer_rating",
        ]

        for column in numeric_columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

        if df["created_at"].isna().any():
            raise ValueError("Invalid created_at values found in the CSV.")

        if df["ticket_id"].isna().any():
            raise ValueError("Missing ticket_id values found in the CSV.")

        if df["ticket_id"].duplicated().any():
            raise ValueError("Duplicate ticket_id values found in the CSV.")

        engine = create_engine(f"sqlite:///{settings.db_full_path}")

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS tickets (
                        ticket_id TEXT PRIMARY KEY,
                        created_at TEXT,
                        category TEXT,
                        priority TEXT,
                        status TEXT,
                        response_time_hrs REAL,
                        resolution_time_hrs REAL,
                        agent_id TEXT,
                        customer_rating REAL,
                        issue_summary TEXT
                    )
                    """
                )
            )

            connection.execute(text("DELETE FROM tickets"))

        df.to_sql(
            "tickets",
            engine,
            if_exists="append",
            index=False,
            dtype={
                "ticket_id": Text,
                "created_at": Text,
                "category": Text,
                "priority": Text,
                "status": Text,
                "response_time_hrs": Float,
                "resolution_time_hrs": Float,
                "agent_id": Text,
                "customer_rating": Float,
                "issue_summary": Text,
            },
        )

        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_tickets_status "
                    "ON tickets(status)"
                )
            )
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_tickets_priority "
                    "ON tickets(priority)"
                )
            )
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_tickets_agent "
                    "ON tickets(agent_id)"
                )
            )
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_tickets_created_at "
                    "ON tickets(created_at)"
                )
            )

        logger.info("Loaded %s tickets into the database.", len(df))
        logger.info("Database created at %s", settings.db_full_path)

    except Exception:
        logger.exception("Failed to load ticket data.")
        raise


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    load_data()