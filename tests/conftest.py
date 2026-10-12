from __future__ import annotations

import sys
from pathlib import Path

import pytest

from envguard.masking import clear_registered_secrets

sys.path.insert(0, str(Path(__file__).parent))

_PROFILE_VARS = ("ENVGUARD_PROFILE", "ENV_PROFILE")


@pytest.fixture(autouse=True)
def _isolated_state(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Run every test in a clean temp directory with no leftover secrets."""

    clear_registered_secrets()
    monkeypatch.chdir(tmp_path)
    for var in _PROFILE_VARS:
        monkeypatch.delenv(var, raising=False)
    yield
    clear_registered_secrets()
