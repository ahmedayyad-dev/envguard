"""envguard: profile-aware, type-safe settings and secrets management.

Built on top of :mod:`pydantic_settings`. It adds environment profiles
(``dev``/``prod``/...), automatic secret detection and log masking, and clear
error messages for missing or invalid configuration keys.
"""

from __future__ import annotations

from envguard.errors import EnvGuardError, MissingEnvError
from envguard.masking import (
    MASK,
    SECRET_NAME_HINTS,
    SecretMaskingFilter,
    clear_registered_secrets,
    install_logging_filter,
    is_secret_field,
    mask,
    redact,
    register_secrets,
)
from envguard.profiles import DEFAULT_PROFILE, get_env_files, get_profile
from envguard.settings import EnvGuardBaseSettings, env_var_name, model_path

try:
    from importlib.metadata import version as _version

    __version__ = _version("envguard")
except Exception:  # pragma: no cover - source checkout without installed metadata
    __version__ = "0.0.0"

__all__ = [
    "DEFAULT_PROFILE",
    "MASK",
    "SECRET_NAME_HINTS",
    "EnvGuardBaseSettings",
    "EnvGuardError",
    "MissingEnvError",
    "SecretMaskingFilter",
    "__version__",
    "clear_registered_secrets",
    "env_var_name",
    "get_env_files",
    "get_profile",
    "install_logging_filter",
    "is_secret_field",
    "mask",
    "model_path",
    "redact",
    "register_secrets",
]
