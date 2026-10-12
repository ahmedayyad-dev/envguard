"""The :class:`EnvGuardBaseSettings` base class."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ValidationError
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from envguard.errors import MissingEnvError
from envguard.masking import is_secret_field, mask, register_secrets
from envguard.profiles import get_env_files, get_profile

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo

__all__ = ["EnvGuardBaseSettings", "env_var_name", "model_path"]


def env_var_name(settings_cls: type[BaseModel], field_name: str) -> str:
    """Return the environment variable name for *field_name* on *settings_cls*."""

    prefix = settings_cls.model_config.get("env_prefix", "") or ""
    return f"{prefix}{field_name}".upper()


def model_path(settings_cls: type[BaseModel]) -> str:
    """Return the importable ``module:QualName`` path for *settings_cls*."""

    return f"{settings_cls.__module__}:{settings_cls.__qualname__}"


class EnvGuardBaseSettings(BaseSettings):
    """``pydantic-settings`` base class with profiles and log masking.

    Subclass it and declare typed fields::

        from pydantic import SecretStr
        from envguard import EnvGuardBaseSettings

        class Settings(EnvGuardBaseSettings):
            database_url: str
            api_secret: SecretStr
            debug: bool = False

    Values are read from (highest precedence first) explicit keyword arguments,
    environment variables, and the profile-aware ``.env`` files described in
    :func:`envguard.profiles.get_env_files`.
    """

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
        env_file_encoding="utf-8",
    )

    @classmethod
    def env_profile(cls) -> str:
        """Return the active profile for this settings class."""

        return get_profile()

    @classmethod
    def env_files(cls) -> tuple[Path, ...]:
        """Return the ``.env`` files that would be loaded for this class."""

        configured = cls.model_config.get("env_file")
        if configured:
            if isinstance(configured, (str, Path)):
                return (Path(configured),)
            return tuple(Path(item) for item in configured)
        return get_env_files(cls.env_profile())

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        dotenv = DotEnvSettingsSource(
            settings_cls,
            env_file=cls.env_files(),
            env_file_encoding=cls.model_config.get("env_file_encoding", "utf-8"),
            env_nested_delimiter=cls.model_config.get("env_nested_delimiter", "__"),
            case_sensitive=cls.model_config.get("case_sensitive", False),
        )
        return init_settings, env_settings, dotenv, file_secret_settings

    def __init__(self, **values: Any) -> None:
        try:
            super().__init__(**values)
        except ValidationError as exc:
            raise MissingEnvError.from_validation_error(type(self), exc) from exc
        register_secrets(self._secret_values())

    def _secret_values(self) -> Iterable[Any]:
        return _collect_secrets(self, type(self).model_fields)

    def __repr_args__(self) -> Iterable[tuple[str | None, Any]]:
        fields: dict[str, FieldInfo] = type(self).model_fields
        for name, value in super().__repr_args__():
            if name is not None and is_secret_field(name, fields.get(name)):
                yield name, mask(value)
            else:
                yield name, value


def _collect_secrets(
    model: BaseModel,
    fields: Mapping[str, FieldInfo],
) -> Iterator[Any]:
    for name, field in fields.items():
        value = getattr(model, name, None)
        if is_secret_field(name, field):
            yield value
        elif isinstance(value, BaseModel):
            yield from _collect_secrets(value, type(value).model_fields)
