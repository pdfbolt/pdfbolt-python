from __future__ import annotations

import json
import os

import pytest

from pdfbolt import PDFBolt, PDFBoltAPIError, PDFBoltNetworkError

pytestmark = pytest.mark.skipif(
    os.environ.get("PDFBOLT_RUN_LIVE_TESTS") != "1" or not os.environ.get("PDFBOLT_API_KEY"),
    reason="Set PDFBOLT_RUN_LIVE_TESTS=1 and PDFBOLT_API_KEY to run live API tests.",
)


def client(api_key: str | None = None) -> PDFBolt:
    return PDFBolt(
        api_key=api_key or os.environ["PDFBOLT_API_KEY"],
        base_url=os.environ.get("PDFBOLT_BASE_URL", "https://api.pdfbolt.com"),
    )


def template_data() -> dict[str, object]:
    raw = os.environ.get("PDFBOLT_TEMPLATE_DATA_JSON")
    if raw:
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)
        return parsed

    return {
        "invoice_number": "PYTHON-SDK-LIVE-001",
        "customer_name": "Acme Inc.",
        "total": "$123.00",
    }


def assert_pdf(result: object) -> None:
    buffer = result.buffer
    assert isinstance(buffer, bytes)
    assert buffer.startswith(b"%PDF-")
    assert result.size > 500
    assert result.conversion_cost in (None, 0, 1) or result.conversion_cost > 0


def assert_sync_success(result: object) -> None:
    assert result.request_id
    assert result.status == "SUCCESS"
    assert result.document_url or result.is_custom_s3_bucket
    assert result.rate_limit.minute.remaining is None or (result.rate_limit.minute.remaining >= 0)


def test_gets_usage_details() -> None:
    usage = client().usage.get()

    assert usage.plan
    assert isinstance(usage.recurring, list)
    assert isinstance(usage.one_time, list)
    assert usage.rate_limit.minute.limit is None or usage.rate_limit.minute.limit > 0


def test_generates_direct_pdf_from_raw_html() -> None:
    pdf = client().direct.from_html(
        html="<h1>PDFBolt Python SDK</h1><p>Live direct HTML test.</p>",
        filename="python-sdk-direct-html.pdf",
        print_background=True,
    )

    assert_pdf(pdf)
    assert pdf.content_type == "application/pdf"


def test_generates_direct_pdf_from_url() -> None:
    pdf = client().direct.from_url(
        url="https://example.com",
        print_background=True,
    )

    assert_pdf(pdf)


def test_generates_base64_direct_pdf_from_raw_html() -> None:
    pdf = client().direct.from_html(
        html="<h1>PDFBolt Python SDK</h1><p>Base64 direct response test.</p>",
        is_encoded=True,
    )

    assert_pdf(pdf)
    assert isinstance(pdf.base64, str)
    assert pdf.content_type == "text/plain"


def test_generates_sync_pdf_url_from_raw_html() -> None:
    result = client().sync.from_html(
        html="<h1>PDFBolt Python SDK</h1><p>Live sync HTML test.</p>",
        print_background=True,
    )

    assert_sync_success(result)
    assert result.conversion_cost is None or result.conversion_cost >= 0


def test_generates_sync_pdf_url_from_url() -> None:
    result = client().sync.from_url(
        url="https://example.com",
        print_background=True,
    )

    assert_sync_success(result)


def test_uploads_sync_result_to_custom_s3_when_presigned_url_is_set() -> None:
    presigned_url = os.environ.get("PDFBOLT_CUSTOM_S3_PRESIGNED_URL")
    if not presigned_url:
        pytest.skip("Set PDFBOLT_CUSTOM_S3_PRESIGNED_URL to run custom S3 live test.")

    result = client().sync.from_html(
        html="<h1>PDFBolt Python SDK</h1><p>Custom S3 live test.</p>",
        custom_s3_presigned_url=presigned_url,
    )

    assert result.request_id
    assert result.status == "SUCCESS"
    assert result.is_custom_s3_bucket is True
    assert result.document_url is None
    assert result.expires_at is None


def test_maps_invalid_api_key_to_api_error() -> None:
    with pytest.raises(PDFBoltAPIError) as exc:
        client(api_key="invalid-api-key").usage.get()

    assert exc.value.status_code == 401
    assert exc.value.error_code == "UNAUTHORIZED"


def test_accepts_async_html_job_when_webhook_url_is_set() -> None:
    webhook = os.environ.get("PDFBOLT_WEBHOOK_URL")
    if not webhook:
        pytest.skip("Set PDFBOLT_WEBHOOK_URL to run async live test.")

    job = client().async_conversions.from_html(
        html="<h1>PDFBolt Python SDK</h1><p>Async live test.</p>",
        webhook=webhook,
        retry_delays=[5, 15, 60],
    )

    assert job.request_id
    assert job.rate_limit.minute.remaining is None or job.rate_limit.minute.remaining >= 0


def test_generates_direct_template_pdf_when_template_id_is_set() -> None:
    template_id = os.environ.get("PDFBOLT_TEMPLATE_ID")
    if not template_id:
        pytest.skip("Set PDFBOLT_TEMPLATE_ID to run template live test.")

    pdf = client().direct.from_template(
        template_id=template_id,
        template_data=template_data(),
    )

    assert_pdf(pdf)


def test_generates_sync_template_pdf_url_when_template_id_is_set() -> None:
    template_id = os.environ.get("PDFBOLT_TEMPLATE_ID")
    if not template_id:
        pytest.skip("Set PDFBOLT_TEMPLATE_ID to run template live test.")

    try:
        result = client().sync.from_template(
            template_id=template_id,
            template_data=template_data(),
        )
    except PDFBoltNetworkError as error:
        pytest.fail(f"Sync template conversion closed before HTTP response: {error}")

    assert_sync_success(result)
