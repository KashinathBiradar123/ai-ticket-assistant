from pathlib import Path

from sqlalchemy import create_engine, text

from app.config import settings


class Database:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or settings.db_full_path
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            pool_pre_ping=True,
        )

    def execute_query(
        self,
        query: str,
        params: dict | None = None,
    ):
        with self.engine.connect() as connection:
            result = connection.execute(
                text(query),
                params or {},
            )
            return [dict(row._mapping) for row in result]

    def execute_scalar(
        self,
        query: str,
        params: dict | None = None,
    ):
        with self.engine.connect() as connection:
            result = connection.execute(
                text(query),
                params or {},
            )
            return result.scalar()

    def execute_write(
        self,
        query: str,
        params: dict | None = None,
    ) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text(query),
                params or {},
            )

    def get_ticket_count(self) -> int:
        return self.execute_scalar(
            "SELECT COUNT(*) FROM tickets"
        ) or 0

    def table_exists(self, table_name: str) -> bool:
        query = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = :table_name
        """

        return self.execute_scalar(
            query,
            {"table_name": table_name},
        ) is not None


database = Database()