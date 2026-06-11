from __future__ import annotations

import os

from _common import client

from pdfbolt import PDFBolt, PDFBoltAPIError, PDFBoltConfigurationError

BASE_URL = os.environ.get("PDFBOLT_BASE_URL", "https://api.pdfbolt.com")

print("Case 1: missing API key should throw PDFBoltConfigurationError")
try:
    PDFBolt(api_key="")
except PDFBoltConfigurationError as error:
    print(f"Class: {error.__class__.__name__}")
    print(f"Message: {error}")

print()
print("Case 2: invalid API key should throw PDFBoltAPIError")
try:
    invalid_client = PDFBolt(api_key="invalid-api-key", base_url=BASE_URL)
    invalid_client.usage.get()
except PDFBoltAPIError as error:
    print(f"Class: {error.__class__.__name__}")
    print(f"HTTP status: {error.status_code}")
    print(f"PDFBolt code: {error.error_code}")
    print(f"Message: {error.error_message}")
    print(f"Timestamp: {error.timestamp}")
    print(f"Minute limit: {error.rate_limit.minute.limit}")
    print(f"Minute remaining: {error.rate_limit.minute.remaining}")

print()
print("Case 3: non-HTTPS URL should throw PDFBoltAPIError")
try:
    client().direct.from_url(url="http://example.com")
except PDFBoltAPIError as error:
    print(f"Class: {error.__class__.__name__}")
    print(f"HTTP status: {error.status_code}")
    print(f"PDFBolt code: {error.error_code}")
    print(f"Message: {error.error_message}")
    print(f"Timestamp: {error.timestamp}")
