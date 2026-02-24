"""CLI interface for the prediction market bot."""

from __future__ import annotations

import asyncio

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from prediction_market_bot.bot import PredictionMarketBot, ScanResult
from prediction_market_bot.config import BotConfig

console = Console()


@click.group()
def main() -> None:
    """Prediction Market Arbitrage Bot — find guaranteed-profit opportunities."""
    pass


@main.command()
@click.option("--cash", default=1000.0, help="Starting cash balance ($)")
@click.option("--min-profit", default=0.5, help="Minimum profit %% to flag")
@click.option("--limit", default=100, help="Markets to fetch per platform")
@click.option("--no-polymarket", is_flag=True, help="Disable Polymarket")
@click.option("--no-kalshi", is_flag=True, help="Disable Kalshi")
@click.option("--log-level", default="INFO", help="Log level")
@click.option("--log-file", default=None, help="Log to file")
def scan(
    cash: float,
    min_profit: float,
    limit: int,
    no_polymarket: bool,
    no_kalshi: bool,
    log_level: str,
    log_file: str | None,
) -> None:
    """Run a single scan for arbitrage opportunities."""
    config = BotConfig(
        starting_cash=cash,
        min_profit_pct=min_profit,
        markets_per_platform=limit,
        enable_polymarket=not no_polymarket,
        enable_kalshi=not no_kalshi,
        log_level=log_level,
        log_file=log_file,
        dry_run=True,
    )
    config.setup_logging()

    bot = PredictionMarketBot(config)
    result = asyncio.run(bot.scan_once())
    _display_scan_result(result)


@main.command()
@click.option("--cash", default=1000.0, help="Starting cash balance ($)")
@click.option("--interval", default=300, help="Seconds between scans")
@click.option("--min-profit", default=0.5, help="Minimum profit %% to flag")
@click.option("--limit", default=100, help="Markets to fetch per platform")
@click.option("--live", is_flag=True, help="Enable live trading (requires API keys)")
@click.option("--log-level", default="INFO", help="Log level")
def run(
    cash: float,
    interval: int,
    min_profit: float,
    limit: int,
    live: bool,
    log_level: str,
) -> None:
    """Run the bot in continuous scanning mode."""
    config = BotConfig(
        starting_cash=cash,
        scan_interval_seconds=interval,
        min_profit_pct=min_profit,
        markets_per_platform=limit,
        dry_run=not live,
        log_level=log_level,
    )
    config.setup_logging()

    if live:
        console.print(
            Panel(
                "[bold red]LIVE TRADING MODE[/bold red]\n"
                "Trades will be executed with real money.\n"
                "Requires API keys configured for each platform.",
                title="WARNING",
            )
        )
        if not click.confirm("Continue with live trading?"):
            return

    console.print(
        Panel(
            f"[bold green]Prediction Market Arbitrage Bot[/bold green]\n"
            f"Mode: {'[red]LIVE[/red]' if live else '[yellow]DRY RUN[/yellow]'}\n"
            f"Cash: ${cash:,.2f}\n"
            f"Min profit: {min_profit}%\n"
            f"Scan interval: {interval}s",
            title="Bot Configuration",
        )
    )

    bot = PredictionMarketBot(config)
    try:
        asyncio.run(bot.run_loop())
    except KeyboardInterrupt:
        console.print("\n[yellow]Bot stopped by user.[/yellow]")
        _display_portfolio_summary(bot)


@main.command()
@click.option("--limit", default=50, help="Markets to fetch per platform")
@click.option("--top", default=20, help="Top N markets to display")
def analyze(limit: int, top: int) -> None:
    """Analyze markets for mispricing signals (no trading)."""
    config = BotConfig(
        markets_per_platform=limit,
        dry_run=True,
        log_level="WARNING",
    )
    config.setup_logging()

    bot = PredictionMarketBot(config)
    result = asyncio.run(bot.scan_once())

    console.print(
        Panel(
            f"Scanned {result.markets_scanned} markets",
            title="Market Analysis",
        )
    )

    if result.top_analyses:
        table = Table(title="Top Markets by Mispricing Score")
        table.add_column("Score", style="bold")
        table.add_column("Platform")
        table.add_column("Question", max_width=50)
        table.add_column("Overround", justify="right")
        table.add_column("Edge Est.", justify="right")
        table.add_column("Notes", max_width=40)

        for analysis in result.top_analyses[:top]:
            score_style = "red" if analysis.mispricing_score >= 50 else (
                "yellow" if analysis.mispricing_score >= 20 else "green"
            )
            table.add_row(
                f"[{score_style}]{analysis.mispricing_score:.0f}[/{score_style}]",
                analysis.market.platform.value,
                analysis.market.question[:50],
                f"{analysis.overround:.4f}",
                f"{analysis.edge_estimate_pct:.2f}%" if analysis.edge_estimate_pct else "-",
                "; ".join(analysis.notes[:2]) if analysis.notes else "-",
            )
        console.print(table)
    else:
        console.print("[yellow]No markets analyzed.[/yellow]")


def _display_scan_result(result: ScanResult) -> None:
    """Display scan results in a formatted table."""
    console.print()
    console.print(
        Panel(
            f"Markets scanned: {result.markets_scanned}\n"
            f"Intra-market arbs: {result.intra_arbs_found}\n"
            f"Cross-market arbs: {result.cross_arbs_found}\n"
            f"Trades executed: {result.trades_executed}",
            title="Scan Results",
        )
    )

    if result.opportunities:
        table = Table(title="Arbitrage Opportunities Found")
        table.add_column("#", style="bold")
        table.add_column("Type")
        table.add_column("Description", max_width=60)
        table.add_column("Profit %", justify="right", style="green")
        table.add_column("Cost", justify="right")
        table.add_column("Payout", justify="right")

        for i, opp in enumerate(result.opportunities, 1):
            arb_type = "INTRA" if "INTRA" in opp.description else "CROSS"
            table.add_row(
                str(i),
                arb_type,
                opp.description[:60],
                f"{opp.profit_pct:.2f}%",
                f"${opp.total_cost:.2f}",
                f"${opp.guaranteed_payout:.2f}",
            )
        console.print(table)
    else:
        console.print(
            "[yellow]No arbitrage opportunities found in this scan. "
            "This is normal — true arb opportunities are rare and fleeting.[/yellow]"
        )

    # Show top mispricing signals
    if result.top_analyses:
        table = Table(title="Top Mispricing Signals")
        table.add_column("Score", style="bold")
        table.add_column("Platform")
        table.add_column("Question", max_width=50)
        table.add_column("Notes", max_width=50)

        for analysis in result.top_analyses[:10]:
            if analysis.mispricing_score > 0:
                table.add_row(
                    f"{analysis.mispricing_score:.0f}",
                    analysis.market.platform.value,
                    analysis.market.question[:50],
                    "; ".join(analysis.notes[:2]),
                )
        if table.row_count > 0:
            console.print(table)


def _display_portfolio_summary(bot: PredictionMarketBot) -> None:
    """Display portfolio and execution summary."""
    summary = bot.executor.summary()
    console.print(
        Panel(
            f"Trades attempted: {summary['trades_attempted']}\n"
            f"Trades executed: {summary['trades_executed']}\n"
            f"Total invested: ${summary['total_invested']:.2f}\n"
            f"Cash remaining: ${summary['cash_remaining']:.2f}\n"
            f"Open positions: {summary['positions']}",
            title="Portfolio Summary",
        )
    )


if __name__ == "__main__":
    main()
