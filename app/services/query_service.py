import json
import logging
import re

from app.database import database
from app.llm.client import llm_client
from app.llm.prompts import build_answer_prompt, build_sql_prompt
from app.schemas import QueryResponse


logger = logging.getLogger(__name__)


ALLOWED_TABLE = "tickets"

ALLOWED_COLUMNS = {
    "ticket_id",
    "created_at",
    "category",
    "priority",
    "status",
    "response_time_hrs",
    "resolution_time_hrs",
    "agent_id",
    "customer_rating",
    "issue_summary",
}

FORBIDDEN_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "replace",
    "truncate",
    "attach",
    "detach",
    "pragma",
}

SQL_KEYWORDS = {
    "select",
    "from",
    "where",
    "and",
    "or",
    "not",
    "is",
    "null",
    "as",
    "count",
    "avg",
    "min",
    "max",
    "sum",
    "group",
    "by",
    "order",
    "asc",
    "desc",
    "limit",
    "offset",
    "having",
    "distinct",
    "case",
    "when",
    "then",
    "else",
    "end",
    "between",
    "like",
    "in",
    "join",
    "on",
    "inner",
    "left",
    "right",
    "outer",
    "with",
    "current_date",
    "current_time",
    "current_timestamp",
    "date",
    "datetime",
    "strftime",
    "extract",
    "interval",
    "cast",
    "coalesce",
    "ifnull",
    "nullif",
    "if",
    "round",
    "abs",
    "length",
    "lower",
    "upper",
    "trim",
    "substr",
    "replace",
    "union",
    "all",
    "exists",
    "over",
    "partition",
    "row_number",
    "rank",
    "dense_rank",
}

KNOWN_STRING_VALUES = {
    "open",
    "resolved",
    "escalated",
    "low",
    "medium",
    "high",
    "critical",
    "billing",
    "technical",
    "general",
}


class QueryService:
    def parse_llm_json(self, response: str) -> dict:
        response = response.strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        cleaned = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            response,
            flags=re.IGNORECASE,
        ).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", response, re.DOTALL)

        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError("LLM returned invalid JSON.")

    def auto_quote_string_values(self, sql: str) -> str:
        for value in KNOWN_STRING_VALUES:
            sql = re.sub(
                rf"(=|!=|<>|\bin\s*\(|,)\s*({value})\b(?!')",
                rf"\1 '\2'",
                sql,
                flags=re.IGNORECASE,
            )

        return sql

    def validate_sql(self, sql: str) -> str:
        sql = sql.strip()

        if not sql:
            raise ValueError("LLM returned an empty SQL query.")

        if sql.endswith(";"):
            sql = sql[:-1].strip()

        if ";" in sql:
            raise ValueError("Multiple SQL statements are not allowed.")

        if "--" in sql or "/*" in sql or "*/" in sql:
            raise ValueError("SQL comments are not allowed.")

        if not re.match(r"^select\b", sql, re.IGNORECASE):
            raise ValueError("Only SELECT queries are allowed.")

        for keyword in FORBIDDEN_KEYWORDS:
            if re.search(rf"\b{keyword}\b", sql, re.IGNORECASE):
                raise ValueError(
                    f"Forbidden SQL keyword detected: {keyword}"
                )

        tables = re.findall(
            r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            sql,
            re.IGNORECASE,
        )

        if not tables:
            raise ValueError("SQL query must reference the tickets table.")

        if any(table.lower() != ALLOWED_TABLE for table in tables):
            raise ValueError("Only the tickets table can be queried.")

        aliases = set(
            re.findall(
                r"\bas\s+([a-zA-Z_][a-zA-Z0-9_]*)",
                sql,
                re.IGNORECASE,
            )
        )

        sql_no_strings = re.sub(r"'[^']*'", "''", sql)
        sql_no_strings = re.sub(r'"[^"]*"', '""', sql_no_strings)

        identifiers = set(
            re.findall(
                r"\b[a-zA-Z_][a-zA-Z0-9_]*\b",
                sql_no_strings,
            )
        )

        alias_names = {alias.lower() for alias in aliases}

        unknown_identifiers = {
            identifier.lower()
            for identifier in identifiers
            if identifier.lower() not in ALLOWED_COLUMNS
            and identifier.lower() not in SQL_KEYWORDS
            and identifier.lower() not in alias_names
            and identifier.lower() != ALLOWED_TABLE
            and not identifier.isdigit()
        }

        if unknown_identifiers:
            raise ValueError(
                "Unknown SQL identifiers detected: "
                + ", ".join(sorted(unknown_identifiers))
            )

        return sql

    def generate_sql(self, question: str) -> dict:
        logger.info("Generating SQL for question: %s", question)

        system_prompt, user_prompt = build_sql_prompt(question)

        try:
            response = llm_client.generate(
                user_prompt,
                system=system_prompt,
            )
        except Exception as exc:
            logger.exception("SQL generation failed.")
            raise RuntimeError(
                "Failed to generate SQL from the LLM."
            ) from exc

        try:
            parsed = self.parse_llm_json(response)
        except ValueError as exc:
            logger.exception("Failed to parse LLM SQL response.")
            raise ValueError(
                "The LLM returned an invalid SQL response."
            ) from exc

        sql = parsed.get("sql", "")
        intent = parsed.get("intent", "unknown")
        explanation = parsed.get("explanation", "")

        sql = self.auto_quote_string_values(sql)
        sql = self.validate_sql(sql)

        logger.info("SQL generated successfully. Intent: %s", intent)

        return {
            "sql": sql,
            "intent": intent,
            "explanation": explanation,
        }

    def fallback_answer(self, result: list[dict]) -> str:
        if not result:
            return "No matching tickets found."

        if len(result) == 1 and len(result[0]) == 1:
            value = list(result[0].values())[0]
            return f"Result: {value}"

        return f"Found {len(result)} matching rows."

    def answer_question(self, question: str) -> QueryResponse:
        logger.info("Processing question: %s", question)

        query_info = self.generate_sql(question)

        try:
            result = database.execute_query(query_info["sql"])
        except Exception as exc:
            logger.exception("SQL execution failed.")
            raise RuntimeError(
                "Failed to execute the generated SQL query."
            ) from exc

        logger.info(
            "SQL executed successfully. Rows returned: %s",
            len(result),
        )

        system_prompt, answer_prompt = build_answer_prompt(
            question=question,
            sql=query_info["sql"],
            result=result,
        )

        try:
            answer = llm_client.generate(
                answer_prompt,
                system=system_prompt,
            )
            logger.info("Final answer generated successfully.")
        except Exception:
            logger.exception("Answer generation failed.")
            answer = self.fallback_answer(result)

        return QueryResponse(
            question=question,
            answer=answer,
            sql=query_info["sql"],
            rows=len(result),
            data=result[:100],
        )


query_service = QueryService()