from __future__ import annotations

import base64

from _common import OUTPUT_DIR, client, print_rate_limit

pdfbolt = client()

raw_html = """
<!doctype html>
<html>
  <body>
    <h1>PDFBolt Python SDK</h1>
    <p>This PDF was generated from raw HTML.</p>
  </body>
</html>
"""

print("from_html raw HTML")
pdf = pdfbolt.direct.from_html(
    html=raw_html,
    format="A4",
    print_background=True,
)
output = OUTPUT_DIR / "convert-html-from-html.pdf"
pdf.save(output)
print(f"PDF saved to {output}")
print(f"Buffer starts with: {pdf.buffer[:5].decode('latin1')}")
print(f"Size bytes: {pdf.size}")
print(f"Conversion cost: {pdf.conversion_cost}")
print_rate_limit(pdf.rate_limit)

print()
print("convert Base64 HTML")
pdf_from_base64 = pdfbolt.direct.convert(
    {
        "html": base64.b64encode(raw_html.encode("utf-8")).decode("ascii"),
        "format": "A4",
        "print_background": True,
    }
)
output = OUTPUT_DIR / "convert-html-base64-convert.pdf"
pdf_from_base64.save(output)
print(f"PDF saved to {output}")
print(f"Buffer starts with: {pdf_from_base64.buffer[:5].decode('latin1')}")
print(f"Size bytes: {pdf_from_base64.size}")
print(f"Conversion cost: {pdf_from_base64.conversion_cost}")
print_rate_limit(pdf_from_base64.rate_limit)
