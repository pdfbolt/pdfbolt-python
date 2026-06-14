from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Unpack, cast

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
from ..types import DirectConvertParams, DirectOptions


class DirectResource:
    def __init__(self, http: PDFBoltHttpClient) -> None:
        self._http = http

    def convert(self, params: DirectConvertParams) -> DirectConversionResult:
        body, request_timeout = split_request_options(cast(Mapping[str, Any], params))
        response_body, headers = self._http.request_binary(
            "POST",
            "/v1/direct",
            body=to_api_body(body),
            request_timeout=request_timeout,
        )
        return DirectConversionResult(body=response_body, headers=headers)

    def from_url(self, *, url: str, **params: Unpack[DirectOptions]) -> DirectConversionResult:
        body = merge_params({"url": url}, cast(Mapping[str, Any], params))
        require_string_field(body, "url", "direct.from_url")
        return self.convert(cast(DirectConvertParams, encode_header_footer_templates(body)))

    def from_html(self, *, html: str, **params: Unpack[DirectOptions]) -> DirectConversionResult:
        body = merge_params({"html": html}, cast(Mapping[str, Any], params))
        html_value = require_string_field(body, "html", "direct.from_html")
        return self.convert(
            cast(
                DirectConvertParams,
                encode_header_footer_templates(
                    {
                        **body,
                        "html": encode_base64(html_value),
                    }
                ),
            ),
        )

    def from_template(
        self,
        *,
        template_id: str,
        template_data: Mapping[str, Any],
        **params: Unpack[DirectOptions],
    ) -> DirectConversionResult:
        body = merge_params(
            {
                "template_id": template_id,
                "template_data": template_data,
            },
            cast(Mapping[str, Any], params),
        )
        require_string_field(body, "template_id", "direct.from_template")
        require_object_field(body, "template_data", "direct.from_template")
        return self.convert(cast(DirectConvertParams, encode_header_footer_templates(body)))
