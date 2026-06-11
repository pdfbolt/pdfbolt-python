from __future__ import annotations

from ..errors import PDFBoltNetworkError
from ..http import PDFBoltHttpClient
from ..models import UsageSummary, usage_summary_from_api
from ..rate_limit import read_rate_limit_info


class UsageResource:
    def __init__(self, http: PDFBoltHttpClient) -> None:
        self._http = http

    def get(self, *, request_timeout: float | None = None) -> UsageSummary:
        data, headers = self._http.request_json(
            "GET",
            "/v1/usage",
            request_timeout=request_timeout,
        )
        try:
            return usage_summary_from_api(data, rate_limit=read_rate_limit_info(headers))
        except ValueError as error:
            raise PDFBoltNetworkError("PDFBolt API returned a malformed usage response.") from error
