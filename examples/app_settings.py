"""Example settings model showing how to use envguard.

Run ``envguard example --model app_settings:Settings --output .env.example``
from this directory to regenerate the accompanying ``.env.example``.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, SecretStr

from envguard import EnvGuardBaseSettings


class Settings(EnvGuardBaseSettings):
    """Application settings loaded from the environment and profile files."""

    environment: Literal["dev", "staging", "prod"] = Field(
        default="dev",
        description="Deployment environment",
    )
    database_url: str = Field(description="PostgreSQL connection string")
    redis_url: str | None = Field(
        default=None,
        description="Optional Redis connection string",
    )
    api_secret: SecretStr = Field(description="Secret used to sign API tokens")
    debug: bool = Field(default=False, description="Enable verbose debug logging")
    workers: int = Field(default=4, description="Number of worker processes")


if __name__ == "__main__":  # pragma: no cover
    settings = Settings()
    print(settings)
