"""Tests for market data models."""

from prediction_market_bot.models.market import (
    Market,
    MarketStatus,
    Outcome,
    Platform,
    Portfolio,
    TradeLeg,
)


def test_outcome_implied_probability():
    o = Outcome(name="Yes", price=0.65)
    assert o.implied_probability == 0.65


def test_market_overround_normal():
    m = Market(
        id="1",
        platform=Platform.POLYMARKET,
        question="Will it rain?",
        outcomes=[
            Outcome(name="Yes", price=0.55),
            Outcome(name="No", price=0.50),
        ],
    )
    assert m.overround == 1.05
    assert not m.has_intra_arb


def test_market_has_intra_arb():
    m = Market(
        id="2",
        platform=Platform.POLYMARKET,
        question="Who wins?",
        outcomes=[
            Outcome(name="Yes", price=0.45),
            Outcome(name="No", price=0.50),
        ],
    )
    assert m.overround == 0.95
    assert m.has_intra_arb
    # Profit = (1/0.95 - 1) * 100 ≈ 5.26%
    assert abs(m.intra_arb_profit_pct - 5.26) < 0.1


def test_market_no_arb_when_single_outcome():
    m = Market(
        id="3",
        platform=Platform.KALSHI,
        question="Test?",
        outcomes=[Outcome(name="Yes", price=0.5)],
    )
    assert not m.has_intra_arb


def test_market_intra_arb_profit_zero_when_no_arb():
    m = Market(
        id="4",
        platform=Platform.KALSHI,
        question="Test?",
        outcomes=[
            Outcome(name="Yes", price=0.60),
            Outcome(name="No", price=0.50),
        ],
    )
    assert m.intra_arb_profit_pct == 0.0


def test_portfolio_record_trade():
    p = Portfolio(cash=1000.0)
    legs = [
        TradeLeg(
            platform=Platform.POLYMARKET,
            market_id="1",
            market_question="Test",
            outcome_name="Yes",
            price=0.50,
            quantity=100.0,
        )
    ]
    p.record_trade(legs, cost=50.0)
    assert p.cash == 950.0
    assert p.total_invested == 50.0
    assert len(p.positions) == 1
