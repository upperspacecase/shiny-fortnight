"""Tests for arbitrage detection engine."""

from prediction_market_bot.engine.arbitrage import (
    _normalize_question,
    find_cross_market_arbs,
    find_intra_market_arbs,
    match_cross_platform_markets,
)
from prediction_market_bot.models.market import (
    CrossMarketPair,
    Market,
    MarketStatus,
    Outcome,
    Platform,
)


def _make_market(
    id: str,
    platform: Platform,
    question: str,
    yes_price: float,
    no_price: float,
) -> Market:
    return Market(
        id=id,
        platform=platform,
        question=question,
        outcomes=[
            Outcome(name="Yes", price=yes_price),
            Outcome(name="No", price=no_price),
        ],
        status=MarketStatus.OPEN,
    )


class TestIntraMarketArb:
    def test_finds_arb_when_underround(self):
        m = _make_market("1", Platform.POLYMARKET, "Test?", 0.45, 0.50)
        arbs = find_intra_market_arbs([m], min_profit_pct=0.1)
        assert len(arbs) == 1
        assert arbs[0].profit_pct > 5.0

    def test_no_arb_when_overround(self):
        m = _make_market("2", Platform.POLYMARKET, "Test?", 0.55, 0.50)
        arbs = find_intra_market_arbs([m])
        assert len(arbs) == 0

    def test_no_arb_when_exact_one(self):
        m = _make_market("3", Platform.KALSHI, "Test?", 0.50, 0.50)
        arbs = find_intra_market_arbs([m])
        assert len(arbs) == 0

    def test_filters_by_min_profit(self):
        # Overround = 0.999, profit ~0.1% — below 0.5% threshold
        m = _make_market("4", Platform.POLYMARKET, "Test?", 0.499, 0.500)
        arbs = find_intra_market_arbs([m], min_profit_pct=0.5)
        assert len(arbs) == 0

    def test_multi_outcome_arb(self):
        m = Market(
            id="5",
            platform=Platform.POLYMARKET,
            question="Who wins the election?",
            outcomes=[
                Outcome(name="Alice", price=0.30),
                Outcome(name="Bob", price=0.30),
                Outcome(name="Charlie", price=0.30),
            ],
            status=MarketStatus.OPEN,
        )
        arbs = find_intra_market_arbs([m], min_profit_pct=0.1)
        assert len(arbs) == 1
        assert arbs[0].profit_pct > 10.0


class TestCrossMarketArb:
    def test_finds_cross_arb(self):
        m_a = _make_market("a1", Platform.POLYMARKET, "Will X happen?", 0.55, 0.50)
        m_b = _make_market("b1", Platform.KALSHI, "Will X happen?", 0.60, 0.35)

        pair = CrossMarketPair(market_a=m_a, market_b=m_b, similarity_score=0.95)
        arbs = find_cross_market_arbs([pair], min_profit_pct=0.1)

        # Best YES = 0.55 (A), Best NO = 0.35 (B) -> total = 0.90 -> ~11% profit
        assert len(arbs) == 1
        assert arbs[0].profit_pct > 10.0

    def test_no_cross_arb_when_prices_sum_above_one(self):
        m_a = _make_market("a2", Platform.POLYMARKET, "Test?", 0.60, 0.50)
        m_b = _make_market("b2", Platform.KALSHI, "Test?", 0.55, 0.55)

        pair = CrossMarketPair(market_a=m_a, market_b=m_b, similarity_score=0.90)
        arbs = find_cross_market_arbs([pair])
        assert len(arbs) == 0


class TestMarketMatching:
    def test_matches_similar_questions(self):
        poly = [_make_market("p1", Platform.POLYMARKET, "Will Bitcoin reach $100k?", 0.60, 0.45)]
        kalshi = [_make_market("k1", Platform.KALSHI, "Will Bitcoin reach $100k?", 0.55, 0.50)]

        pairs = match_cross_platform_markets(poly, kalshi, min_similarity=0.5)
        assert len(pairs) == 1
        assert pairs[0].similarity_score > 0.8

    def test_no_match_for_dissimilar_questions(self):
        poly = [_make_market("p2", Platform.POLYMARKET, "Will it rain tomorrow?", 0.60, 0.45)]
        kalshi = [_make_market("k2", Platform.KALSHI, "Who will win the Super Bowl?", 0.55, 0.50)]

        pairs = match_cross_platform_markets(poly, kalshi, min_similarity=0.65)
        assert len(pairs) == 0


class TestNormalizeQuestion:
    def test_removes_noise(self):
        assert _normalize_question("Will it rain?") == "it rain"

    def test_lowercases(self):
        assert _normalize_question("BITCOIN") == "bitcoin"
