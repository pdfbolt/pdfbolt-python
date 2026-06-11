from __future__ import annotations

from _common import OUTPUT_DIR, client, print_rate_limit

pdfbolt = client()

pdf = pdfbolt.direct.from_url(
    url="https://example.com",
    is_encoded=True,
)

output = OUTPUT_DIR / "direct-base64-response.pdf"
pdf.save(output)

print(f"PDF saved to {output}")
print(f"Buffer starts with: {pdf.buffer[:5].decode('latin1')}")
print(f"Size bytes: {pdf.size}")
print(f"Base64 value type: {type(pdf.base64).__name__}")
print(f"Base64 starts with: {pdf.base64[:32] if pdf.base64 else None}")
print(f"Base64 matches decoded buffer: {pdf.base64 is not None}")
print(f"Content-Type: {pdf.content_type}")
print(f"Conversion cost: {pdf.conversion_cost}")
print_rate_limit(pdf.rate_limit)
