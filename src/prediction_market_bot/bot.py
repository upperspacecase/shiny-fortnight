"""Main bot orchestrator — ties together clients, analysis, and execution."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from prediction_market_bot.clients.kalshi import KalshiClient
from prediction_market_bot.clients.polymarket import PolymarketClient
from prediction_market_bot.config import BotConfig
from prediction_market_bot.engine.analyzer import MarketAnalysis, rank_markets
from prediction_market_bot.engine.arbitrage import (
    find_cross_market_arbs,
    find_intra_market_arbs,
    match_cross_platform_markets,
)
from prediction_market_bot.engine.executor import TradeExecutor
from prediction_market_bot.models.market import ArbitrageOpportunity, Market, Portfolio
from prediction_market_bot.sample_data import (
    get_sample_kalshi_markets,
    get_sample_polymarket_markets,
)

logger = logging.getLogger(__name__)


class PredictionMarketBot:
    """Main bot that scans markets, finds arbitrage, and executes trades."""

    def __init__(self, config: BotConfig) -> None:
        self.config = config
        self.portfolio = Portfolio(cash=config.starting_cash)
        self.executor = TradeExecutor(
            portfolio=self.portfolio,
            max_position_size=config.max_position_size,
            max_portfolio_risk=config.max_portfolio_risk,
            dry_run=config.dry_run,
        )
        self._all_opportunities: list[ArbitrageOpportunity] = []
        self._all_analyses: list[MarketAnalysis] = []

    async def scan_once(self) -> ScanResult:
        """Run a single scan cycle across all enabled platforms."""
        logger.info("Starting market scan at %s", datetime.utcnow().isoformat())

        # Fetch markets from all enabled platforms
        poly_markets: list[Market] = []
        kalshi_markets: list[Market] = []

        if self.config.demo:
            logger.info("Using sample market data (demo mode)")
            if self.config.enable_polymarket:
                poly_markets = get_sample_polymarket_markets()
            if self.config.enable_kalshi:
                kalshi_markets = get_sample_kalshi_markets()
        else:
            tasks = []
            if self.config.enable_polymarket:
                tasks.append(("polymarket", self._fetch_polymarket()))
            if self.config.enable_kalshi:
                tasks.append(("kalshi", self._fetch_kalshi()))

            for name, coro in tasks:
                try:
                    result = await coro
                    if name == "polymarket":
                        poly_markets = result
                    else:
                        kalshi_markets = result
                except Exception:
                    logger.exception("Failed to fetch from %s", name)

        all_markets = poly_markets + kalshi_markets
        logger.info(
            "Fetched %d markets total (Polymarket: %d, Kalshi: %d)",
            len(all_markets),
            len(poly_markets),
            len(kalshi_markets),
        )

        # 1. Intra-market arbitrage
        intra_arbs = find_intra_market_arbs(
            all_markets, min_profit_pct=self.config.min_profit_pct
        )

        # 2. Cross-market arbitrage
        cross_arbs: list[ArbitrageOpportunity] = []
        if poly_markets and kalshi_markets:
            pairs = match_cross_platform_markets(
                poly_markets,
                kalshi_markets,
                min_similarity=self.config.min_similarity,
            )
            cross_arbs = find_cross_market_arbs(
                pairs, min_profit_pct=self.config.min_profit_pct
            )

        all_opps = intra_arbs + cross_arbs
        all_opps.sort(key=lambda o: o.profit_pct, reverse=True)

        # 3. Analyze top markets for mispricing signals
        analyses = rank_markets(all_markets)

        # 4. Execute top arbitrage opportunities
        executed = []
        for opp in all_opps:
            result = self.executor.execute_arbitrage(opp)
            if result.success:
                executed.append(opp)

        self._all_opportunities.extend(all_opps)
        self._all_analyses = analyses

        scan_result = ScanResult(
            markets_scanned=len(all_markets),
            intra_arbs_found=len(intra_arbs),
            cross_arbs_found=len(cross_arbs),
            trades_executed=len(executed),
            opportunities=all_opps,
            top_analyses=analyses[:20],
        )

        logger.info(
            "Scan complete: %d markets, %d intra-arbs, %d cross-arbs, %d trades",
            scan_result.markets_scanned,
            scan_result.intra_arbs_found,
            scan_result.cross_arbs_found,
            scan_result.trades_executed,
        )

        return scan_result

    async def run_loop(self) -> None:
        """Run the bot in a continuous loop."""
        logger.info("Bot starting in %s mode", "DRY-RUN" if self.config.dry_run else "LIVE")
        logger.info("Starting cash: $%.2f", self.config.starting_cash)
        logger.info("Scan interval: %ds", self.config.scan_interval_seconds)

        while True:
            try:
                await self.scan_once()
            except Exception:
                logger.exception("Error during scan cycle")

            logger.info(
                "Next scan in %d seconds...", self.config.scan_interval_seconds
            )
            await asyncio.sleep(self.config.scan_interval_seconds)

    async def _fetch_polymarket(self) -> list[Market]:
        async with PolymarketClient() as client:
            return await client.fetch_active_markets(
                limit=self.config.markets_per_platform
            )

    async def _fetch_kalshi(self) -> list[Market]:
        async with KalshiClient() as client:
            return await client.fetch_active_markets(
                limit=self.config.markets_per_platform
            )


class ScanResult:
    """Results from a single scan cycle."""

    def __init__(
        self,
        markets_scanned: int,
        intra_arbs_found: int,
        cross_arbs_found: int,
        trades_executed: int,
        opportunities: list[ArbitrageOpportunity],
        top_analyses: list[MarketAnalysis],
    ) -> None:
        self.markets_scanned = markets_scanned
        self.intra_arbs_found = intra_arbs_found
        self.cross_arbs_found = cross_arbs_found
        self.trades_executed = trades_executed
        self.opportunities = opportunities
        self.top_analyses = top_analyses
