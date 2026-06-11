from __future__ import annotations

import requests

from .http import DEFAULT_BASE_URL, DEFAULT_REQUEST_TIMEOUT_SECONDS, PDFBoltHttpClient
from .resources.async_conversions import AsyncConversionsResource
from .resources.direct import DirectResource
from .resources.sync import SyncResource
from .resources.usage import UsageResource
from .webhooks import Webhooks, webhooks


class PDFBolt:
    webhooks: Webhooks = webhooks

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        request_timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
        session: requests.Session | None = None,
    ) -> None:
        http = PDFBoltHttpClient(
            api_key=api_key,
            base_url=base_url,
            request_timeout=request_timeout,
            session=session,
        )

        self.direct = DirectResource(http)
        self.sync = SyncResource(http)
        self.async_conversions = AsyncConversionsResource(http)
        self.usage = UsageResource(http)
