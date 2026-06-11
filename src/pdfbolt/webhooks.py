from __future__ import annotations

import hmac
import json
from collections.abc import Sequence
from typing import Any

from .errors import PDFBoltWebhookSignatureError
from .models import AsyncConversionWebhookEvent, webhook_event_from_api

WebhookRawBody = str | bytes | bytearray | memoryview


class Webhooks:
    def verify_signature(
        self,
        *,
        raw_body: WebhookRawBody,
        signature: str | Sequence[str] | None,
        secret: str,
    ) -> bool:
        if not secret:
            return False

        normalized = _normalize_signature(signature)
        if not normalized:
            return False

        expected = _sign_body(raw_body, secret)
        return hmac.compare_digest(normalized.encode("ascii"), expected.encode("ascii"))

    def verify_and_parse(
        self,
        *,
        raw_body: WebhookRawBody,
        signature: str | Sequence[str] | None,
        secret: str,
    ) -> AsyncConversionWebhookEvent:
        if not self.verify_signature(raw_body=raw_body, signature=signature, secret=secret):
            raise PDFBoltWebhookSignatureError("Invalid PDFBolt webhook signature.")

        try:
            parsed: Any = json.loads(_to_bytes(raw_body).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise PDFBoltWebhookSignatureError("Invalid PDFBolt webhook payload.") from error

        if not isinstance(parsed, dict):
            raise PDFBoltWebhookSignatureError("Invalid PDFBolt webhook payload.")

        try:
            return webhook_event_from_api(parsed)
        except ValueError as error:
            raise PDFBoltWebhookSignatureError("Invalid PDFBolt webhook payload.") from error


webhooks = Webhooks()


def _sign_body(raw_body: WebhookRawBody, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), _to_bytes(raw_body), "sha256").hexdigest()
    return f"sha256={digest}"


def _normalize_signature(signature: str | Sequence[str] | None) -> str | None:
    if isinstance(signature, str):
        return _ascii_signature_or_none(signature)

    if isinstance(signature, Sequence):
        first = signature[0] if signature else None
        return _ascii_signature_or_none(first) if isinstance(first, str) else None

    return None


def _ascii_signature_or_none(signature: str) -> str | None:
    try:
        signature.encode("ascii")
    except UnicodeEncodeError:
        return None

    return signature


def _to_bytes(raw_body: WebhookRawBody) -> bytes:
    if isinstance(raw_body, str):
        return raw_body.encode("utf-8")

    if isinstance(raw_body, bytes):
        return raw_body

    return bytes(raw_body)
