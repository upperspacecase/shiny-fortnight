"""Tests for trade executor."""

from prediction_market_bot.engine.executor import TradeExecutor
from prediction_market_bot.models.market import (
    ArbitrageOpportunity,
    Platform,
    Portfolio,
    TradeLeg,
)


def _make_opp(
    profit_pct: float = 5.0,
    total_cost: float = 100.0,
) -> ArbitrageOpportunity:
    legs = [
        TradeLeg(
            platform=Platform.POLYMARKET,
            market_id="1",
            market_question="Test?",
            outcome_name="Yes",
            price=0.45,
            quantity=110.0,
        ),
        TradeLeg(
            platform=Platform.POLYMARKET,
            market_id="1",
            market_question="Test?",
            outcome_name="No",
            price=0.50,
            quantity=100.0,
        ),
    ]
    return ArbitrageOpportunity(
        description="Test arb",
        profit_pct=profit_pct,
        legs=legs,
        total_cost=total_cost,
        guaranteed_payout=total_cost * (1 + profit_pct / 100),
    )


class TestTradeExecutor:
    def test_dry_run_execution(self):
        portfolio = Portfolio(cash=1000.0)
        executor = TradeExecutor(portfolio, dry_run=True)
        opp = _make_opp()

        result = executor.execute_arbitrage(opp)
        assert result.success
        assert "[DRY RUN]" in result.message
        assert portfolio.cash == 900.0

    def test_rejects_when_insufficient_cash(self):
        portfolio = Portfolio(cash=50.0)
        executor = TradeExecutor(portfolio, dry_run=True)
        opp = _make_opp(total_cost=100.0)

        result = executor.execute_arbitrage(opp)
        assert not result.success
        assert "Insufficient cash" in result.message

    def test_rejects_when_exceeds_position_size(self):
        portfolio = Portfolio(cash=1000.0)
        executor = TradeExecutor(portfolio, max_position_size=50.0, dry_run=True)
        opp = _make_opp(total_cost=100.0)

        result = executor.execute_arbitrage(opp)
        assert not result.success
        assert "Position size" in result.message

    def test_rejects_thin_profit(self):
        portfolio = Portfolio(cash=1000.0)
        executor = TradeExecutor(portfolio, dry_run=True)
        opp = _make_opp(profit_pct=0.05)

        result = executor.execute_arbitrage(opp)
        assert not result.success
        assert "too thin" in result.message.lower()

    def test_portfolio_risk_limit(self):
        portfolio = Portfolio(cash=500.0, total_invested=400.0)
        executor = TradeExecutor(
            portfolio, max_portfolio_risk=0.5, dry_run=True
        )
        opp = _make_opp(total_cost=100.0)

        result = executor.execute_arbitrage(opp)
        assert not result.success
        assert "risk limit" in result.message.lower()

    def test_summary(self):
        portfolio = Portfolio(cash=1000.0)
        executor = TradeExecutor(portfolio, dry_run=True)
        opp = _make_opp()

        executor.execute_arbitrage(opp)
        summary = executor.summary()

        assert summary["trades_attempted"] == 1
        assert summary["trades_executed"] == 1
        assert summary["cash_remaining"] == 900.0
