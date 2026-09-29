from functools import lru_cache
import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field


load_dotenv()


class Settings(BaseModel):
    app_name: str = Field(
        default_factory=lambda: os.getenv(
            "APP_NAME",
            "LegalEase"
        )
    )

    gemini_api_key: str = Field(
        default_factory=lambda: os.getenv(
            "GEMINI_API_KEY",
            ""
        )
    )

    gemini_model: str = Field(
        default_factory=lambda: os.getenv(
            "GEMINI_MODEL",
            "gemini-1.5-pro"
        )
    )

    backend_url: str = Field(
        default_factory=lambda: os.getenv(
            "BACKEND_URL",
            "http://127.0.0.1:8000"
        )
    )

    max_generation_chars: int = Field(
        default_factory=lambda: int(
            os.getenv(
                "MAX_GENERATION_CHARS",
                "30000"
            )
        )
    )

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS",
                "http://localhost:8501,http://127.0.0.1:8501"
            ).split(",")
            if origin.strip()
        ]
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()