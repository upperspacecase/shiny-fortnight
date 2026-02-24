"""Sample market data for demo/offline mode.

Provides realistic prediction market data with deliberately seeded
arbitrage opportunities so the bot can demonstrate its detection
capabilities without needing live API access.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from prediction_market_bot.models.market import Market, MarketStatus, Outcome, Platform


def get_sample_polymarket_markets() -> list[Market]:
    """Return sample Polymarket-style markets with some mispriced."""
    now = datetime.utcnow()
    return [
        # --- Intra-market arb: prices sum to 0.94 (6.4% profit) ---
        Market(
            id="pm-btc-100k",
            platform=Platform.POLYMARKET,
            question="Will Bitcoin exceed $100,000 by March 31, 2026?",
            outcomes=[
                Outcome(name="Yes", price=0.52, token_id="tok-btc-yes"),
                Outcome(name="No", price=0.42, token_id="tok-btc-no"),
            ],
            status=MarketStatus.OPEN,
            volume=1_250_000,
            liquidity=320_000,
            end_date=now + timedelta(days=35),
            url="https://polymarket.com/event/btc-100k",
            category="Crypto",
        ),
        # --- Normal market (no arb) ---
        Market(
            id="pm-fed-rate",
            platform=Platform.POLYMARKET,
            question="Will the Fed cut rates in March 2026?",
            outcomes=[
                Outcome(name="Yes", price=0.35, token_id="tok-fed-yes"),
                Outcome(name="No", price=0.68, token_id="tok-fed-no"),
            ],
            status=MarketStatus.OPEN,
            volume=890_000,
            liquidity=210_000,
            end_date=now + timedelta(days=20),
            url="https://polymarket.com/event/fed-rate-march",
            category="Economics",
        ),
        # --- Cross-market candidate: priced differently on Kalshi ---
        Market(
            id="pm-oscar-best-pic",
            platform=Platform.POLYMARKET,
            question="Will 'The Brutalist' win Best Picture at the Oscars?",
            outcomes=[
                Outcome(name="Yes", price=0.40, token_id="tok-oscar-yes"),
                Outcome(name="No", price=0.63, token_id="tok-oscar-no"),
            ],
            status=MarketStatus.OPEN,
            volume=420_000,
            liquidity=95_000,
            end_date=now + timedelta(days=10),
            url="https://polymarket.com/event/oscars-best-picture",
            category="Entertainment",
        ),
        # --- Intra-market arb: 3-way market sums to 0.88 (13.6% profit) ---
        Market(
            id="pm-nba-mvp",
            platform=Platform.POLYMARKET,
            question="Who will win NBA MVP 2025-26?",
            outcomes=[
                Outcome(name="Nikola Jokic", price=0.38, token_id="tok-mvp-jokic"),
                Outcome(name="Shai Gilgeous-Alexander", price=0.30, token_id="tok-mvp-sga"),
                Outcome(name="Luka Doncic", price=0.20, token_id="tok-mvp-luka"),
            ],
            status=MarketStatus.OPEN,
            volume=680_000,
            liquidity=45_000,
            end_date=now + timedelta(days=90),
            url="https://polymarket.com/event/nba-mvp",
            category="Sports",
        ),
        # --- Low-liquidity longshot market ---
        Market(
            id="pm-ufo-disclosure",
            platform=Platform.POLYMARKET,
            question="Will the US government confirm extraterrestrial contact by 2026?",
            outcomes=[
                Outcome(name="Yes", price=0.03, token_id="tok-ufo-yes"),
                Outcome(name="No", price=0.98, token_id="tok-ufo-no"),
            ],
            status=MarketStatus.OPEN,
            volume=15_000,
            liquidity=2_500,
            end_date=now + timedelta(days=300),
            url="https://polymarket.com/event/ufo-disclosure",
            category="Science",
        ),
        # --- Tight overround (near arb) ---
        Market(
            id="pm-trump-approval",
            platform=Platform.POLYMARKET,
            question="Will Trump approval rating exceed 50% in February 2026?",
            outcomes=[
                Outcome(name="Yes", price=0.28, token_id="tok-trump-yes"),
                Outcome(name="No", price=0.73, token_id="tok-trump-no"),
            ],
            status=MarketStatus.OPEN,
            volume=1_100_000,
            liquidity=280_000,
            end_date=now + timedelta(days=4),
            url="https://polymarket.com/event/trump-approval",
            category="Politics",
        ),
        # --- Cross-market candidate ---
        Market(
            id="pm-recession-2026",
            platform=Platform.POLYMARKET,
            question="Will the US enter a recession in 2026?",
            outcomes=[
                Outcome(name="Yes", price=0.22, token_id="tok-recess-yes"),
                Outcome(name="No", price=0.80, token_id="tok-recess-no"),
            ],
            status=MarketStatus.OPEN,
            volume=2_300_000,
            liquidity=560_000,
            end_date=now + timedelta(days=280),
            url="https://polymarket.com/event/us-recession-2026",
            category="Economics",
        ),
    ]


def get_sample_kalshi_markets() -> list[Market]:
    """Return sample Kalshi-style markets, some matching Polymarket questions."""
    now = datetime.utcnow()
    return [
        # --- Matches pm-oscar-best-pic but priced differently (cross-arb) ---
        # Poly YES=0.40, Kalshi NO=0.55 → combined = 0.95 → 5.3% profit
        Market(
            id="OSCAR-BESTPIC-BRUTALIST",
            platform=Platform.KALSHI,
            question="Will 'The Brutalist' win Best Picture at the Oscars?",
            outcomes=[
                Outcome(name="Yes", price=0.45),
                Outcome(name="No", price=0.55),
            ],
            status=MarketStatus.OPEN,
            volume=180_000,
            liquidity=42_000,
            end_date=now + timedelta(days=10),
            url="https://kalshi.com/markets/OSCAR-BESTPIC-BRUTALIST",
            category="Entertainment",
        ),
        # --- Matches pm-recession-2026 (cross-arb) ---
        # Poly YES=0.22, Kalshi NO=0.72 → combined = 0.94 → 6.4% profit
        Market(
            id="RECESSION-26-US",
            platform=Platform.KALSHI,
            question="Will the US enter a recession in 2026?",
            outcomes=[
                Outcome(name="Yes", price=0.28),
                Outcome(name="No", price=0.72),
            ],
            status=MarketStatus.OPEN,
            volume=950_000,
            liquidity=230_000,
            end_date=now + timedelta(days=280),
            url="https://kalshi.com/markets/RECESSION-26-US",
            category="Economics",
        ),
        # --- Matches pm-fed-rate (NO arb — prices align) ---
        Market(
            id="FED-RATE-MAR26",
            platform=Platform.KALSHI,
            question="Will the Fed cut rates in March 2026?",
            outcomes=[
                Outcome(name="Yes", price=0.34),
                Outcome(name="No", price=0.67),
            ],
            status=MarketStatus.OPEN,
            volume=620_000,
            liquidity=150_000,
            end_date=now + timedelta(days=20),
            url="https://kalshi.com/markets/FED-RATE-MAR26",
            category="Economics",
        ),
        # --- Intra-market arb: sum = 0.92 (8.7% profit) ---
        Market(
            id="MIDTERM-SENATE-CONTROL",
            platform=Platform.KALSHI,
            question="Will Democrats control the Senate after 2026 midterms?",
            outcomes=[
                Outcome(name="Yes", price=0.42),
                Outcome(name="No", price=0.50),
            ],
            status=MarketStatus.OPEN,
            volume=540_000,
            liquidity=120_000,
            end_date=now + timedelta(days=250),
            url="https://kalshi.com/markets/MIDTERM-SENATE-CONTROL",
            category="Politics",
        ),
        # --- Normal market ---
        Market(
            id="SP500-5500-MAR26",
            platform=Platform.KALSHI,
            question="Will S&P 500 close above 5,500 on March 31, 2026?",
            outcomes=[
                Outcome(name="Yes", price=0.62),
                Outcome(name="No", price=0.41),
            ],
            status=MarketStatus.OPEN,
            volume=1_800_000,
            liquidity=430_000,
            end_date=now + timedelta(days=35),
            url="https://kalshi.com/markets/SP500-5500-MAR26",
            category="Economics",
        ),
        # --- Matches pm-btc-100k but NO cross-arb (similar pricing) ---
        Market(
            id="BTC-100K-MAR26",
            platform=Platform.KALSHI,
            question="Will Bitcoin exceed $100,000 by March 31, 2026?",
            outcomes=[
                Outcome(name="Yes", price=0.54),
                Outcome(name="No", price=0.48),
            ],
            status=MarketStatus.OPEN,
            volume=780_000,
            liquidity=190_000,
            end_date=now + timedelta(days=35),
            url="https://kalshi.com/markets/BTC-100K-MAR26",
            category="Crypto",
        ),
    ]
