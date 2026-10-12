from __future__ import annotations

import pytest

from envguard.cli import main


def test_example_generates_file(tmp_path) -> None:
    output = tmp_path / ".env.example"

    assert main(["example", "--model", "_models:CliSettings", "--output", str(output)]) == 0

    content = output.read_text()
    assert "DATABASE_URL=" in content
    assert "API_SECRET=changeme" in content
    assert "DEBUG" not in content


def test_example_include_optional(tmp_path) -> None:
    output = tmp_path / ".env.example"

    code = main(
        [
            "example",
            "--model",
            "_models:CliSettings",
            "--output",
            str(output),
            "--include-optional",
        ]
    )

    assert code == 0
    assert "DEBUG=false" in output.read_text()


def test_example_refuses_to_overwrite(tmp_path) -> None:
    output = tmp_path / ".env.example"
    output.write_text("existing")

    assert main(["example", "--model", "_models:CliSettings", "--output", str(output)]) == 1
    assert output.read_text() == "existing"


def test_example_force_overwrites(tmp_path) -> None:
    output = tmp_path / ".env.example"
    output.write_text("existing")

    code = main(["example", "--model", "_models:CliSettings", "--output", str(output), "--force"])

    assert code == 0
    assert "DATABASE_URL=" in output.read_text()


def test_check_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgres://localhost/db")
    monkeypatch.setenv("API_SECRET", "x")

    assert main(["check", "--model", "_models:CliSettings"]) == 0


def test_check_missing_returns_one() -> None:
    assert main(["check", "--model", "_models:CliSettings"]) == 1


def test_bad_model_path_returns_one() -> None:
    assert main(["check", "--model", "does.not.exist:Settings"]) == 1
    assert main(["check", "--model", "no-colon"]) == 1


def test_version(capsys) -> None:
    assert main(["--version"]) == 0
    assert "envguard" in capsys.readouterr().out


def test_no_command_prints_help(capsys) -> None:
    assert main([]) == 1
    assert "usage" in capsys.readouterr().out.lower()
