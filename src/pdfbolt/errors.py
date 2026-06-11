from __future__ import annotations

from collections.abc import Mapping

from .models import RateLimitInfo
from .rate_limit import read_rate_limit_info


class PDFBoltError(Exception):
    """Base class for all PDFBolt SDK errors."""


class PDFBoltAPIError(PDFBoltError):
    """Raised when the PDFBolt API returns an HTTP error response."""

    def __init__(
        self,
        *,
        message: str,
        status_code: int,
        timestamp: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        headers: Mapping[str, str] | None = None,
        raw_body: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.timestamp = timestamp
        self.error_code = error_code
        self.error_message = error_message
        self.rate_limit: RateLimitInfo = read_rate_limit_info(headers)
        self.headers = headers
        self.raw_body = raw_body


class PDFBoltNetworkError(PDFBoltError):
    """Raised when the SDK did not receive a usable HTTP response."""


class PDFBoltWebhookSignatureError(PDFBoltError):
    """Raised when webhook signature verification fails."""


class PDFBoltValidationError(PDFBoltError):
    """Raised before a request is sent when high-level helper parameters are invalid."""


class PDFBoltConfigurationError(PDFBoltError):
    """Raised when the SDK client is missing required configuration."""
