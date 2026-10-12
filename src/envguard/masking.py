"""Secret detection and log masking utilities."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

from pydantic import SecretStr
from pydantic.fields import FieldInfo

__all__ = [
    "MASK",
    "SECRET_NAME_HINTS",
    "SecretMaskingFilter",
    "clear_registered_secrets",
    "install_logging_filter",
    "is_secret_field",
    "mask",
    "redact",
    "register_secrets",
]

#: Sentinel used when a secret value is masked.
MASK = "********"
#: Text that replaces a registered secret inside log records.
REDACTED = "***"

#: Substrings (case-insensitive) that mark a field name as sensitive.
SECRET_NAME_HINTS: tuple[str, ...] = (
    "secret",
    "password",
    "passwd",
    "pwd",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "access_key",
    "dsn",
    "credential",
    "auth",
)

_registered_secrets: set[str] = set()


def _annotation_is_secret(annotation: Any) -> bool:
    if annotation is SecretStr:
        return True
    return any(_annotation_is_secret(arg) for arg in getattr(annotation, "__args__", ()))


def is_secret_field(name: str, field: FieldInfo | None = None) -> bool:
    """Return ``True`` if *name*/*field* should be treated as a secret.

    Detection is automatic via the field type (``SecretStr``), an explicit
    ``json_schema_extra={"secret": True}`` marker, or a substring of the field
    name matching :data:`SECRET_NAME_HINTS`.
    """

    if field is not None:
        extra = field.json_schema_extra
        if isinstance(extra, dict) and extra.get("secret"):
            return True
        if field.annotation is not None and _annotation_is_secret(field.annotation):
            return True
    lowered = name.lower()
    return any(hint in lowered for hint in SECRET_NAME_HINTS)


def _to_text(value: Any) -> str:
    if isinstance(value, SecretStr):
        return value.get_secret_value()
    return str(value)


def mask(value: Any, *, reveal: int = 0, mask: str = MASK) -> str:
    """Return a masked representation of *value*.

    When ``reveal`` is greater than zero the last ``reveal`` characters are kept
    visible (useful for debugging key prefixes/suffixes).
    """

    if value is None:
        return mask
    text = _to_text(value)
    if reveal > 0 and len(text) > reveal:
        return f"{mask}{text[-reveal:]}"
    return mask


def register_secrets(values: Iterable[Any]) -> None:
    """Register secret values so they can be redacted from logs."""

    for value in values:
        if value is None:
            continue
        if isinstance(value, (list, tuple, set, frozenset)):
            register_secrets(value)
            continue
        text = _to_text(value)
        if text:
            _registered_secrets.add(text)


def clear_registered_secrets() -> None:
    """Forget all previously registered secrets (mostly useful in tests)."""

    _registered_secrets.clear()


def redact(text: str) -> str:
    """Replace every registered secret found in *text* with ``***``."""

    for secret in sorted(_registered_secrets, key=len, reverse=True):
        if secret and secret in text:
            text = text.replace(secret, REDACTED)
    return text


class SecretMaskingFilter(logging.Filter):
    """Logging filter that redacts registered secrets from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        redacted = redact(message)
        if redacted != message:
            record.msg = redacted
            record.args = ()
        return True


def install_logging_filter(logger: logging.Logger | None = None) -> SecretMaskingFilter:
    """Attach a :class:`SecretMaskingFilter` to *logger* (default: root)."""

    target = logger or logging.getLogger()
    for existing in target.filters:
        if isinstance(existing, SecretMaskingFilter):
            return existing
    secret_filter = SecretMaskingFilter()
    target.addFilter(secret_filter)
    return secret_filter
