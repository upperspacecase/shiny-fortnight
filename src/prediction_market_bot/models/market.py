"""Core data models for prediction markets."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Platform(Enum):
    """Supported prediction market platforms."""

    POLYMARKET = "polymarket"
    KALSHI = "kalshi"


class MarketStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    RESOLVED = "resolved"


@dataclass(frozen=True)
class Outcome:
    """A single outcome within a market (e.g. YES or NO)."""

    name: str
    price: float  # 0.0 to 1.0, represents implied probability / cost
    token_id: str = ""

    @property
    def implied_probability(self) -> float:
        return self.price


@dataclass
class Market:
    """A single prediction market question with its outcomes."""

    id: str
    platform: Platform
    question: str
    outcomes: list[Outcome]
    status: MarketStatus = MarketStatus.OPEN
    volume: float = 0.0
    liquidity: float = 0.0
    end_date: datetime | None = None
    url: str = ""
    category: str = ""
    fetched_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def overround(self) -> float:
        """Sum of all outcome prices. If > 1.0, the book has overround (margin).
        If < 1.0, there's an intra-market arbitrage opportunity."""
        return sum(o.price for o in self.outcomes)

    @property
    def has_intra_arb(self) -> bool:
        """True if buying all outcomes costs less than $1 (guaranteed profit)."""
        return self.overround < 1.0 and len(self.outcomes) >= 2

    @property
    def intra_arb_profit_pct(self) -> float:
        """Guaranteed profit percentage from intra-market arbitrage.
        E.g., if overround is 0.95, profit is ~5.26% ((1/0.95 - 1) * 100)."""
        if not self.has_intra_arb:
            return 0.0
        return (1.0 / self.overround - 1.0) * 100.0


@dataclass(frozen=True)
class CrossMarketPair:
    """Two markets on different platforms asking the same or equivalent question."""

    market_a: Market
    market_b: Market
    similarity_score: float  # 0.0 to 1.0


@dataclass
class ArbitrageOpportunity:
    """A detected arbitrage opportunity."""

    description: str
    profit_pct: float
    legs: list[TradeLeg]
    total_cost: float
    guaranteed_payout: float
    detected_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def profit_amount(self) -> float:
        return self.guaranteed_payout - self.total_cost


@dataclass(frozen=True)
class TradeLeg:
    """One leg of an arbitrage trade."""

    platform: Platform
    market_id: str
    market_question: str
    outcome_name: str
    price: float
    quantity: float
    url: str = ""


@dataclass
class Portfolio:
    """Tracks positions and P&L."""

    positions: list[TradeLeg] = field(default_factory=list)
    cash: float = 1000.0
    total_invested: float = 0.0
    realized_pnl: float = 0.0

    @property
    def unrealized_value(self) -> float:
        """Worst-case guaranteed value of open positions."""
        return sum(leg.quantity for leg in self.positions)

    def record_trade(self, legs: list[TradeLeg], cost: float) -> None:
        self.positions.extend(legs)
        self.cash -= cost
        self.total_invested += cost
