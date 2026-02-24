"""Kalshi API client.

Kalshi is a CFTC-regulated prediction market exchange.
Docs: https://trading-api.readme.io/reference
"""

from __future__ import annotations

import logging
from datetime import datetime

from prediction_market_bot.clients.base import BaseClient
from prediction_market_bot.models.market import Market, MarketStatus, Outcome, Platform

logger = logging.getLogger(__name__)

KALSHI_API_BASE = "https://api.elections.kalshi.com/trade-api/v2"


class KalshiClient(BaseClient):
    """Client for Kalshi's public trading API."""

    def __init__(self, api_base: str = KALSHI_API_BASE) -> None:
        super().__init__(base_url=api_base)

    async def fetch_active_markets(self, limit: int = 100) -> list[Market]:
        """Fetch active markets from Kalshi."""
        markets: list[Market] = []
        try:
            resp = await self._client.get(
                "/markets",
                params={
                    "limit": limit,
                    "status": "open",
                },
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            logger.exception("Failed to fetch Kalshi markets")
            return markets

        for item in data.get("markets", []):
            try:
                market = self._parse_market(item)
                if market and market.status == MarketStatus.OPEN:
                    markets.append(market)
            except Exception:
                logger.debug("Skipping unparseable market: %s", item.get("ticker", "?"))

        logger.info("Fetched %d active Kalshi markets", len(markets))
        return markets

    def _parse_market(self, data: dict) -> Market | None:
        yes_price = data.get("yes_bid") or data.get("last_price")
        if yes_price is None:
            return None

        # Kalshi prices are in cents (0-100)
        yes_price_normalized = float(yes_price) / 100.0
        no_price_normalized = 1.0 - yes_price_normalized

        # Check for explicit no_bid which may differ from 1 - yes_bid
        no_bid = data.get("no_bid")
        if no_bid is not None:
            no_price_normalized = float(no_bid) / 100.0

        outcomes = [
            Outcome(name="Yes", price=yes_price_normalized),
            Outcome(name="No", price=no_price_normalized),
        ]

        end_date = None
        if data.get("close_time"):
            try:
                end_date = datetime.fromisoformat(
                    data["close_time"].replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                pass

        ticker = data.get("ticker", "")
        return Market(
            id=ticker,
            platform=Platform.KALSHI,
            question=data.get("title", ""),
            outcomes=outcomes,
            status=MarketStatus.OPEN,
            volume=float(data.get("volume", 0) or 0),
            liquidity=float(data.get("open_interest", 0) or 0),
            end_date=end_date,
            url=f"https://kalshi.com/markets/{ticker}",
            category=data.get("category", ""),
        )
