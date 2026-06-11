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
from ..direct_result import DirectConversionResult
from ..http import PDFBoltHttpClient


class DirectResource:
    def __init__(self, http: PDFBoltHttpClient) -> None:
        self._http = http

    def convert(self, params: Mapping[str, Any]) -> DirectConversionResult:
        body, request_timeout = split_request_options(params)
        response_body, headers = self._http.request_binary(
            "POST",
            "/v1/direct",
            body=to_api_body(body),
            request_timeout=request_timeout,
        )
        return DirectConversionResult(body=response_body, headers=headers)

    def from_url(self, *, url: str, **params: Any) -> DirectConversionResult:
        body = merge_params({"url": url}, params)
        require_string_field(body, "url", "direct.from_url")
        return self.convert(encode_header_footer_templates(body))

    def from_html(self, *, html: str, **params: Any) -> DirectConversionResult:
        body = merge_params({"html": html}, params)
        html_value = require_string_field(body, "html", "direct.from_html")
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
    ) -> DirectConversionResult:
        body = merge_params(
            {
                "template_id": template_id,
                "template_data": template_data,
            },
            params,
        )
        require_string_field(body, "template_id", "direct.from_template")
        require_object_field(body, "template_data", "direct.from_template")
        return self.convert(encode_header_footer_templates(body))
