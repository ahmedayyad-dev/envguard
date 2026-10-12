"""Exceptions with actionable messages for missing/invalid settings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic import BaseModel, ValidationError

__all__ = ["EnvGuardError", "MissingEnvError"]


class EnvGuardError(Exception):
    """Base class for every error raised by envguard."""


class MissingEnvError(EnvGuardError):
    """Raised when required settings are missing or fail validation.

    Attributes:
        missing: mapping of environment variable name to the validation message
            for required values that were not provided.
        invalid: mapping of environment variable name to the validation message
            for values that were provided but failed type/format validation.
    """

    def __init__(
        self,
        message: str,
        *,
        missing: dict[str, str] | None = None,
        invalid: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.missing: dict[str, str] = missing or {}
        self.invalid: dict[str, str] = invalid or {}

    @classmethod
    def from_validation_error(
        cls,
        settings_cls: type[BaseModel],
        exc: ValidationError,
    ) -> MissingEnvError:
        """Build a friendly :class:`MissingEnvError` from a pydantic error."""

        from envguard.profiles import get_profile
        from envguard.settings import env_var_name, model_path

        missing: dict[str, str] = {}
        invalid: dict[str, str] = {}

        for error in exc.errors():
            loc = tuple(error.get("loc", ()))
            field_name = "_".join(str(part) for part in loc) if loc else "?"
            key = env_var_name(settings_cls, field_name)
            message: Any = error.get("msg", "invalid value")
            if error.get("type") == "missing":
                missing[key] = str(message)
            else:
                invalid[key] = str(message)

        profile = get_profile()
        lines = [f"Cannot load {settings_cls.__name__} (profile '{profile}'):"]

        if missing:
            lines.append("")
            lines.append(f"  Missing {len(missing)} required setting(s):")
            lines.extend(f"    - {key}: {msg}" for key, msg in missing.items())

        if invalid:
            lines.append("")
            lines.append(f"  Invalid {len(invalid)} setting(s):")
            lines.extend(f"    - {key}: {msg}" for key, msg in invalid.items())

        lines.append("")
        lines.append("  Set these in your .env file or as environment variables.")
        lines.append(
            f"  Tip: run `envguard example --model {model_path(settings_cls)}` "
            "to generate a .env.example."
        )

        return cls("\n".join(lines), missing=missing, invalid=invalid)
