# PDFBolt Python SDK

Official Python SDK for the PDFBolt API.

PDFBolt generates PDFs from HTTPS URLs, raw HTML, and published templates. See the [PDFBolt docs](https://pdfbolt.com/docs) and [OpenAPI reference](https://pdfbolt.com/docs/api-reference) for the full REST API. The SDK is typed, uses `requests`, and is intended for server-side Python applications.

## Installation

```bash
pip install pdfbolt
```

Requires Python 3.11 or newer.

## Quick Start

```python
import os

from pdfbolt import PDFBolt, VERSION

pdfbolt = PDFBolt(api_key=os.environ["PDFBOLT_API_KEY"])

pdf = pdfbolt.direct.from_url(
    url="https://example.com",
    print_background=True,
)

pdf.save("example.pdf")

print(f"Using PDFBolt SDK {VERSION}")
print(f"Saved {pdf.size} bytes")
```

## Convert a URL to PDF

Use `from_url()` when you want PDFBolt to load an HTTPS page and render it as a PDF.

```python
pdf = pdfbolt.direct.from_url(
    url="https://example.com",
    format="A4",
    print_background=True,
)

pdf.save("url.pdf")
```

## Convert HTML to PDF

Use `from_html()` when you have raw HTML. The SDK automatically encodes it to Base64 for the API.

```python
pdf = pdfbolt.direct.from_html(
    html="<h1>Hello from PDFBolt</h1>",
    format="A4",
)

pdf.save("hello.pdf")
```

If you already have a Base64-encoded HTML string, use `convert()` directly. It returns the same `DirectConversionResult` as `from_html()`.

```python
pdf = pdfbolt.direct.convert({
    "html": "PGgxPkhlbGxvPC9oMT4="
})

pdf.save("hello.pdf")
```

Header and footer templates work the same way: `from_url()`, `from_html()`, and `from_template()` accept raw HTML templates and automatically encode them to Base64, while `convert()` expects Base64-encoded template values.

This rule applies to all low-level `convert()` methods: `direct.convert()`, `sync.convert()`, and `async_conversions.convert()` send HTML and header/footer template values as provided.

See the [`headerTemplate`](https://pdfbolt.com/docs/parameters#headertemplate) and [`footerTemplate`](https://pdfbolt.com/docs/parameters#footertemplate) parameter docs for supported placeholders and examples.

```python
pdf = pdfbolt.direct.from_html(
    html="<h1>Invoice</h1>",
    display_header_footer=True,
    header_template='<div style="font-size:9px;width:100%;text-align:center;">Invoice</div>',
    footer_template='<div style="font-size:9px;width:100%;text-align:center;">Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>',
    margin={
        "top": "20mm",
        "bottom": "20mm",
    },
)

pdf.save("invoice.pdf")
```

## Convert a Template to PDF

Use `from_template()` with a published PDFBolt template ID and the JSON data for that template.

```python
pdf = pdfbolt.direct.from_template(
    template_id="00000000-0000-0000-0000-000000000000",
    template_data={
        "invoiceNumber": "INV-1001",
        "customerName": "Acme Inc.",
        "total": "$250.00",
    },
)

pdf.save("template.pdf")
```

`template_data` is sent as provided. The SDK does not rename keys inside your template data object.

## Direct Results

Use `pdfbolt.direct` when you want the generated PDF returned in the HTTP response. Direct conversions return a `DirectConversionResult`.

`DirectConversionResult.buffer` always contains PDF bytes. When you pass `is_encoded=True`, PDFBolt returns Base64 text and the SDK exposes it as `DirectConversionResult.base64`. `DirectConversionResult.buffer` still contains decoded PDF bytes, so `save()` works the same way.

```python
pdf = pdfbolt.direct.from_url(
    url="https://example.com",
    filename="example.pdf",
)

pdf.save("example.pdf")

print(pdf.buffer)  # bytes with PDF content
print(pdf.base64)  # string only when is_encoded=True, otherwise None
print(pdf.size)
print(pdf.content_type)
print(pdf.content_disposition)
print(pdf.filename)
print(pdf.conversion_cost)
print(pdf.rate_limit.minute.remaining)
print(pdf.headers.get("x-pdfbolt-conversion-cost"))
```

Direct, Sync, Async job, and Usage results expose parsed rate-limit values through `rate_limit`. Rate-limit fields can be `None` when a response does not include the matching header. Direct results also expose raw HTTP headers through `pdf.headers`.

## Get a Temporary URL

Use `pdfbolt.sync` when you want PDFBolt to generate the document and return a temporary download URL.

```python
result = pdfbolt.sync.from_url(url="https://example.com")

print(result.request_id)
print(result.status)
print(result.document_url)
print(result.expires_at)
print(result.duration)
print(result.document_size_mb)
print(result.rate_limit.minute.remaining)
print(result.conversion_cost)
```

For custom S3 uploads, pass a valid presigned URL. PDFBolt uploads the generated PDF to your S3-compatible bucket, so `document_url` and `expires_at` are `None`.

```python
result = pdfbolt.sync.from_html(
    html="<h1>Invoice</h1>",
    custom_s3_presigned_url=os.environ["PDFBOLT_CUSTOM_S3_PRESIGNED_URL"],
)

print(result.is_custom_s3_bucket)  # True
print(result.document_url)  # None
```

Presigned URLs are usually time-limited and often single-use. Generate a new HTTPS presigned PUT URL for each conversion. Do not commit presigned URLs; they grant temporary write access. If your URL signs `Content-Type` or `Content-Disposition`, the PDFBolt upload request must send matching values. When possible, sign only the `host` header to avoid signature mismatches.

See [Uploading to Your S3 Bucket](https://pdfbolt.com/docs/s3-bucket-upload) for setup details.

## Run an Async Conversion

Use `pdfbolt.async_conversions` when the conversion should run in the background. The request returns an accepted job with a `request_id` immediately, and PDFBolt sends the final success or failure payload to your HTTPS webhook later.

```python
job = pdfbolt.async_conversions.from_url(
    url="https://example.com",
    webhook="https://your-app.com/webhooks/pdfbolt",
    retry_delays=[5, 15, 60],
)

print(job.request_id)
print(job.rate_limit.minute.remaining)
```

[`retryDelays`](https://pdfbolt.com/docs/api-endpoints/async#retrydelays) are in minutes and retry the conversion attempt itself, not webhook delivery.

For async custom S3 uploads, pass a valid `custom_s3_presigned_url` in the async request. After a successful upload, the final webhook has `is_custom_s3_bucket=True`, `document_url=None`, and `expires_at=None`.

## Verify Webhook Signatures

Use the exact raw request body received from your framework. Do not parse and re-serialize JSON before verification. Supported raw body types are `str`, `bytes`, `bytearray`, and `memoryview`.

The `secret` value is your PDFBolt webhook signature key, not your API key.

```python
import os

from pdfbolt import webhooks

event = webhooks.verify_and_parse(
    raw_body=raw_body,
    signature=request.headers.get("x-pdfbolt-signature"),
    secret=os.environ["PDFBOLT_WEBHOOK_SECRET"],
)

print(event.request_id)
print(event.status)
print(event.error_code)
print(event.document_url)
```

`verify_and_parse()` verifies the HMAC signature first and parses JSON only after the signature is valid. If you only need a boolean result, use `webhooks.verify_signature()`.

The SDK exposes webhook helpers through both `PDFBolt.webhooks` and the top-level `webhooks` export. Use whichever import style fits your codebase.

## Error Handling

The PDFBolt API returns one common error response shape. The SDK represents API error responses with one class: `PDFBoltAPIError`. Check `status_code` for HTTP-level handling and `error_code` for PDFBolt-specific causes.

```python
from pdfbolt import (
    PDFBoltAPIError,
    PDFBoltError,
    PDFBoltNetworkError,
    PDFBoltValidationError,
)

try:
    pdfbolt.direct.from_url(url="https://example.com")
except PDFBoltValidationError as error:
    print(error)
except PDFBoltAPIError as error:
    print(error.status_code)
    print(error.timestamp)
    print(error.error_code)
    print(error.error_message)
    print(error.rate_limit.minute.limit)
    print(error.rate_limit.minute.remaining)
    print(error.raw_body)

    if error.status_code == 401:
        print("Check your API key.")

    if error.error_code == "TOO_MANY_REQUESTS":
        print(error.rate_limit.minute.remaining)
except PDFBoltNetworkError as error:
    print(error)
except PDFBoltError:
    raise
```

`PDFBoltError` is the base class for all SDK errors. `PDFBoltAPIError` is thrown when the PDFBolt API returns an HTTP error response.

Exported error classes:

```python
PDFBoltError
PDFBoltAPIError
PDFBoltNetworkError
PDFBoltWebhookSignatureError
PDFBoltValidationError
PDFBoltConfigurationError
```

See [Error Handling](https://pdfbolt.com/docs/error-handling) for the full API error reference. These SDK-specific classes are worth calling out:

- `PDFBoltValidationError` is thrown before a request is sent when a high-level helper is called with missing or invalid SDK-side parameters.
- `PDFBoltConfigurationError` is thrown before a request is sent, for example when the API key is missing.
- `PDFBoltNetworkError` means the SDK did not receive a usable HTTP response, for example because of a network failure, timeout, or malformed success response.
- `PDFBoltWebhookSignatureError` is thrown by `verify_and_parse()` when the webhook signature or payload is invalid.

## Advanced Client Options

```python
import os
import requests

from pdfbolt import PDFBolt

session = requests.Session()

pdfbolt = PDFBolt(
    api_key=os.environ["PDFBOLT_API_KEY"],
    base_url="https://api.pdfbolt.com",
    request_timeout=120.0,
    session=session,
)
```

The SDK does not automatically retry failed requests. One SDK method call sends at most one HTTP request. For async conversion retries handled by PDFBolt, use the `retry_delays` conversion parameter.

`request_timeout` is the SDK HTTP timeout in seconds. The conversion `timeout` option is different: it is sent to the PDFBolt API and controls the browser render timeout for the PDF conversion.

The SDK sends `User-Agent: pdfbolt-python/<version>` on requests to the PDFBolt API. This helps identify SDK traffic for support and debugging. To set headers for the page being rendered by Chromium, use the conversion `extra_http_headers` parameter.

Common conversion options such as `format`, `margin`, `print_background`, `content_disposition`, `filename`, and `compression` use Pythonic snake_case names and are mapped to the REST API request fields. See [Conversion Parameters](https://pdfbolt.com/docs/parameters) for the full parameter reference.

## Usage

Use `pdfbolt.usage.get()` to read the current account plan, remaining conversion credits, and rate-limit metadata.

```python
usage = pdfbolt.usage.get()

print(usage.plan)
print(usage.recurring)
print(usage.one_time)
print(usage.rate_limit.day.remaining)
```

## SDK Reference

Main client methods:

```python
pdfbolt.direct.convert(...)
pdfbolt.direct.from_url(...)
pdfbolt.direct.from_html(...)
pdfbolt.direct.from_template(...)

pdfbolt.sync.convert(...)
pdfbolt.sync.from_url(...)
pdfbolt.sync.from_html(...)
pdfbolt.sync.from_template(...)

pdfbolt.async_conversions.convert(...)
pdfbolt.async_conversions.from_url(...)
pdfbolt.async_conversions.from_html(...)
pdfbolt.async_conversions.from_template(...)

pdfbolt.usage.get(...)
```

Webhook helpers:

```python
PDFBolt.webhooks.verify_signature(...)
PDFBolt.webhooks.verify_and_parse(...)

webhooks.verify_signature(...)
webhooks.verify_and_parse(...)
```

Common runtime exports:

```python
PDFBolt
DirectConversionResult
VERSION
Webhooks
webhooks
PDFBoltError
PDFBoltAPIError
PDFBoltNetworkError
PDFBoltWebhookSignatureError
PDFBoltValidationError
PDFBoltConfigurationError
```

Typed model exports include direct, sync, async job, webhook event, usage, and rate-limit result classes.

## Development

```bash
python -m pip install -e ".[dev]"
ruff check .
mypy src
pytest
python -m build
twine check dist/*
```

## Examples

Set your API key before running examples:

```bash
export PDFBOLT_API_KEY="your_api_key_here"
export PDFBOLT_BASE_URL="https://api.pdfbolt.com"
```

On Windows PowerShell:

```powershell
$env:PDFBOLT_API_KEY="your_api_key_here"
$env:PDFBOLT_BASE_URL="https://api.pdfbolt.com"
```

Run examples from the project root:

```bash
python examples/quick_start.py
python examples/convert_html.py
python examples/direct_base64.py
python examples/sync.py
python examples/error_classes.py
```

Optional examples:

```bash
export PDFBOLT_WEBHOOK_URL="https://your-app.com/webhooks/pdfbolt"
python examples/async_job.py

export PDFBOLT_CUSTOM_S3_PRESIGNED_URL="https://..."
python examples/sync.py

export PDFBOLT_TEMPLATE_ID="your_template_id"
export PDFBOLT_TEMPLATE_DATA_JSON='{"invoice_number":"PYTHON-SDK-001","total":"$123.00"}'
python examples/template.py
```

Webhook E2E:

```bash
export PDFBOLT_WEBHOOK_SECRET="your_webhook_signature_secret"
python examples/webhook_server.py
```

Expose `http://127.0.0.1:8787` through an HTTPS tunnel and use the public URL as `PDFBOLT_WEBHOOK_URL` before running `examples/async_job.py`.

## Live Tests

Live tests are skipped by default. To run them:

```bash
export PDFBOLT_RUN_LIVE_TESTS=1
export PDFBOLT_API_KEY="your_api_key_here"
export PDFBOLT_BASE_URL="https://api.pdfbolt.com"
python -m pytest tests/live
```

Optional live test inputs:

```bash
export PDFBOLT_WEBHOOK_URL="https://your-app.com/webhooks/pdfbolt"
export PDFBOLT_TEMPLATE_ID="your_template_id"
export PDFBOLT_TEMPLATE_DATA_JSON='{"invoice_number":"PYTHON-SDK-001","total":"$123.00"}'
export PDFBOLT_CUSTOM_S3_PRESIGNED_URL="https://..."
```
