from __future__ import annotations

import pytest

from _models import AppSettings, NestedSettings, PlainSecretSettings
from envguard import EnvGuardError, MissingEnvError
from envguard.masking import redact


def test_defaults_and_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOST", "example.com")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("API_SECRET", "s3cr3t")

    settings = AppSettings()

    assert settings.host == "example.com"
    assert settings.port == 9000
    assert settings.api_secret.get_secret_value() == "s3cr3t"
    assert redact("s3cr3t") == "***"


def test_reads_dotenv(tmp_path) -> None:
    (tmp_path / ".env").write_text("HOST=from-file\nAPI_SECRET=filesecret\n")

    settings = AppSettings()

    assert settings.host == "from-file"
    assert settings.api_secret.get_secret_value() == "filesecret"


def test_env_overrides_dotenv(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".env").write_text("HOST=from-file\nAPI_SECRET=x\n")
    monkeypatch.setenv("HOST", "from-env")

    assert AppSettings().host == "from-env"


def test_missing_required_raises() -> None:
    with pytest.raises(MissingEnvError) as info:
        AppSettings()

    error = info.value
    assert isinstance(error, EnvGuardError)
    assert "API_SECRET" in error.missing
    assert "API_SECRET" in str(error)
    assert "envguard example" in str(error)


def test_invalid_type_recorded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_SECRET", "x")
    monkeypatch.setenv("PORT", "not-a-number")

    with pytest.raises(MissingEnvError) as info:
        AppSettings()

    assert "PORT" in info.value.invalid


def test_nested_delimiter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB__PASSWORD", "nested-secret")

    settings = NestedSettings()

    assert settings.db.password.get_secret_value() == "nested-secret"
    assert redact("nested-secret") == "***"


def test_repr_masks_plain_str_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PASSWORD", "hunter2")

    settings = PlainSecretSettings()

    assert "hunter2" not in repr(settings)
    assert "hunter2" not in str(settings)
