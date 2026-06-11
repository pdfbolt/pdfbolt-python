from __future__ import annotations

import os

from _common import client, print_rate_limit

pdfbolt = client()

result = pdfbolt.sync.from_html(
    html="<h1>PDFBolt Python Sync Example</h1><p>This returns a temporary PDF URL.</p>",
    format="A4",
    print_background=True,
)

print("Sync conversion result")
print(f"Request ID: {result.request_id}")
print(f"Status: {result.status}")
print(f"Document URL: {result.document_url}")
print(f"Expires at: {result.expires_at}")
print(f"Duration ms: {result.duration}")
print(f"Document size MB: {result.document_size_mb}")
print(f"Conversion cost: {result.conversion_cost}")
print_rate_limit(result.rate_limit)

custom_s3_url = os.environ.get("PDFBOLT_CUSTOM_S3_PRESIGNED_URL")
if custom_s3_url:
    custom = pdfbolt.sync.from_html(
        html="<h1>PDFBolt Python Custom S3 Example</h1>",
        custom_s3_presigned_url=custom_s3_url,
    )
    print()
    print("Custom S3 upload result")
    print(f"Request ID: {custom.request_id}")
    print(f"Custom S3 bucket: {custom.is_custom_s3_bucket}")
    print(f"Document URL: {custom.document_url}")
    print(f"Expires at: {custom.expires_at}")
