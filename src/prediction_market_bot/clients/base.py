"""Base client with shared HTTP logic."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import httpx

from prediction_market_bot.models.market import Market

logger = logging.getLogger(__name__)


class BaseClient(ABC):
    """Abstract base for prediction market API clients."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers={"Accept": "application/json"},
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> BaseClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    @abstractmethod
    async def fetch_active_markets(self, limit: int = 100) -> list[Market]:
        """Fetch currently active/open markets from this platform."""
        ...
