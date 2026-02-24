"""Trade execution engine.

Handles position sizing, risk checks, and trade simulation.
By default runs in DRY-RUN mode — logs intended trades without executing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from prediction_market_bot.models.market import ArbitrageOpportunity, Portfolio, TradeLeg

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of attempting to execute a trade."""

    success: bool
    message: str
    legs_executed: list[TradeLeg]
    cost: float = 0.0


class TradeExecutor:
    """Manages trade execution and portfolio tracking."""

    def __init__(
        self,
        portfolio: Portfolio,
        max_position_size: float = 200.0,
        max_portfolio_risk: float = 0.5,
        dry_run: bool = True,
    ) -> None:
        self.portfolio = portfolio
        self.max_position_size = max_position_size
        self.max_portfolio_risk = max_portfolio_risk
        self.dry_run = dry_run
        self._execution_log: list[ExecutionResult] = []

    def execute_arbitrage(self, opp: ArbitrageOpportunity) -> ExecutionResult:
        """Execute an arbitrage opportunity (or simulate in dry-run mode)."""
        # Pre-trade risk checks
        rejection = self._check_risk(opp)
        if rejection:
            result = ExecutionResult(
                success=False,
                message=rejection,
                legs_executed=[],
            )
            self._execution_log.append(result)
            return result

        if self.dry_run:
            return self._simulate_execution(opp)

        return self._live_execution(opp)

    def _check_risk(self, opp: ArbitrageOpportunity) -> str | None:
        """Return rejection reason, or None if trade passes risk checks."""
        if opp.total_cost > self.max_position_size:
            return (
                f"Position size ${opp.total_cost:.2f} exceeds "
                f"max ${self.max_position_size:.2f}"
            )

        if opp.total_cost > self.portfolio.cash:
            return (
                f"Insufficient cash: need ${opp.total_cost:.2f}, "
                f"have ${self.portfolio.cash:.2f}"
            )

        portfolio_exposure = self.portfolio.total_invested + opp.total_cost
        initial_capital = self.portfolio.cash + self.portfolio.total_invested
        if initial_capital > 0 and portfolio_exposure / initial_capital > self.max_portfolio_risk:
            return (
                f"Portfolio risk limit: exposure would be "
                f"{portfolio_exposure / initial_capital:.1%} "
                f"(max {self.max_portfolio_risk:.1%})"
            )

        if opp.profit_pct < 0.1:
            return f"Profit too thin ({opp.profit_pct:.3f}%) — not worth execution risk"

        return None

    def _simulate_execution(self, opp: ArbitrageOpportunity) -> ExecutionResult:
        """Simulate trade execution in dry-run mode."""
        logger.info("[DRY RUN] Would execute: %s", opp.description)
        for leg in opp.legs:
            logger.info(
                "  [DRY RUN] %s %s @ $%.4f on %s (%s)",
                "BUY",
                leg.outcome_name,
                leg.price,
                leg.platform.value,
                leg.market_question[:40],
            )

        # Track in portfolio even in dry-run for simulation purposes
        self.portfolio.record_trade(opp.legs, opp.total_cost)

        result = ExecutionResult(
            success=True,
            message=f"[DRY RUN] Simulated: {opp.description}",
            legs_executed=opp.legs,
            cost=opp.total_cost,
        )
        self._execution_log.append(result)
        return result

    def _live_execution(self, opp: ArbitrageOpportunity) -> ExecutionResult:
        """Execute trades on live platforms.

        NOTE: This requires API keys and authenticated sessions with each
        platform. Currently not implemented — use dry_run=True.
        """
        logger.warning(
            "Live execution not implemented. "
            "Requires authenticated API sessions with each platform. "
            "Falling back to dry-run."
        )
        return self._simulate_execution(opp)

    @property
    def execution_log(self) -> list[ExecutionResult]:
        return list(self._execution_log)

    def summary(self) -> dict:
        """Return a summary of execution activity."""
        executed = [r for r in self._execution_log if r.success]
        total_cost = sum(r.cost for r in executed)
        return {
            "trades_attempted": len(self._execution_log),
            "trades_executed": len(executed),
            "total_invested": total_cost,
            "cash_remaining": self.portfolio.cash,
            "positions": len(self.portfolio.positions),
        }
