from __future__ import annotations

from _common import OUTPUT_DIR, client, print_rate_limit

from pdfbolt import VERSION

pdfbolt = client()

pdf = pdfbolt.direct.from_url(
    url="https://example.com",
    print_background=True,
)

output = OUTPUT_DIR / "quick-start-example.pdf"
pdf.save(output)

print(f"Using PDFBolt Python SDK {VERSION}")
print(f"PDF saved to {output}")
print(f"Buffer starts with: {pdf.buffer[:5].decode('latin1')}")
print(f"Size bytes: {pdf.size}")
print(f"Base64 value: {pdf.base64}")
print(f"Content-Type: {pdf.content_type}")
print(f"Filename: {pdf.filename}")
print(f"Conversion cost: {pdf.conversion_cost}")
print_rate_limit(pdf.rate_limit)
