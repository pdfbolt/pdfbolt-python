from __future__ import annotations

import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import BinaryIO

from pdfbolt import PDFBoltWebhookSignatureError, webhooks

HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "8787"))
SECRET = os.environ.get("PDFBOLT_WEBHOOK_SECRET")


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        try:
            raw_body = self._read_raw_body()
        except ValueError as error:
            print(f"Invalid webhook request body: {error}")
            self.send_response(400)
            self.end_headers()
            return

        signature = self.headers.get("x-pdfbolt-signature")

        try:
            if SECRET:
                event = webhooks.verify_and_parse(
                    raw_body=raw_body,
                    signature=signature,
                    secret=SECRET,
                )
                print("Verified PDFBolt webhook")
            else:
                print("Received unverified PDFBolt webhook")
                print("Set PDFBOLT_WEBHOOK_SECRET to verify signatures.")
                print(raw_body.decode("utf-8", errors="replace"))
                self.send_response(200)
                self.end_headers()
                return
        except PDFBoltWebhookSignatureError:
            if SECRET:
                print("Invalid PDFBolt webhook signature")
                self.send_response(400)
                self.end_headers()
                return

            print(raw_body.decode("utf-8", errors="replace"))
            self.send_response(200)
            self.end_headers()
            return

        print(f"Request ID: {event.request_id}")
        print(f"Status: {event.status}")
        print(f"Error code: {event.error_code}")
        print(f"Error message: {event.error_message}")
        print(f"Document URL: {event.document_url}")
        print(f"Expires at: {event.expires_at}")
        print(f"Duration ms: {event.duration}")
        print(f"Document size MB: {event.document_size_mb}")
        print(f"Custom S3 bucket: {event.is_custom_s3_bucket}")

        self.send_response(200)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return

    def _read_raw_body(self) -> bytes:
        if self.headers.get("transfer-encoding", "").lower() == "chunked":
            return self._read_chunked_body()

        content_length = int(self.headers.get("content-length", "0"))
        return self.rfile.read(content_length)

    def _read_chunked_body(self) -> bytes:
        return _read_chunked_body(self.rfile)


def _read_chunked_body(rfile: BinaryIO) -> bytes:
    body = bytearray()

    while True:
        size_line = rfile.readline()
        if size_line == b"":
            raise ValueError("unexpected EOF while reading chunk size")

        size_token = size_line.strip().split(b";", 1)[0]
        if not size_token:
            raise ValueError("empty chunk size")

        try:
            chunk_size = int(size_token, 16)
        except ValueError as error:
            raise ValueError("invalid chunk size") from error

        if chunk_size == 0:
            _consume_chunk_trailers(rfile)
            return bytes(body)

        chunk = rfile.read(chunk_size)
        if len(chunk) != chunk_size:
            raise ValueError("unexpected EOF while reading chunk body")

        terminator = rfile.read(2)
        if terminator != b"\r\n":
            raise ValueError("invalid chunk terminator")

        body.extend(chunk)


def _consume_chunk_trailers(rfile: BinaryIO) -> None:
    while True:
        trailer_line = rfile.readline()
        if trailer_line == b"":
            raise ValueError("unexpected EOF while reading chunk trailers")
        if trailer_line in (b"\r\n", b"\n"):
            return


def main() -> None:
    server = HTTPServer((HOST, PORT), WebhookHandler)
    print(f"PDFBolt webhook server listening on http://{HOST}:{PORT}")
    print(
        "Expose this server through an HTTPS tunnel "
        "and use that public URL as PDFBOLT_WEBHOOK_URL."
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
