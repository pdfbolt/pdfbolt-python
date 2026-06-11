from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import requests

from ._version import VERSION
from .errors import PDFBoltAPIError, PDFBoltConfigurationError, PDFBoltNetworkError

DEFAULT_BASE_URL = "https://api.pdfbolt.com"
DEFAULT_REQUEST_TIMEOUT_SECONDS = 120.0


class PDFBoltHttpClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        request_timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
        session: requests.Session | None = None,
    ) -> None:
        if not api_key:
            raise PDFBoltConfigurationError("PDFBolt API key is required.")

        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._request_timeout = request_timeout
        self._session = session or requests.Session()

    def request_json(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
        request_timeout: float | None = None,
    ) -> tuple[dict[str, Any], Mapping[str, str]]:
        response = self._request(
            method,
            path,
            body=body,
            request_timeout=request_timeout,
            accept="application/json",
        )
        try:
            data = response.json()
        except ValueError as error:
            raise PDFBoltNetworkError(
                f"PDFBolt API returned a malformed JSON response for {path} "
                f"(status {response.status_code})."
            ) from error

        if not isinstance(data, dict):
            raise PDFBoltNetworkError(
                f"PDFBolt API returned a malformed JSON response for {path} "
                f"(status {response.status_code})."
            )

        return data, response.headers

    def request_binary(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
        request_timeout: float | None = None,
    ) -> tuple[bytes, Mapping[str, str]]:
        response = self._request(
            method,
            path,
            body=body,
            request_timeout=request_timeout,
            accept="application/pdf, text/plain, application/json",
        )
        return response.content, response.headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None,
        request_timeout: float | None,
        accept: str,
    ) -> requests.Response:
        timeout = self._request_timeout if request_timeout is None else request_timeout
        headers = self._headers(accept=accept, has_body=body is not None)

        try:
            response = self._session.request(
                method,
                f"{self._base_url}{path}",
                headers=headers,
                json=body,
                timeout=timeout,
            )
        except requests.Timeout as error:
            raise PDFBoltNetworkError(f"PDFBolt request timed out after {timeout}s.") from error
        except Exception as error:
            raise PDFBoltNetworkError(
                "PDFBolt request failed before receiving a response."
            ) from error

        if response.status_code >= 400:
            raise _create_api_error(response)

        return response

    def _headers(self, *, accept: str, has_body: bool) -> dict[str, str]:
        headers = {
            "Accept": accept,
            "API-KEY": self._api_key,
            "User-Agent": f"pdfbolt-python/{VERSION}",
        }
        if has_body:
            headers["Content-Type"] = "application/json"
        return headers


def _create_api_error(response: requests.Response) -> PDFBoltAPIError:
    raw_body = response.text
    parsed = _parse_json_object(raw_body)
    error_message = _read_string(parsed, "errorMessage")
    message = (
        error_message
        or response.reason
        or (f"PDFBolt API request failed with status {response.status_code}.")
    )

    return PDFBoltAPIError(
        message=message,
        status_code=response.status_code,
        timestamp=_read_string(parsed, "timestamp"),
        error_code=_read_string(parsed, "errorCode"),
        error_message=error_message,
        headers=response.headers,
        raw_body=raw_body,
    )


def _parse_json_object(raw_body: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(raw_body)
    except json.JSONDecodeError:
        return None

    return parsed if isinstance(parsed, dict) else None


def _read_string(source: dict[str, Any] | None, key: str) -> str | None:
    value = source.get(key) if source else None
    return value if isinstance(value, str) else None
