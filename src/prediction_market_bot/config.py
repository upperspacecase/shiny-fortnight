"""Bot configuration."""

from __future__ import annotations

import logging
from dataclasses import dataclass


@dataclass
class BotConfig:
    """Configuration for the prediction market bot."""

    # Scanning
    scan_interval_seconds: int = 300
    markets_per_platform: int = 100

    # Arbitrage detection
    min_profit_pct: float = 0.5
    min_similarity: float = 0.65

    # Execution
    dry_run: bool = True
    starting_cash: float = 1000.0
    max_position_size: float = 200.0
    max_portfolio_risk: float = 0.5

    # Platforms
    enable_polymarket: bool = True
    enable_kalshi: bool = True

    # Logging
    log_level: str = "INFO"
    log_file: str | None = None

    def setup_logging(self) -> None:
        handlers: list[logging.Handler] = [logging.StreamHandler()]
        if self.log_file:
            handlers.append(logging.FileHandler(self.log_file))

        logging.basicConfig(
            level=getattr(logging, self.log_level.upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=handlers,
        )
