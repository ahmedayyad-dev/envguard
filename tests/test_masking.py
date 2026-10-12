from __future__ import annotations

import logging

from pydantic import SecretStr
from pydantic.fields import FieldInfo

from envguard import MASK, is_secret_field, mask, redact, register_secrets
from envguard.masking import SecretMaskingFilter


def test_is_secret_by_name() -> None:
    assert is_secret_field("api_key")
    assert is_secret_field("db_password")
    assert not is_secret_field("host")


def test_is_secret_by_type() -> None:
    field = FieldInfo(annotation=SecretStr)
    assert is_secret_field("value", field)


def test_is_secret_by_marker() -> None:
    field = FieldInfo(annotation=str, json_schema_extra={"secret": True})
    assert is_secret_field("value", field)


def test_mask_full_and_reveal() -> None:
    assert mask("abc") == MASK
    assert mask(SecretStr("abcdef"), reveal=2).endswith("ef")
    assert mask(None) == MASK


def test_redact_replaces_registered_secret() -> None:
    register_secrets(["topsecret"])
    assert redact("value=topsecret") == "value=***"


def test_logging_filter_redacts() -> None:
    register_secrets(["topsecret"])

    logger = logging.getLogger("envguard-tests")
    logger.setLevel(logging.INFO)
    logger.addFilter(SecretMaskingFilter())

    captured: list[str] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured.append(record.getMessage())

    handler = _Capture()
    logger.addHandler(handler)
    try:
        logger.info("token is %s", "topsecret")
    finally:
        logger.removeHandler(handler)

    assert captured == ["token is ***"]
