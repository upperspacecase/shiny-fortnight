"""Polymarket CLOB API client.

Polymarket uses a Central Limit Order Book (CLOB) with binary outcome tokens.
Docs: https://docs.polymarket.com/
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from prediction_market_bot.clients.base import BaseClient
from prediction_market_bot.models.market import Market, MarketStatus, Outcome, Platform

logger = logging.getLogger(__name__)

GAMMA_API_BASE = "https://gamma-api.polymarket.com"


class PolymarketClient(BaseClient):
    """Client for the Polymarket Gamma (public) API."""

    def __init__(self) -> None:
        super().__init__(base_url=GAMMA_API_BASE)

    async def fetch_active_markets(self, limit: int = 100) -> list[Market]:
        """Fetch active markets from Polymarket's Gamma API."""
        markets: list[Market] = []
        try:
            resp = await self._client.get(
                "/markets",
                params={
                    "limit": limit,
                    "active": "true",
                    "closed": "false",
                    "order": "volume24hr",
                    "ascending": "false",
                },
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            logger.exception("Failed to fetch Polymarket markets")
            return markets

        for item in data:
            try:
                market = self._parse_market(item)
                if market and market.status == MarketStatus.OPEN:
                    markets.append(market)
            except Exception:
                logger.debug("Skipping unparseable market: %s", item.get("id", "?"))

        logger.info("Fetched %d active Polymarket markets", len(markets))
        return markets

    def _parse_market(self, data: dict) -> Market | None:
        outcomes_raw = data.get("outcomes", "")
        prices_raw = data.get("outcomePrices", "")

        if isinstance(outcomes_raw, str):
            # Gamma API returns JSON-encoded strings
            import json

            try:
                outcome_names = json.loads(outcomes_raw)
                outcome_prices = json.loads(prices_raw)
            except (json.JSONDecodeError, TypeError):
                return None
        elif isinstance(outcomes_raw, list):
            outcome_names = outcomes_raw
            outcome_prices = prices_raw if isinstance(prices_raw, list) else []
        else:
            return None

        if not outcome_names or not outcome_prices:
            return None

        if len(outcome_names) != len(outcome_prices):
            return None

        outcomes = []
        for name, price in zip(outcome_names, outcome_prices):
            try:
                outcomes.append(Outcome(name=str(name), price=float(price)))
            except (ValueError, TypeError):
                return None

        end_date = None
        if data.get("endDate"):
            try:
                end_date = datetime.fromisoformat(
                    data["endDate"].replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                pass

        clobTokenIds = data.get("clobTokenIds", "")
        if isinstance(clobTokenIds, str):
            import json

            try:
                token_ids = json.loads(clobTokenIds)
            except (json.JSONDecodeError, TypeError):
                token_ids = []
        else:
            token_ids = clobTokenIds or []

        # Attach token IDs to outcomes
        if token_ids and len(token_ids) == len(outcomes):
            outcomes = [
                Outcome(name=o.name, price=o.price, token_id=tid)
                for o, tid in zip(outcomes, token_ids)
            ]

        return Market(
            id=str(data.get("id", "")),
            platform=Platform.POLYMARKET,
            question=data.get("question", ""),
            outcomes=outcomes,
            status=MarketStatus.OPEN,
            volume=float(data.get("volume", 0) or 0),
            liquidity=float(data.get("liquidity", 0) or 0),
            end_date=end_date,
            url=f"https://polymarket.com/event/{data.get('slug', '')}",
            category=data.get("category", ""),
        )
