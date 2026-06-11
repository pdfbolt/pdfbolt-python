from __future__ import annotations

import base64
from collections.abc import Mapping
from typing import Any

from .errors import PDFBoltValidationError

RAW_NESTED_KEYS = {
    "additionalWebhookHeaders",
    "additional_webhook_headers",
    "extraHTTPHeaders",
    "extra_http_headers",
    "templateData",
    "template_data",
}

API_KEY_OVERRIDES = {
    "apply_extra_http_headers_to_all_resources": "applyExtraHTTPHeadersToAllResources",
    "extra_http_headers": "extraHTTPHeaders",
}


def encode_base64(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def encode_header_footer_templates(params: dict[str, Any]) -> dict[str, Any]:
    encoded = dict(params)
    for key in ("header_template", "headerTemplate", "footer_template", "footerTemplate"):
        value = encoded.get(key)
        if isinstance(value, str):
            encoded[key] = encode_base64(value)
    return encoded


def split_request_options(params: Mapping[str, Any]) -> tuple[dict[str, Any], float | None]:
    body: dict[str, Any] = {}
    request_timeout = None

    for key, value in params.items():
        if key == "request_timeout":
            request_timeout = _optional_timeout(value)
        else:
            body[key] = value

    return body, request_timeout


def to_api_body(params: Mapping[str, Any]) -> dict[str, Any]:
    return {_to_api_key(key): _to_api_value(value, key=key) for key, value in params.items()}


def require_string_field(params: Mapping[str, Any], field_name: str, method_name: str) -> str:
    value = params.get(field_name)
    if not isinstance(value, str):
        raise PDFBoltValidationError(f"{field_name} is required when using {method_name}().")
    return value


def require_object_field(
    params: Mapping[str, Any],
    field_name: str,
    method_name: str,
) -> Mapping[str, Any]:
    value = params.get(field_name)
    if not isinstance(value, Mapping):
        raise PDFBoltValidationError(f"{field_name} must be an object when using {method_name}().")
    return value


def merge_params(required: Mapping[str, Any], optional: Mapping[str, Any]) -> dict[str, Any]:
    return {**required, **optional}


def _to_api_value(value: Any, *, key: str) -> Any:
    if key in RAW_NESTED_KEYS:
        return value

    if isinstance(value, Mapping):
        return to_api_body(value)

    if isinstance(value, list):
        return [_to_api_value(item, key="") for item in value]

    return value


def _to_api_key(key: str) -> str:
    if key in API_KEY_OVERRIDES:
        return API_KEY_OVERRIDES[key]

    if "_" not in key:
        return key

    parts = key.split("_")
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def _optional_timeout(value: Any) -> float | None:
    if value is None:
        return None

    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)

    raise PDFBoltValidationError("request_timeout must be a number of seconds.")
