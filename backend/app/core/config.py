from typing import Any, List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Plataforma Web de Encuestas y PDUL - Alcaldía de Maturín"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/pdul_db",
        description="Async SQLAlchemy database connection URL",
    )
    SQLITE_FALLBACK_URL: str = Field(
        default="sqlite+aiosqlite:///pdul_dev.db",
        description="Fallback SQLite database URL for local development",
    )
    CORS_ORIGINS: Union[List[str], str] = ["*"]

    # Path to default canonical PDUL Form.io survey schema
    DEFAULT_PDUL_SCHEMA_PATH: str = "shared/schemas/pdul_origen_destino.json"

    # Identificadores canónicos centralizados del instrumento PDUL
    CANONICAL_SURVEY_ID: str = "00000000-0000-0000-0000-000000000001"
    CANONICAL_SURVEY_SLUG: str = "cuestionario-od-maturin"
    LEGACY_SURVEY_SLUG: str = "pdul_origen_destino"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, v: Union[str, Any]) -> str:
        if isinstance(v, str):
            val = v.strip()
            if val.startswith("postgres://"):
                val = val.replace("postgres://", "postgresql+asyncpg://", 1)
            elif val.startswith("postgresql://") and not val.startswith("postgresql+asyncpg://"):
                val = val.replace("postgresql://", "postgresql+asyncpg://", 1)
            if "sslmode=" in val:
                val = (
                    val.replace("sslmode=require", "ssl=require")
                    .replace("sslmode=prefer", "")
                    .replace("sslmode=disable", "")
                )
                if val.endswith("?") or val.endswith("&"):
                    val = val[:-1]
            return val
        return str(v)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v  # type: ignore[return-value]
        return ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
