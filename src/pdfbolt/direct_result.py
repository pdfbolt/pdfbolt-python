from __future__ import annotations

import base64
import binascii
import re
from collections.abc import Mapping
from pathlib import Path

from .errors import PDFBoltNetworkError
from .models import RateLimitInfo
from .rate_limit import read_header, read_number_header, read_rate_limit_info


class DirectConversionResult:
    def __init__(self, *, body: bytes, headers: Mapping[str, str]) -> None:
        self.headers = headers
        self.content_type = _normalize_content_type(read_header(headers, "content-type"))
        self.content_disposition = read_header(headers, "content-disposition")
        self.conversion_cost = read_number_header(headers, "x-pdfbolt-conversion-cost")
        self.filename = _parse_content_disposition_filename(self.content_disposition)
        self.rate_limit: RateLimitInfo = read_rate_limit_info(headers)
        self.base64: str | None

        if self.content_type == "text/plain":
            try:
                self.base64 = body.decode("utf-8").strip()
                if not self.base64:
                    raise ValueError("empty Base64 response")
                self.buffer = base64.b64decode(self.base64, validate=True)
            except (UnicodeDecodeError, binascii.Error, ValueError) as error:
                raise PDFBoltNetworkError(
                    "PDFBolt API returned a malformed Base64 direct response."
                ) from error
        else:
            self.base64 = None
            self.buffer = body

    @property
    def size(self) -> int:
        return len(self.buffer)

    def save(self, file_path: str | Path) -> None:
        Path(file_path).write_bytes(self.buffer)


def _normalize_content_type(value: str | None) -> str:
    if not value:
        return "application/pdf"

    content_types = [
        part.split(";", 1)[0].strip().lower()
        for part in value.split(",")
        if part.split(";", 1)[0].strip()
    ]
    if "application/pdf" in content_types:
        return "application/pdf"
    if "text/plain" in content_types:
        return "text/plain"

    return content_types[0] if content_types else "application/pdf"


def _parse_content_disposition_filename(content_disposition: str | None) -> str | None:
    if not content_disposition:
        return None

    match = re.search(r'(?:^|;)\s*filename="?([^";]+)"?', content_disposition, re.IGNORECASE)
    return match.group(1) if match else None
