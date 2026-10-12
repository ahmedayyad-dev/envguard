"""Environment profile resolution and ``.env`` file discovery."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

__all__ = [
    "DEFAULT_PROFILE",
    "PROFILE_ENV_VARS",
    "get_env_files",
    "get_profile",
]

#: Profile used when none is configured.
DEFAULT_PROFILE: Final = "dev"

#: Environment variables consulted (in order) to select a profile.
PROFILE_ENV_VARS: Final = ("ENVGUARD_PROFILE", "ENV_PROFILE")


def get_profile(explicit: str | None = None) -> str:
    """Resolve the active profile.

    Priority: *explicit* argument, then :data:`PROFILE_ENV_VARS`, then
    :data:`DEFAULT_PROFILE`.
    """

    if explicit:
        return explicit.strip()
    for var in PROFILE_ENV_VARS:
        value = os.getenv(var)
        if value and value.strip():
            return value.strip()
    return DEFAULT_PROFILE


def get_env_files(
    profile: str | None = None,
    base_dir: str | Path | None = None,
) -> tuple[Path, ...]:
    """Return the existing ``.env`` files to load for *profile*, in order.

    Files are loaded from lowest to highest precedence: ``.env``,
    ``.env.<profile>`` and ``.env.<profile>.local``. Missing files are omitted.
    """

    resolved_profile = get_profile(profile)
    base = Path(base_dir) if base_dir is not None else Path.cwd()
    candidates = (
        base / ".env",
        base / f".env.{resolved_profile}",
        base / f".env.{resolved_profile}.local",
    )
    return tuple(path for path in candidates if path.is_file())
