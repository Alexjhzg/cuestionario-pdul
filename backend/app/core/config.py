from pathlib import Path
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Plataforma Web de Encuestas y PDUL - Alcaldía de Maturín"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/pdul_db",
        description="Async SQLAlchemy database connection URL",
    )
    CORS_ORIGINS: Union[List[str], str] = ["*"]

    # Path to default canonical PDUL Form.io survey schema
    DEFAULT_PDUL_SCHEMA_PATH: str = "shared/schemas/pdul_origen_destino.json"

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
