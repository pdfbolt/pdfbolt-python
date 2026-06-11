# Changelog

## 1.0.0 - 2026-06-11

Initial release of the official PDFBolt Python SDK.

### Added

- Direct PDF generation from HTTPS URLs, raw HTML, and published templates.
- Sync conversion jobs returning temporary PDF URLs.
- Async conversion jobs with webhook delivery.
- Custom S3 presigned URL support for sync and async conversions.
- Usage API support.
- Webhook signature verification helpers.
- Typed result models for direct, sync, async, webhook, usage, and rate-limit responses.
- SDK error classes for API, network, validation, configuration, and webhook signature failures.
- ESM-style Python package metadata with `py.typed` for type-aware users and tools.
- Local unit tests, optional live integration tests, examples, and GitHub CI.
