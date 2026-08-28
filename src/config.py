import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Blog engine configuration.
    """
    groq_api_key: Optional[str] = None
    host: str = "0.0.0.0"
    port: int = 8000
    default_model: str = "llama-3.3-70b-versatile"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def validate_key(self) -> bool:
        return bool(self.groq_api_key or os.getenv("GROQ_API_KEY"))


settings = Settings()
