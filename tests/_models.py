from __future__ import annotations

from pydantic import BaseModel, Field, SecretStr

from envguard import EnvGuardBaseSettings


class AppSettings(EnvGuardBaseSettings):
    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    api_secret: SecretStr = Field(description="API signing secret")


class _Database(BaseModel):
    password: SecretStr


class NestedSettings(EnvGuardBaseSettings):
    db: _Database


class PlainSecretSettings(EnvGuardBaseSettings):
    password: str


class CliSettings(EnvGuardBaseSettings):
    database_url: str = Field(description="Database URL")
    api_secret: SecretStr = Field(description="API secret")
    debug: bool = Field(default=False, description="Debug mode")
