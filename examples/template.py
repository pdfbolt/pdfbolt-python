from __future__ import annotations

import json
import os

from _common import OUTPUT_DIR, client, print_rate_limit, required_env, template_data

pdfbolt = client()
template_id = required_env("PDFBOLT_TEMPLATE_ID")
data = json.loads(os.environ.get("PDFBOLT_TEMPLATE_DATA_JSON", "null")) or template_data()

print("Direct template conversion")
pdf = pdfbolt.direct.from_template(
    template_id=template_id,
    template_data=data,
)
output = OUTPUT_DIR / "template-direct.pdf"
pdf.save(output)
print(f"PDF saved to {output}")
print(f"Size bytes: {pdf.size}")
print(f"Conversion cost: {pdf.conversion_cost}")
print_rate_limit(pdf.rate_limit)

print()
print("Sync template conversion")
sync_result = pdfbolt.sync.from_template(
    template_id=template_id,
    template_data=data,
)
print(f"Request ID: {sync_result.request_id}")
print(f"Status: {sync_result.status}")
print(f"Document URL: {sync_result.document_url}")
print(f"Conversion cost: {sync_result.conversion_cost}")
print_rate_limit(sync_result.rate_limit)
