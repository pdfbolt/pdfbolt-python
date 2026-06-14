from __future__ import annotations

import base64
import hashlib
import hmac
import json
from io import BytesIO
from pathlib import Path

import pytest
import responses

from examples.webhook_server import _read_chunked_body
from pdfbolt import (
    VERSION,
    PDFBolt,
    PDFBoltAPIError,
    PDFBoltConfigurationError,
    PDFBoltNetworkError,
    PDFBoltValidationError,
    PDFBoltWebhookSignatureError,
    webhooks,
)

BASE_URL = "https://api.test.pdfbolt.local"
API_KEY = "test-api-key"


@responses.activate
def test_direct_from_html_encodes_html_and_header_footer_templates() -> None:
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/direct",
        body=b"%PDF-test",
        headers={
            "content-type": "application/pdf",
            "content-disposition": 'attachment; filename="invoice.pdf"',
            "x-pdfbolt-conversion-cost": "1",
            "x-pdfbolt-limit-minute": "500",
            "x-pdfbolt-remaining-minute": "499",
        },
        status=200,
    )

    client = PDFBolt(api_key=API_KEY, base_url=BASE_URL)
    result = client.direct.from_html(
        html="<h1>Hello</h1>",
        display_header_footer=True,
        header_template="<span>Header</span>",
        footer_template="<span>Footer</span>",
        print_background=True,
    )

    request = responses.calls[0].request
    body = json.loads(request.body.decode("utf-8"))

    assert request.headers["API-KEY"] == API_KEY
    assert request.headers["User-Agent"] == f"pdfbolt-python/{VERSION}"
    assert body["html"] == base64.b64encode(b"<h1>Hello</h1>").decode("ascii")
    assert body["displayHeaderFooter"] is True
    assert body["headerTemplate"] == base64.b64encode(b"<span>Header</span>").decode("ascii")
    assert body["footerTemplate"] == base64.b64encode(b"<span>Footer</span>").decode("ascii")
    assert body["printBackground"] is True
    assert result.buffer == b"%PDF-test"
    assert result.base64 is None
    assert result.size == 9
    assert result.filename == "invoice.pdf"
    assert result.conversion_cost == 1
    assert result.rate_limit.minute.remaining == 499


@responses.activate
def test_direct_encoded_response_decodes_base64_and_save(tmp_path: Path) -> None:
    encoded = base64.b64encode(b"%PDF-encoded").decode("ascii")
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/direct",
        body=encoded,
        headers={"content-type": "text/plain"},
        status=200,
    )

    client = PDFBolt(api_key=API_KEY, base_url=BASE_URL)
    result = client.direct.convert({"url": "https://example.com", "is_encoded": True})
    output = tmp_path / "encoded.pdf"
    result.save(output)

    assert result.base64 == encoded
    assert result.buffer == b"%PDF-encoded"
    assert output.read_bytes() == b"%PDF-encoded"
    body = json.loads(responses.calls[0].request.body.decode("utf-8"))
    assert body["isEncoded"] is True


@responses.activate
def test_malformed_direct_base64_response_maps_to_network_error() -> None:
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/direct",
        body="not valid base64",
        headers={"content-type": "text/plain"},
        status=200,
    )

    client = PDFBolt(api_key=API_KEY, base_url=BASE_URL)

    with pytest.raises(PDFBoltNetworkError, match="malformed Base64 direct response"):
        client.direct.convert({"url": "https://example.com", "is_encoded": True})


@responses.activate
def test_sync_result_maps_json_and_response_headers() -> None:
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/sync",
        json={
            "requestId": "req_123",
            "status": "SUCCESS",
            "errorCode": None,
            "errorMessage": None,
            "documentUrl": "https://example.com/file.pdf",
            "expiresAt": "2026-06-12T00:00:00Z",
            "isAsync": False,
            "duration": 584,
            "documentSizeMb": 0.02,
            "isCustomS3Bucket": False,
        },
        headers={
            "x-pdfbolt-conversion-cost": "1",
            "x-pdfbolt-limit-day": "100000",
            "x-pdfbolt-remaining-day": "99999",
        },
        status=200,
    )

    client = PDFBolt(api_key=API_KEY, base_url=BASE_URL)
    result = client.sync.from_url(url="https://example.com", format="A4")

    assert result.request_id == "req_123"
    assert result.status == "SUCCESS"
    assert result.document_url == "https://example.com/file.pdf"
    assert result.conversion_cost == 1
    assert result.rate_limit.day.remaining == 99999
    body = json.loads(responses.calls[0].request.body.decode("utf-8"))
    assert body == {"url": "https://example.com", "format": "A4"}


@responses.activate
def test_malformed_sync_response_maps_to_network_error() -> None:
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/sync",
        json={
            "status": "SUCCESS",
            "errorCode": None,
            "errorMessage": None,
            "documentUrl": "https://example.com/file.pdf",
            "expiresAt": "2026-06-12T00:00:00Z",
            "isAsync": False,
            "duration": 584,
            "documentSizeMb": 0.02,
            "isCustomS3Bucket": False,
        },
        status=200,
    )

    client = PDFBolt(api_key=API_KEY, base_url=BASE_URL)

    with pytest.raises(PDFBoltNetworkError, match="malformed sync conversion response"):
        client.sync.from_url(url="https://example.com")


@pytest.mark.parametrize(
    ("status_value", "is_async_value"),
    [
        ("FAILURE", False),
        ("SUCCESS", True),
    ],
)
@responses.activate
def test_sync_response_requires_success_status_and_non_async_flag(
    status_value: str,
    is_async_value: bool,
) -> None:
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/sync",
        json={
            "requestId": "req_123",
            "status": status_value,
            "errorCode": None,
            "errorMessage": None,
            "documentUrl": "https://example.com/file.pdf",
            "expiresAt": "2026-06-12T00:00:00Z",
            "isAsync": is_async_value,
            "duration": 584,
            "documentSizeMb": 0.02,
            "isCustomS3Bucket": False,
        },
        status=200,
    )

    client = PDFBolt(api_key=API_KEY, base_url=BASE_URL)

    with pytest.raises(PDFBoltNetworkError, match="malformed sync conversion response"):
        client.sync.from_url(url="https://example.com")


@responses.activate
def test_async_request_maps_options_and_keeps_request_timeout_out_of_body() -> None:
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/async",
        json={"requestId": "job_123"},
        headers={"x-pdfbolt-remaining-minute": "498"},
        status=200,
    )

    client = PDFBolt(api_key=API_KEY, base_url=BASE_URL)
    job = client.async_conversions.from_url(
        url="https://example.com",
        webhook="https://example.com/webhook",
        retry_delays=[5, 15, 60],
        additional_webhook_headers={"x-test": "ok"},
        request_timeout=30,
    )

    body = json.loads(responses.calls[0].request.body.decode("utf-8"))
    assert job.request_id == "job_123"
    assert job.rate_limit.minute.remaining == 498
    assert body["retryDelays"] == [5, 15, 60]
    assert body["additionalWebhookHeaders"] == {"x-test": "ok"}
    assert "requestTimeout" not in body
    assert "request_timeout" not in body


@responses.activate
def test_malformed_async_job_response_maps_to_network_error() -> None:
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/async",
        json={"requestId": 123},
        status=200,
    )

    client = PDFBolt(api_key=API_KEY, base_url=BASE_URL)

    with pytest.raises(PDFBoltNetworkError, match="malformed async conversion response"):
        client.async_conversions.from_url(
            url="https://example.com",
            webhook="https://example.com/webhook",
        )


@responses.activate
def test_conversion_option_acronyms_map_to_api_field_names() -> None:
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/direct",
        body=b"%PDF-test",
        headers={"content-type": "application/pdf"},
        status=200,
    )

    client = PDFBolt(api_key=API_KEY, base_url=BASE_URL)
    client.direct.from_url(
        url="https://example.com",
        extra_http_headers={"x-test": "ok"},
        apply_extra_http_headers_to_all_resources=True,
    )

    body = json.loads(responses.calls[0].request.body.decode("utf-8"))
    assert body["extraHTTPHeaders"] == {"x-test": "ok"}
    assert body["applyExtraHTTPHeadersToAllResources"] is True
    assert "extraHttpHeaders" not in body
    assert "applyExtraHttpHeadersToAllResources" not in body


@responses.activate
def test_template_data_is_not_camel_cased() -> None:
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/direct",
        body=b"%PDF-template",
        headers={"content-type": "application/pdf"},
        status=200,
    )

    client = PDFBolt(api_key=API_KEY, base_url=BASE_URL)
    client.direct.from_template(
        template_id="template_123",
        template_data={
            "invoice_number": "INV-001",
            "line_items": [{"unit_price": "$10.00"}],
        },
    )

    body = json.loads(responses.calls[0].request.body.decode("utf-8"))
    assert body["templateId"] == "template_123"
    assert body["templateData"] == {
        "invoice_number": "INV-001",
        "line_items": [{"unit_price": "$10.00"}],
    }


@responses.activate
def test_api_errors_map_to_pdfbolt_api_error() -> None:
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/direct",
        json={
            "timestamp": "2026-06-11T10:00:00Z",
            "httpErrorCode": 400,
            "errorCode": "BAD_REQUEST",
            "errorMessage": "Invalid URL.",
        },
        headers={"x-pdfbolt-limit-minute": "500", "x-pdfbolt-remaining-minute": "497"},
        status=400,
    )

    client = PDFBolt(api_key=API_KEY, base_url=BASE_URL)

    with pytest.raises(PDFBoltAPIError) as exc:
        client.direct.from_url(url="https://example.com")

    assert exc.value.status_code == 400
    assert exc.value.timestamp == "2026-06-11T10:00:00Z"
    assert exc.value.error_code == "BAD_REQUEST"
    assert exc.value.error_message == "Invalid URL."
    assert exc.value.rate_limit.minute.limit == 500
    assert exc.value.raw_body is not None


@responses.activate
def test_malformed_usage_response_maps_to_network_error() -> None:
    responses.add(
        responses.GET,
        f"{BASE_URL}/v1/usage",
        json={
            "plan": "ENTERPRISE_1_MONTHLY",
            "recurring": [{"left": 1, "expires": "2026-06-12T00:00:00Z", "overage": 0}],
            "oneTime": [],
        },
        status=200,
    )

    client = PDFBolt(api_key=API_KEY, base_url=BASE_URL)

    with pytest.raises(PDFBoltNetworkError, match="malformed usage response"):
        client.usage.get()


@pytest.mark.parametrize("missing_key", ["recurring", "oneTime"])
@responses.activate
def test_usage_response_requires_credit_package_lists(missing_key: str) -> None:
    body = {
        "plan": "ENTERPRISE_1_MONTHLY",
        "recurring": [],
        "oneTime": [],
    }
    del body[missing_key]

    responses.add(
        responses.GET,
        f"{BASE_URL}/v1/usage",
        json=body,
        status=200,
    )

    client = PDFBolt(api_key=API_KEY, base_url=BASE_URL)

    with pytest.raises(PDFBoltNetworkError, match="malformed usage response"):
        client.usage.get()


@responses.activate
def test_malformed_success_json_maps_to_network_error() -> None:
    responses.add(
        responses.POST,
        f"{BASE_URL}/v1/sync",
        body="{not json",
        headers={"content-type": "application/json"},
        status=200,
    )

    client = PDFBolt(api_key=API_KEY, base_url=BASE_URL)

    with pytest.raises(PDFBoltNetworkError, match="malformed JSON response"):
        client.sync.from_url(url="https://example.com")


def test_configuration_and_validation_errors() -> None:
    with pytest.raises(PDFBoltConfigurationError):
        PDFBolt(api_key="")

    client = PDFBolt(api_key=API_KEY, base_url=BASE_URL)
    with pytest.raises(PDFBoltValidationError):
        client.direct.from_html(html=123)  # type: ignore[arg-type]

    with pytest.raises(PDFBoltValidationError):
        client.sync.convert({"url": "https://example.com", "request_timeout": "slow"})


@responses.activate
def test_network_errors_are_pdfbolt_network_errors() -> None:
    responses.add(
        responses.GET,
        f"{BASE_URL}/v1/usage",
        body=ConnectionError("connection closed"),
    )

    client = PDFBolt(api_key=API_KEY, base_url=BASE_URL)

    with pytest.raises(PDFBoltNetworkError):
        client.usage.get()


def test_webhook_signature_helpers() -> None:
    raw_body = b'{"requestId":"req_123","status":"SUCCESS","errorCode":null,"errorMessage":null,"documentUrl":"https://example.com/file.pdf","expiresAt":"2026-06-12T00:00:00Z","isAsync":true,"duration":100,"documentSizeMb":0.01,"isCustomS3Bucket":false}'
    digest = hmac.new(b"secret", raw_body, hashlib.sha256).hexdigest()
    signature = f"sha256={digest}"

    assert webhooks.verify_signature(raw_body=raw_body, signature=signature, secret="secret")
    event = webhooks.verify_and_parse(raw_body=raw_body, signature=signature, secret="secret")

    assert event.request_id == "req_123"
    assert event.status == "SUCCESS"
    assert event.document_url == "https://example.com/file.pdf"

    with pytest.raises(PDFBoltWebhookSignatureError):
        webhooks.verify_and_parse(raw_body=raw_body, signature="sha256=bad", secret="secret")

    assert not webhooks.verify_signature(raw_body=raw_body, signature=signature, secret="")
    with pytest.raises(PDFBoltWebhookSignatureError):
        webhooks.verify_and_parse(raw_body=raw_body, signature=signature, secret="")

    assert not webhooks.verify_signature(raw_body=raw_body, signature="ś", secret="secret")
    with pytest.raises(PDFBoltWebhookSignatureError):
        webhooks.verify_and_parse(raw_body=raw_body, signature="ś", secret="secret")


def test_webhook_malformed_payload_maps_to_webhook_error() -> None:
    raw_body = b"{not json"
    digest = hmac.new(b"secret", raw_body, hashlib.sha256).hexdigest()
    signature = f"sha256={digest}"

    with pytest.raises(PDFBoltWebhookSignatureError, match="Invalid PDFBolt webhook payload"):
        webhooks.verify_and_parse(raw_body=raw_body, signature=signature, secret="secret")


def test_webhook_schema_errors_map_to_webhook_error() -> None:
    raw_body = (
        b'{"status":"SUCCESS","errorCode":null,"errorMessage":null,'
        b'"documentUrl":"https://example.com/file.pdf",'
        b'"expiresAt":"2026-06-12T00:00:00Z","isAsync":true,'
        b'"duration":100,"documentSizeMb":0.01,"isCustomS3Bucket":false}'
    )
    digest = hmac.new(b"secret", raw_body, hashlib.sha256).hexdigest()
    signature = f"sha256={digest}"

    with pytest.raises(PDFBoltWebhookSignatureError, match="Invalid PDFBolt webhook payload"):
        webhooks.verify_and_parse(raw_body=raw_body, signature=signature, secret="secret")


@pytest.mark.parametrize(
    "raw_body",
    [
        b'{"requestId":"req_123","status":"PENDING","errorCode":null,"errorMessage":null,"documentUrl":"https://example.com/file.pdf","expiresAt":"2026-06-12T00:00:00Z","isAsync":true,"duration":100,"documentSizeMb":0.01,"isCustomS3Bucket":false}',
        b'{"requestId":"req_123","status":"SUCCESS","errorCode":null,"errorMessage":null,"documentUrl":"https://example.com/file.pdf","expiresAt":"2026-06-12T00:00:00Z","isAsync":false,"duration":100,"documentSizeMb":0.01,"isCustomS3Bucket":false}',
    ],
)
def test_webhook_payload_requires_final_status_and_async_flag(raw_body: bytes) -> None:
    digest = hmac.new(b"secret", raw_body, hashlib.sha256).hexdigest()
    signature = f"sha256={digest}"

    with pytest.raises(PDFBoltWebhookSignatureError, match="Invalid PDFBolt webhook payload"):
        webhooks.verify_and_parse(raw_body=raw_body, signature=signature, secret="secret")


def test_webhook_server_reads_chunked_body_with_trailers() -> None:
    raw_stream = BytesIO(
        b"5\r\nhello\r\n6;ext=value\r\n world\r\n0\r\nx-test: ok\r\nanother: value\r\n\r\n"
    )

    assert _read_chunked_body(raw_stream) == b"hello world"


def test_webhook_server_rejects_truncated_chunked_body() -> None:
    with pytest.raises(ValueError, match="unexpected EOF"):
        _read_chunked_body(BytesIO(b"5\r\nhe"))


def test_client_exposes_resources_and_static_webhooks() -> None:
    client = PDFBolt(api_key=API_KEY, base_url=BASE_URL)

    assert client.direct is not None
    assert client.sync is not None
    assert client.async_conversions is not None
    assert client.usage is not None
    assert PDFBolt.webhooks is webhooks
