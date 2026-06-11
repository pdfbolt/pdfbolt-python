from collections.abc import Mapping

from .models import RateLimitInfo, RateLimitWindow


def read_rate_limit_info(headers: Mapping[str, str] | None) -> RateLimitInfo:
    return RateLimitInfo(
        minute=RateLimitWindow(
            limit=read_number_header(headers, "x-pdfbolt-limit-minute"),
            remaining=read_number_header(headers, "x-pdfbolt-remaining-minute"),
        ),
        hour=RateLimitWindow(
            limit=read_number_header(headers, "x-pdfbolt-limit-hour"),
            remaining=read_number_header(headers, "x-pdfbolt-remaining-hour"),
        ),
        day=RateLimitWindow(
            limit=read_number_header(headers, "x-pdfbolt-limit-day"),
            remaining=read_number_header(headers, "x-pdfbolt-remaining-day"),
        ),
    )


def read_number_header(headers: Mapping[str, str] | None, name: str) -> int | float | None:
    value = read_header(headers, name)
    if value is None or value == "":
        return None

    try:
        number = float(value)
    except ValueError:
        return None

    return int(number) if number.is_integer() else number


def read_header(headers: Mapping[str, str] | None, name: str) -> str | None:
    if headers is None:
        return None

    lowered = name.lower()
    for key, value in headers.items():
        if key.lower() == lowered:
            return value

    return None
