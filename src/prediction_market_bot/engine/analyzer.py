"""Market analyzer — evaluates markets for mispricing and expected value.

Beyond pure arbitrage, this module scores markets for potential +EV trades
by looking at pricing anomalies, overround patterns, and market structure.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

from prediction_market_bot.models.market import Market

logger = logging.getLogger(__name__)


@dataclass
class MarketAnalysis:
    """Analysis result for a single market."""

    market: Market
    overround: float
    mispricing_score: float  # 0-100, higher = more likely mispriced
    edge_estimate_pct: float
    notes: list[str] = field(default_factory=list)
    analyzed_at: datetime = field(default_factory=datetime.utcnow)


def analyze_market(market: Market) -> MarketAnalysis:
    """Analyze a single market for mispricing signals."""
    notes: list[str] = []
    overround = market.overround
    mispricing_score = 0.0
    edge_estimate = 0.0

    # Signal 1: Overround anomaly
    # Normal binary markets have overround ~1.02-1.05.
    # Below 1.0 = free money (intra-arb). Above 1.10 = very high vig.
    if overround < 1.0:
        mispricing_score += 50
        edge_estimate = (1.0 / overround - 1.0) * 100
        notes.append(f"Underround: prices sum to {overround:.4f} (arb opportunity)")
    elif overround < 1.01:
        mispricing_score += 20
        notes.append(f"Very tight overround ({overround:.4f}), potential edge")
    elif overround > 1.10:
        notes.append(f"High vig ({overround:.4f}), avoid unless strong view")

    # Signal 2: Extreme probabilities near boundaries
    for outcome in market.outcomes:
        p = outcome.price
        if 0.01 <= p <= 0.05:
            mispricing_score += 15
            notes.append(
                f"'{outcome.name}' priced at {p:.3f} — "
                f"longshot bias common at this range"
            )
        elif 0.95 <= p <= 0.99:
            mispricing_score += 10
            notes.append(
                f"'{outcome.name}' priced at {p:.3f} — "
                f"near-certainty, check for overconfidence"
            )

    # Signal 3: Low liquidity (easier to move, potential for mispricing)
    if market.liquidity > 0 and market.liquidity < 5000:
        mispricing_score += 15
        notes.append(
            f"Low liquidity (${market.liquidity:,.0f}), "
            f"prices may not reflect true probability"
        )

    # Signal 4: Price doesn't match round-number bias
    for outcome in market.outcomes:
        p = outcome.price
        # Markets tend to cluster at 0.10, 0.25, 0.50, 0.75, 0.90
        round_levels = [0.10, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.70, 0.75, 0.80, 0.90]
        near_round = any(abs(p - r) < 0.02 for r in round_levels)
        if near_round:
            mispricing_score += 5
            notes.append(
                f"'{outcome.name}' near round number ({p:.3f}), "
                f"could be anchoring bias"
            )

    # Signal 5: Multi-outcome markets (> 2 outcomes)
    if len(market.outcomes) > 2:
        mispricing_score += 10
        notes.append(
            f"{len(market.outcomes)} outcomes — "
            f"multi-way markets more likely to have mispricing"
        )

    mispricing_score = min(mispricing_score, 100.0)

    return MarketAnalysis(
        market=market,
        overround=overround,
        mispricing_score=mispricing_score,
        edge_estimate_pct=edge_estimate,
        notes=notes,
    )


def rank_markets(markets: list[Market]) -> list[MarketAnalysis]:
    """Analyze and rank markets by mispricing potential."""
    analyses = [analyze_market(m) for m in markets]
    analyses.sort(key=lambda a: a.mispricing_score, reverse=True)
    return analyses
