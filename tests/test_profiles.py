from __future__ import annotations

import pytest

from _models import AppSettings
from envguard import get_env_files, get_profile


def test_default_profile() -> None:
    assert get_profile() == "dev"


def test_env_var_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVGUARD_PROFILE", "prod")
    assert get_profile() == "prod"


def test_alternate_env_var_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV_PROFILE", "staging")
    assert get_profile() == "staging"


def test_explicit_profile_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVGUARD_PROFILE", "prod")
    assert get_profile("custom") == "custom"


def test_get_env_files_order(tmp_path) -> None:
    (tmp_path / ".env").write_text("")
    (tmp_path / ".env.dev").write_text("")
    (tmp_path / ".env.dev.local").write_text("")

    files = get_env_files("dev", base_dir=tmp_path)

    assert [path.name for path in files] == [".env", ".env.dev", ".env.dev.local"]


def test_missing_files_are_omitted(tmp_path) -> None:
    assert get_env_files("dev", base_dir=tmp_path) == ()


def test_profile_file_overrides_base(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".env").write_text("HOST=base\nAPI_SECRET=a\n")
    (tmp_path / ".env.prod").write_text("HOST=prod-host\n")
    monkeypatch.setenv("ENVGUARD_PROFILE", "prod")

    settings = AppSettings()

    assert settings.host == "prod-host"
    assert settings.api_secret.get_secret_value() == "a"
