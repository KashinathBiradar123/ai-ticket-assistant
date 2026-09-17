from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_path: str = "data/tickets.db"
    csv_path: str = "data/support_tickets.csv"

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    llm_provider: str = "groq"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent

    @property
    def db_full_path(self) -> Path:
        path = Path(self.db_path)
        return path if path.is_absolute() else self.base_dir / path

    @property
    def csv_full_path(self) -> Path:
        path = Path(self.csv_path)
        return path if path.is_absolute() else self.base_dir / path


settings = Settings()