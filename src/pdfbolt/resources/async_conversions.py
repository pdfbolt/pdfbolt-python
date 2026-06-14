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
from ..errors import PDFBoltNetworkError
from ..http import PDFBoltHttpClient
from ..models import AsyncConversionJob, async_conversion_job_from_api
from ..rate_limit import read_rate_limit_info
from ..types import AsyncConvertParams, AsyncOptions


class AsyncConversionsResource:
    def __init__(self, http: PDFBoltHttpClient) -> None:
        self._http = http

    def convert(self, params: AsyncConvertParams) -> AsyncConversionJob:
        body, request_timeout = split_request_options(cast(Mapping[str, Any], params))
        data, headers = self._http.request_json(
            "POST",
            "/v1/async",
            body=to_api_body(body),
            request_timeout=request_timeout,
        )
        try:
            return async_conversion_job_from_api(data, rate_limit=read_rate_limit_info(headers))
        except ValueError as error:
            raise PDFBoltNetworkError(
                "PDFBolt API returned a malformed async conversion response."
            ) from error

    def from_url(
        self,
        *,
        url: str,
        webhook: str,
        **params: Unpack[AsyncOptions],
    ) -> AsyncConversionJob:
        body = merge_params({"url": url, "webhook": webhook}, cast(Mapping[str, Any], params))
        require_string_field(body, "url", "async_conversions.from_url")
        require_string_field(body, "webhook", "async_conversions.from_url")
        return self.convert(cast(AsyncConvertParams, encode_header_footer_templates(body)))

    def from_html(
        self,
        *,
        html: str,
        webhook: str,
        **params: Unpack[AsyncOptions],
    ) -> AsyncConversionJob:
        body = merge_params({"html": html, "webhook": webhook}, cast(Mapping[str, Any], params))
        html_value = require_string_field(body, "html", "async_conversions.from_html")
        require_string_field(body, "webhook", "async_conversions.from_html")
        return self.convert(
            cast(
                AsyncConvertParams,
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
        webhook: str,
        **params: Unpack[AsyncOptions],
    ) -> AsyncConversionJob:
        body = merge_params(
            {
                "template_id": template_id,
                "template_data": template_data,
                "webhook": webhook,
            },
            cast(Mapping[str, Any], params),
        )
        require_string_field(body, "template_id", "async_conversions.from_template")
        require_object_field(body, "template_data", "async_conversions.from_template")
        require_string_field(body, "webhook", "async_conversions.from_template")
        return self.convert(cast(AsyncConvertParams, encode_header_footer_templates(body)))
