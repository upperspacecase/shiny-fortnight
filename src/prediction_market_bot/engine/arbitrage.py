"""Arbitrage detection engine.

Two main strategies for guaranteed profit in prediction markets:

1. INTRA-MARKET ARBITRAGE:
   If a market's YES + NO prices sum to < $1.00, you can buy both sides
   and guarantee a $1.00 payout for less than $1.00 invested.
   Example: YES = $0.45, NO = $0.50 -> cost $0.95, payout $1.00, profit $0.05

2. CROSS-MARKET ARBITRAGE:
   If two platforms price the same event differently, buy the cheaper side
   on each platform.
   Example:
     Platform A: "Will X happen?" YES = $0.60
     Platform B: "Will X happen?" NO  = $0.35
     Cost: $0.95, one side guaranteed to pay $1.00 -> profit $0.05
"""

from __future__ import annotations

import logging
from difflib import SequenceMatcher

from prediction_market_bot.models.market import (
    ArbitrageOpportunity,
    CrossMarketPair,
    Market,
    TradeLeg,
)

logger = logging.getLogger(__name__)

# Minimum profit percentage to flag as an opportunity
MIN_PROFIT_PCT = 0.5
# Minimum text similarity to consider two markets as equivalent
MIN_SIMILARITY = 0.65
# Default trade size in dollars
DEFAULT_TRADE_SIZE = 100.0


def find_intra_market_arbs(
    markets: list[Market],
    min_profit_pct: float = MIN_PROFIT_PCT,
) -> list[ArbitrageOpportunity]:
    """Find markets where buying all outcomes costs less than $1.

    This is the simplest form of guaranteed profit: if the sum of all outcome
    prices is < 1.0, you buy every outcome and are guaranteed one of them
    pays out $1.00.
    """
    opportunities: list[ArbitrageOpportunity] = []

    for market in markets:
        if not market.has_intra_arb:
            continue
        if market.intra_arb_profit_pct < min_profit_pct:
            continue

        overround = market.overround
        trade_size = DEFAULT_TRADE_SIZE
        # Buy equal notional on each outcome
        quantity_per_outcome = trade_size / len(market.outcomes)

        legs = [
            TradeLeg(
                platform=market.platform,
                market_id=market.id,
                market_question=market.question,
                outcome_name=outcome.name,
                price=outcome.price,
                quantity=quantity_per_outcome / outcome.price,  # shares
                url=market.url,
            )
            for outcome in market.outcomes
        ]

        total_cost = sum(leg.price * leg.quantity for leg in legs)
        # One outcome always resolves to $1, so payout = max shares across legs
        # Actually for equal investment: payout = quantity_per_outcome / cheapest_price
        guaranteed_payout = min(leg.quantity for leg in legs)

        # Simpler calculation: invest $X total, get back $X / overround
        total_cost_simple = trade_size
        guaranteed_payout_simple = trade_size / overround

        opp = ArbitrageOpportunity(
            description=(
                f"INTRA-MARKET ARB on {market.platform.value}: "
                f'"{market.question}" — '
                f"prices sum to {overround:.4f} "
                f"({market.intra_arb_profit_pct:.2f}% guaranteed profit)"
            ),
            profit_pct=market.intra_arb_profit_pct,
            legs=legs,
            total_cost=total_cost_simple,
            guaranteed_payout=guaranteed_payout_simple,
        )
        opportunities.append(opp)
        logger.info(
            "Intra-market arb: %s (%.2f%% profit)",
            market.question[:60],
            market.intra_arb_profit_pct,
        )

    return opportunities


def find_cross_market_arbs(
    pairs: list[CrossMarketPair],
    min_profit_pct: float = MIN_PROFIT_PCT,
) -> list[ArbitrageOpportunity]:
    """Find arbitrage across two platforms pricing the same event.

    For binary markets: buy YES on the platform where it's cheapest,
    buy NO on the platform where it's cheapest. If total cost < $1.00,
    guaranteed profit.
    """
    opportunities: list[ArbitrageOpportunity] = []

    for pair in pairs:
        a = pair.market_a
        b = pair.market_b

        if len(a.outcomes) != 2 or len(b.outcomes) != 2:
            continue

        # Find YES/NO prices on each platform
        a_yes = _find_outcome_price(a, "Yes")
        a_no = _find_outcome_price(a, "No")
        b_yes = _find_outcome_price(b, "Yes")
        b_no = _find_outcome_price(b, "No")

        if any(p is None for p in [a_yes, a_no, b_yes, b_no]):
            continue

        # Strategy 1: Buy YES on cheapest, NO on cheapest
        best_yes_price = min(a_yes, b_yes)
        best_yes_platform = a if a_yes <= b_yes else b
        best_no_price = min(a_no, b_no)
        best_no_platform = a if a_no <= b_no else b

        combined_cost = best_yes_price + best_no_price
        if combined_cost >= 1.0:
            continue

        profit_pct = (1.0 / combined_cost - 1.0) * 100.0
        if profit_pct < min_profit_pct:
            continue

        trade_size = DEFAULT_TRADE_SIZE
        # Invest proportionally
        yes_investment = trade_size * (best_yes_price / combined_cost)
        no_investment = trade_size * (best_no_price / combined_cost)

        legs = [
            TradeLeg(
                platform=best_yes_platform.platform,
                market_id=best_yes_platform.id,
                market_question=best_yes_platform.question,
                outcome_name="Yes",
                price=best_yes_price,
                quantity=yes_investment / best_yes_price,
                url=best_yes_platform.url,
            ),
            TradeLeg(
                platform=best_no_platform.platform,
                market_id=best_no_platform.id,
                market_question=best_no_platform.question,
                outcome_name="No",
                price=best_no_price,
                quantity=no_investment / best_no_price,
                url=best_no_platform.url,
            ),
        ]

        opp = ArbitrageOpportunity(
            description=(
                f"CROSS-MARKET ARB: "
                f'"{a.question[:50]}" — '
                f"YES@{best_yes_price:.3f} on {best_yes_platform.platform.value}, "
                f"NO@{best_no_price:.3f} on {best_no_platform.platform.value} "
                f"(combined {combined_cost:.4f}, {profit_pct:.2f}% profit)"
            ),
            profit_pct=profit_pct,
            legs=legs,
            total_cost=trade_size,
            guaranteed_payout=trade_size / combined_cost,
        )
        opportunities.append(opp)
        logger.info(
            "Cross-market arb: %s (%.2f%% profit)",
            a.question[:60],
            profit_pct,
        )

    return opportunities


def match_cross_platform_markets(
    markets_a: list[Market],
    markets_b: list[Market],
    min_similarity: float = MIN_SIMILARITY,
) -> list[CrossMarketPair]:
    """Match markets across platforms by question similarity.

    Uses fuzzy string matching on market questions to find pairs that
    are asking about the same underlying event.
    """
    pairs: list[CrossMarketPair] = []

    for ma in markets_a:
        best_match: Market | None = None
        best_score = 0.0

        q_a = _normalize_question(ma.question)

        for mb in markets_b:
            q_b = _normalize_question(mb.question)
            score = SequenceMatcher(None, q_a, q_b).ratio()

            if score > best_score:
                best_score = score
                best_match = mb

        if best_match and best_score >= min_similarity:
            pairs.append(
                CrossMarketPair(
                    market_a=ma,
                    market_b=best_match,
                    similarity_score=best_score,
                )
            )
            logger.debug(
                "Matched: '%s' <-> '%s' (score=%.3f)",
                ma.question[:40],
                best_match.question[:40],
                best_score,
            )

    return pairs


def _find_outcome_price(market: Market, outcome_name: str) -> float | None:
    """Find the price of a named outcome (case-insensitive)."""
    target = outcome_name.lower()
    for outcome in market.outcomes:
        if outcome.name.lower() == target:
            return outcome.price
    return None


def _normalize_question(question: str) -> str:
    """Normalize a market question for fuzzy matching."""
    q = question.lower().strip()
    # Remove common suffixes/prefixes that differ across platforms
    for noise in ["will ", "is ", "does ", "do ", "?", "."]:
        q = q.replace(noise, "")
    return q.strip()
