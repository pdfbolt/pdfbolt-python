from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._utils import (
    encode_base64,
    encode_header_footer_templates,
    merge_params,
    require_object_field,
    require_string_field,
    split_request_options,
    to_api_body,
)
from ..errors import PDFBoltNetworkError
from ..http import PDFBoltHttpClient
from ..models import SyncConversionResult, sync_conversion_result_from_api
from ..rate_limit import read_number_header, read_rate_limit_info


class SyncResource:
    def __init__(self, http: PDFBoltHttpClient) -> None:
        self._http = http

    def convert(self, params: Mapping[str, Any]) -> SyncConversionResult:
        body, request_timeout = split_request_options(params)
        data, headers = self._http.request_json(
            "POST",
            "/v1/sync",
            body=to_api_body(body),
            request_timeout=request_timeout,
        )
        try:
            return sync_conversion_result_from_api(
                data,
                conversion_cost=read_number_header(headers, "x-pdfbolt-conversion-cost"),
                rate_limit=read_rate_limit_info(headers),
            )
        except ValueError as error:
            raise PDFBoltNetworkError(
                "PDFBolt API returned a malformed sync conversion response."
            ) from error

    def from_url(self, *, url: str, **params: Any) -> SyncConversionResult:
        body = merge_params({"url": url}, params)
        require_string_field(body, "url", "sync.from_url")
        return self.convert(encode_header_footer_templates(body))

    def from_html(self, *, html: str, **params: Any) -> SyncConversionResult:
        body = merge_params({"html": html}, params)
        html_value = require_string_field(body, "html", "sync.from_html")
        return self.convert(
            encode_header_footer_templates(
                {
                    **body,
                    "html": encode_base64(html_value),
                }
            )
        )

    def from_template(
        self,
        *,
        template_id: str,
        template_data: Mapping[str, Any],
        **params: Any,
    ) -> SyncConversionResult:
        body = merge_params(
            {
                "template_id": template_id,
                "template_data": template_data,
            },
            params,
        )
        require_string_field(body, "template_id", "sync.from_template")
        require_object_field(body, "template_data", "sync.from_template")
        return self.convert(encode_header_footer_templates(body))
