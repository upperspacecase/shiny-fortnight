"""Tests for market analyzer."""

from prediction_market_bot.engine.analyzer import analyze_market, rank_markets
from prediction_market_bot.models.market import Market, MarketStatus, Outcome, Platform


def _make_market(
    yes_price: float,
    no_price: float,
    liquidity: float = 50000.0,
    extra_outcomes: list[Outcome] | None = None,
) -> Market:
    outcomes = [
        Outcome(name="Yes", price=yes_price),
        Outcome(name="No", price=no_price),
    ]
    if extra_outcomes:
        outcomes.extend(extra_outcomes)
    return Market(
        id="test",
        platform=Platform.POLYMARKET,
        question="Test market?",
        outcomes=outcomes,
        status=MarketStatus.OPEN,
        liquidity=liquidity,
    )


class TestAnalyzeMarket:
    def test_underround_detected(self):
        m = _make_market(0.45, 0.50)
        result = analyze_market(m)
        assert result.mispricing_score >= 50
        assert result.edge_estimate_pct > 0
        assert any("arb" in n.lower() for n in result.notes)

    def test_tight_overround(self):
        m = _make_market(0.50, 0.505)
        result = analyze_market(m)
        assert result.mispricing_score >= 20

    def test_longshot_bias_detected(self):
        m = _make_market(0.03, 0.97)
        result = analyze_market(m)
        assert any("longshot" in n.lower() for n in result.notes)

    def test_low_liquidity_flagged(self):
        m = _make_market(0.50, 0.55, liquidity=1000.0)
        result = analyze_market(m)
        assert any("liquidity" in n.lower() for n in result.notes)

    def test_multi_outcome_flagged(self):
        m = _make_market(
            0.30,
            0.30,
            extra_outcomes=[Outcome(name="Draw", price=0.30)],
        )
        result = analyze_market(m)
        assert any("multi-way" in n.lower() for n in result.notes)


class TestRankMarkets:
    def test_ranks_by_mispricing_score(self):
        markets = [
            _make_market(0.50, 0.55),  # normal, low score
            _make_market(0.45, 0.50),  # underround, high score
            _make_market(0.03, 0.97, liquidity=1000.0),  # longshot + low liq
        ]
        ranked = rank_markets(markets)
        assert ranked[0].mispricing_score >= ranked[1].mispricing_score
        assert ranked[1].mispricing_score >= ranked[2].mispricing_score
