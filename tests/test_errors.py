from __future__ import annotations

import pytest

from _models import AppSettings
from envguard import EnvGuardError, MissingEnvError


def test_missing_error_is_envguard_error() -> None:
    with pytest.raises(MissingEnvError) as info:
        AppSettings()

    assert isinstance(info.value, EnvGuardError)


def test_missing_error_lists_keys_and_hint() -> None:
    with pytest.raises(MissingEnvError) as info:
        AppSettings()

    message = str(info.value)
    assert "- API_SECRET" in message
    assert "Missing 1 required setting" in message
    assert "envguard example --model _models:AppSettings" in message


def test_invalid_and_missing_are_separated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_SECRET", "x")
    monkeypatch.setenv("PORT", "nope")

    with pytest.raises(MissingEnvError) as info:
        AppSettings()

    assert "PORT" in info.value.invalid
    assert info.value.missing == {}
