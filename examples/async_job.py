from __future__ import annotations

import os

from _common import client, print_rate_limit, required_env

pdfbolt = client()
webhook = required_env("PDFBOLT_WEBHOOK_URL")

job = pdfbolt.async_conversions.from_html(
    html="<h1>PDFBolt Python Async Example</h1>",
    webhook=webhook,
    retry_delays=[5, 15, 60],
)

print("Async conversion accepted")
print(f"Request ID: {job.request_id}")
print(f"Webhook URL: {webhook}")
print_rate_limit(job.rate_limit)
print("Final conversion cost is delivered later with the webhook.")

custom_s3_url = os.environ.get("PDFBOLT_CUSTOM_S3_PRESIGNED_URL")
if custom_s3_url:
    custom_job = pdfbolt.async_conversions.from_html(
        html="<h1>PDFBolt Python Async Custom S3 Example</h1>",
        webhook=webhook,
        custom_s3_presigned_url=custom_s3_url,
    )
    print()
    print("Async custom S3 job accepted")
    print(f"Request ID: {custom_job.request_id}")
    print_rate_limit(custom_job.rate_limit)
    print(
        "After successful upload, the final webhook should have "
        "isCustomS3Bucket: true, documentUrl: null, and expiresAt: null."
    )
