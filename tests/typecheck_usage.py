from __future__ import annotations

from typing import TYPE_CHECKING

from pdfbolt import (
    AsyncConvertParams,
    DirectConversionResult,
    DirectConvertParams,
    PDFBolt,
    SyncConversionResult,
    SyncConvertParams,
    UsageSummary,
)

if TYPE_CHECKING:
    client = PDFBolt(api_key="test-api-key")

    direct_params: DirectConvertParams = {
        "html": "PGgxPkhlbGxvPC9oMT4=",
        "format": "A4",
        "margin": {"top": "12mm", "bottom": "12mm"},
        "print_background": True,
        "is_encoded": True,
        "request_timeout": 30,
    }

    sync_params: SyncConvertParams = {
        "url": "https://example.com",
        "custom_s3_presigned_url": None,
        "print_production": {
            "pdf_standard": "pdf-x-4",
            "color_space": "cmyk",
            "icc_profile": "fogra39",
        },
    }

    async_params: AsyncConvertParams = {
        "template_id": "template-id",
        "template_data": {"invoice_number": "INV-001"},
        "webhook": "https://example.com/webhook",
        "additional_webhook_headers": {"x-test": "ok"},
        "retry_delays": [5, 15, 60],
    }

    direct_result: DirectConversionResult = client.direct.from_url(
        url="https://example.com",
        format="A4",
        extra_http_headers={"User-Agent": "render-browser/1.0"},
    )
    direct_convert_result: DirectConversionResult = client.direct.convert(direct_params)
    sync_result: SyncConversionResult = client.sync.convert(sync_params)
    async_job = client.async_conversions.convert(async_params)
    usage: UsageSummary = client.usage.get(request_timeout=30)

    _ = (direct_result, direct_convert_result, sync_result, async_job, usage)
