from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(
        min_length=3,
        description="Natural language question about support tickets.",
    )


class QueryResponse(BaseModel):
    question: str = Field(
        description="Original user question.",
    )
    answer: str = Field(
        description="Natural language answer generated from the query result.",
    )
    sql: str = Field(
        description="Read-only SQL query executed against the tickets database.",
    )
    rows: int = Field(
        description="Number of rows returned by the query.",
    )
    data: list[dict] = Field(
        default_factory=list,
        description="Query result rows.",
    )


class Anomaly(BaseModel):
    ticket_id: str = Field(
        description="Unique identifier of the anomalous ticket.",
    )
    reason: str = Field(
        description="Reason why the ticket was flagged as an anomaly.",
    )
    severity: str = Field(
        description="Severity level of the anomaly.",
    )
    details: dict = Field(
        default_factory=dict,
        description="Additional information about the anomaly.",
    )


class AnomalyResponse(BaseModel):
    total_anomalies: int = Field(
        description="Total number of detected anomalies.",
    )
    by_severity: dict[str, int] = Field(
        default_factory=dict,
        description="Number of anomalies grouped by severity.",
    )
    anomalies: list[Anomaly] = Field(
        default_factory=list,
        description="List of detected anomalies.",
    )


class HealthResponse(BaseModel):
    status: str = Field(
        description="Current application health status.",
    )
    database: str = Field(
        description="Database connectivity status.",
    )
    tickets_loaded: int = Field(
        description="Number of tickets currently loaded in the database.",
    )
    llm_provider: str = Field(
        description="Configured LLM provider.",
    )
    llm_available: bool = Field(
        description="Whether the configured LLM is currently reachable.",
    )