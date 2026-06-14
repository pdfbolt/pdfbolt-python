from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .types import AsyncConversionWebhookStatus, ConversionErrorCode, SyncConversionStatus


@dataclass(frozen=True)
class RateLimitWindow:
    limit: int | float | None
    remaining: int | float | None


@dataclass(frozen=True)
class RateLimitInfo:
    minute: RateLimitWindow
    hour: RateLimitWindow
    day: RateLimitWindow


@dataclass(frozen=True)
class SyncConversionResult:
    request_id: str
    status: SyncConversionStatus
    error_code: ConversionErrorCode | None
    error_message: str | None
    document_url: str | None
    expires_at: str | None
    is_async: Literal[False]
    duration: int | float | None
    document_size_mb: int | float | None
    is_custom_s3_bucket: bool | None
    conversion_cost: int | float | None
    rate_limit: RateLimitInfo


@dataclass(frozen=True)
class AsyncConversionJob:
    request_id: str
    rate_limit: RateLimitInfo


@dataclass(frozen=True)
class AsyncConversionWebhookEvent:
    request_id: str
    status: AsyncConversionWebhookStatus
    error_code: ConversionErrorCode | None
    error_message: str | None
    document_url: str | None
    expires_at: str | None
    is_async: Literal[True]
    duration: int | float | None
    document_size_mb: int | float | None
    is_custom_s3_bucket: bool | None


@dataclass(frozen=True)
class RecurringCredits:
    total: int | float
    left: int | float
    expires: str
    overage: int | float


@dataclass(frozen=True)
class OneTimeCredits:
    total: int | float
    left: int | float
    expires: str


@dataclass(frozen=True)
class UsageSummary:
    plan: str
    recurring: list[RecurringCredits]
    one_time: list[OneTimeCredits]
    rate_limit: RateLimitInfo


def sync_conversion_result_from_api(
    data: dict[str, Any],
    *,
    conversion_cost: int | float | None,
    rate_limit: RateLimitInfo,
) -> SyncConversionResult:
    return SyncConversionResult(
        request_id=_required_str_field(data, "requestId", "sync conversion"),
        status=_required_sync_status_field(data, "status", "sync conversion"),
        error_code=_required_nullable_str_field(data, "errorCode", "sync conversion"),
        error_message=_required_nullable_str_field(data, "errorMessage", "sync conversion"),
        document_url=_required_nullable_str_field(data, "documentUrl", "sync conversion"),
        expires_at=_required_nullable_str_field(data, "expiresAt", "sync conversion"),
        is_async=_required_false_field(data, "isAsync", "sync conversion"),
        duration=_required_nullable_number_field(data, "duration", "sync conversion"),
        document_size_mb=_required_nullable_number_field(data, "documentSizeMb", "sync conversion"),
        is_custom_s3_bucket=_required_nullable_bool_field(
            data, "isCustomS3Bucket", "sync conversion"
        ),
        conversion_cost=conversion_cost,
        rate_limit=rate_limit,
    )


def async_conversion_job_from_api(
    data: dict[str, Any],
    *,
    rate_limit: RateLimitInfo,
) -> AsyncConversionJob:
    return AsyncConversionJob(
        request_id=_required_str_field(data, "requestId", "async conversion job"),
        rate_limit=rate_limit,
    )


def webhook_event_from_api(data: dict[str, Any]) -> AsyncConversionWebhookEvent:
    return AsyncConversionWebhookEvent(
        request_id=_required_str_field(data, "requestId", "webhook payload"),
        status=_required_webhook_status_field(data, "status", "webhook payload"),
        error_code=_required_nullable_str_field(data, "errorCode", "webhook payload"),
        error_message=_required_nullable_str_field(data, "errorMessage", "webhook payload"),
        document_url=_required_nullable_str_field(data, "documentUrl", "webhook payload"),
        expires_at=_required_nullable_str_field(data, "expiresAt", "webhook payload"),
        is_async=_required_true_field(data, "isAsync", "webhook payload"),
        duration=_required_nullable_number_field(data, "duration", "webhook payload"),
        document_size_mb=_required_nullable_number_field(data, "documentSizeMb", "webhook payload"),
        is_custom_s3_bucket=_required_nullable_bool_field(
            data, "isCustomS3Bucket", "webhook payload"
        ),
    )


def usage_summary_from_api(data: dict[str, Any], *, rate_limit: RateLimitInfo) -> UsageSummary:
    recurring = [
        RecurringCredits(
            total=_required_number(item.get("total"), f"recurring[{index}].total"),
            left=_required_number(item.get("left"), f"recurring[{index}].left"),
            expires=_required_str(item.get("expires"), f"recurring[{index}].expires"),
            overage=_required_number(item.get("overage"), f"recurring[{index}].overage"),
        )
        for index, item in enumerate(_required_list_of_objects(data, "recurring"))
    ]
    one_time = [
        OneTimeCredits(
            total=_required_number(item.get("total"), f"oneTime[{index}].total"),
            left=_required_number(item.get("left"), f"oneTime[{index}].left"),
            expires=_required_str(item.get("expires"), f"oneTime[{index}].expires"),
        )
        for index, item in enumerate(_required_list_of_objects(data, "oneTime"))
    ]

    return UsageSummary(
        plan=_required_str_field(data, "plan", "usage"),
        recurring=recurring,
        one_time=one_time,
        rate_limit=rate_limit,
    )


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _optional_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _optional_number(value: Any) -> int | float | None:
    return value if isinstance(value, int | float) and not isinstance(value, bool) else None


def _required_list_of_objects(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = _required_field(data, key, "usage")
    if not isinstance(value, list):
        raise ValueError(f"Malformed PDFBolt usage response: {key} must be a list.")

    result: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(
                f"Malformed PDFBolt usage response: {key}[{index}] must be an object."
            )
        result.append(item)

    return result


def _required_number(value: Any, path: str) -> int | float:
    number = _optional_number(value)
    if number is None:
        raise ValueError(f"Malformed PDFBolt usage response: {path} must be a number.")

    return number


def _required_str(value: Any, path: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Malformed PDFBolt usage response: {path} must be a string.")

    return value


def _required_str_field(data: dict[str, Any], key: str, context: str) -> str:
    value = _required_field(data, key, context)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Malformed PDFBolt {context} response: {key} must be a string.")

    return value


def _required_bool_field(data: dict[str, Any], key: str, context: str) -> bool:
    value = _required_field(data, key, context)
    if not isinstance(value, bool):
        raise ValueError(f"Malformed PDFBolt {context} response: {key} must be a boolean.")

    return value


def _required_false_field(data: dict[str, Any], key: str, context: str) -> Literal[False]:
    value = _required_bool_field(data, key, context)
    if value is not False:
        raise ValueError(f"Malformed PDFBolt {context} response: {key} must be false.")

    return False


def _required_true_field(data: dict[str, Any], key: str, context: str) -> Literal[True]:
    value = _required_bool_field(data, key, context)
    if value is not True:
        raise ValueError(f"Malformed PDFBolt {context} response: {key} must be true.")

    return True


def _required_sync_status_field(
    data: dict[str, Any],
    key: str,
    context: str,
) -> SyncConversionStatus:
    value = _required_str_field(data, key, context)
    if value != "SUCCESS":
        raise ValueError(f"Malformed PDFBolt {context} response: {key} must be SUCCESS.")

    return "SUCCESS"


def _required_webhook_status_field(
    data: dict[str, Any],
    key: str,
    context: str,
) -> AsyncConversionWebhookStatus:
    value = _required_str_field(data, key, context)
    if value == "SUCCESS":
        return "SUCCESS"
    if value == "FAILURE":
        return "FAILURE"

    raise ValueError(f"Malformed PDFBolt {context} response: {key} must be SUCCESS or FAILURE.")


def _required_nullable_str_field(
    data: dict[str, Any],
    key: str,
    context: str,
) -> str | None:
    value = _required_field(data, key, context)
    if value is None or isinstance(value, str):
        return value

    raise ValueError(f"Malformed PDFBolt {context} response: {key} must be a string or null.")


def _required_nullable_bool_field(
    data: dict[str, Any],
    key: str,
    context: str,
) -> bool | None:
    value = _required_field(data, key, context)
    if value is None or isinstance(value, bool):
        return value

    raise ValueError(f"Malformed PDFBolt {context} response: {key} must be a boolean or null.")


def _required_nullable_number_field(
    data: dict[str, Any],
    key: str,
    context: str,
) -> int | float | None:
    value = _required_field(data, key, context)
    if value is None:
        return None

    number = _optional_number(value)
    if number is None:
        raise ValueError(f"Malformed PDFBolt {context} response: {key} must be a number or null.")

    return number


def _required_field(data: dict[str, Any], key: str, context: str) -> Any:
    if key not in data:
        raise ValueError(f"Malformed PDFBolt {context} response: {key} is missing.")

    return data[key]
