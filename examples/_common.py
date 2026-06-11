from __future__ import annotations

import os
from pathlib import Path

from pdfbolt import PDFBolt

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def client() -> PDFBolt:
    return PDFBolt(
        api_key=required_env("PDFBOLT_API_KEY"),
        base_url=os.environ.get("PDFBOLT_BASE_URL", "https://api.pdfbolt.com"),
    )


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Set {name} before running this example.")
    return value


def template_data() -> dict[str, object]:
    return {
        "invoice_number": "PYTHON-SDK-001",
        "customer_name": "Acme Inc.",
        "total": "$123.00",
    }


def print_rate_limit(rate_limit: object) -> None:
    minute = rate_limit.minute
    print(f"Minute limit: {minute.limit}")
    print(f"Minute remaining: {minute.remaining}")
