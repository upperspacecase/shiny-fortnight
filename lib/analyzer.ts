/**
 * Market analyzer — evaluates markets for mispricing and expected value.
 *
 * Scores markets by pricing anomalies, overround patterns, and market structure.
 */

import { Market, MarketAnalysis, getOverround, hasIntraArb } from "./types";

export function analyzeMarket(market: Market): MarketAnalysis {
  const notes: string[] = [];
  const overround = getOverround(market);
  let mispricingScore = 0;
  let edgeEstimate = 0;

  // Signal 1: Overround anomaly
  if (overround < 1.0) {
    mispricingScore += 50;
    edgeEstimate = (1.0 / overround - 1.0) * 100;
    notes.push(
      `Underround: prices sum to ${overround.toFixed(4)} (arb opportunity)`
    );
  } else if (overround < 1.01) {
    mispricingScore += 20;
    notes.push(
      `Very tight overround (${overround.toFixed(4)}), potential edge`
    );
  } else if (overround > 1.1) {
    notes.push(
      `High vig (${overround.toFixed(4)}), avoid unless strong view`
    );
  }

  // Signal 2: Extreme probabilities near boundaries
  for (const outcome of market.outcomes) {
    const p = outcome.price;
    if (p >= 0.01 && p <= 0.05) {
      mispricingScore += 15;
      notes.push(
        `'${outcome.name}' priced at ${p.toFixed(3)} — longshot bias common at this range`
      );
    } else if (p >= 0.95 && p <= 0.99) {
      mispricingScore += 10;
      notes.push(
        `'${outcome.name}' priced at ${p.toFixed(3)} — near-certainty, check for overconfidence`
      );
    }
  }

  // Signal 3: Low liquidity
  if (market.liquidity > 0 && market.liquidity < 5000) {
    mispricingScore += 15;
    notes.push(
      `Low liquidity ($${market.liquidity.toLocaleString()}), prices may not reflect true probability`
    );
  }

  // Signal 4: Round-number anchoring bias
  const roundLevels = [0.1, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9];
  for (const outcome of market.outcomes) {
    const p = outcome.price;
    const nearRound = roundLevels.some((r) => Math.abs(p - r) < 0.02);
    if (nearRound) {
      mispricingScore += 5;
      notes.push(
        `'${outcome.name}' near round number (${p.toFixed(3)}), could be anchoring bias`
      );
    }
  }

  // Signal 5: Multi-outcome markets
  if (market.outcomes.length > 2) {
    mispricingScore += 10;
    notes.push(
      `${market.outcomes.length} outcomes — multi-way markets more likely to have mispricing`
    );
  }

  mispricingScore = Math.min(mispricingScore, 100);

  return {
    market,
    overround,
    mispricingScore,
    edgeEstimatePct: edgeEstimate,
    notes,
    analyzedAt: new Date().toISOString(),
  };
}

export function rankMarkets(markets: Market[]): MarketAnalysis[] {
  return markets
    .map(analyzeMarket)
    .sort((a, b) => b.mispricingScore - a.mispricingScore);
}
