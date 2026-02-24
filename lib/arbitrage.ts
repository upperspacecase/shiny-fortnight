/**
 * Arbitrage detection engine.
 *
 * Two main strategies for guaranteed profit in prediction markets:
 *
 * 1. INTRA-MARKET ARBITRAGE:
 *    If a market's outcome prices sum to < $1.00, buy all outcomes for
 *    guaranteed $1.00 payout.
 *    Example: YES=$0.45 + NO=$0.50 = $0.95 cost → $1.00 payout → 5.26% profit
 *
 * 2. CROSS-MARKET ARBITRAGE:
 *    If two platforms price the same event differently, buy the cheaper side
 *    on each platform.
 *    Example: Platform A YES=$0.60, Platform B NO=$0.35 → $0.95 → 5.26% profit
 */

import {
  ArbitrageOpportunity,
  CrossMarketPair,
  Market,
  TradeLeg,
  getOverround,
  hasIntraArb,
  getIntraArbProfitPct,
} from "./types";

const DEFAULT_TRADE_SIZE = 100.0;

export function findIntraMarketArbs(
  markets: Market[],
  minProfitPct: number = 0.5
): ArbitrageOpportunity[] {
  const opportunities: ArbitrageOpportunity[] = [];

  for (const market of markets) {
    if (!hasIntraArb(market)) continue;

    const profitPct = getIntraArbProfitPct(market);
    if (profitPct < minProfitPct) continue;

    const overround = getOverround(market);
    const tradeSize = DEFAULT_TRADE_SIZE;
    const quantityPerOutcome = tradeSize / market.outcomes.length;

    const legs: TradeLeg[] = market.outcomes.map((outcome) => ({
      platform: market.platform,
      marketId: market.id,
      marketQuestion: market.question,
      outcomeName: outcome.name,
      price: outcome.price,
      quantity: quantityPerOutcome / outcome.price,
      url: market.url,
    }));

    opportunities.push({
      description:
        `INTRA-MARKET ARB on ${market.platform}: ` +
        `"${market.question}" — ` +
        `prices sum to ${overround.toFixed(4)} ` +
        `(${profitPct.toFixed(2)}% guaranteed profit)`,
      profitPct,
      legs,
      totalCost: tradeSize,
      guaranteedPayout: tradeSize / overround,
      detectedAt: new Date().toISOString(),
    });
  }

  return opportunities;
}

export function findCrossMarketArbs(
  pairs: CrossMarketPair[],
  minProfitPct: number = 0.5
): ArbitrageOpportunity[] {
  const opportunities: ArbitrageOpportunity[] = [];

  for (const pair of pairs) {
    const { marketA, marketB } = pair;

    if (marketA.outcomes.length !== 2 || marketB.outcomes.length !== 2) continue;

    const aYes = findOutcomePrice(marketA, "Yes");
    const aNo = findOutcomePrice(marketA, "No");
    const bYes = findOutcomePrice(marketB, "Yes");
    const bNo = findOutcomePrice(marketB, "No");

    if (aYes === null || aNo === null || bYes === null || bNo === null) continue;

    const bestYesPrice = Math.min(aYes, bYes);
    const bestYesPlatform = aYes <= bYes ? marketA : marketB;
    const bestNoPrice = Math.min(aNo, bNo);
    const bestNoPlatform = aNo <= bNo ? marketA : marketB;

    const combinedCost = bestYesPrice + bestNoPrice;
    if (combinedCost >= 1.0) continue;

    const profitPct = (1.0 / combinedCost - 1.0) * 100.0;
    if (profitPct < minProfitPct) continue;

    const tradeSize = DEFAULT_TRADE_SIZE;
    const yesInvestment = tradeSize * (bestYesPrice / combinedCost);
    const noInvestment = tradeSize * (bestNoPrice / combinedCost);

    const legs: TradeLeg[] = [
      {
        platform: bestYesPlatform.platform,
        marketId: bestYesPlatform.id,
        marketQuestion: bestYesPlatform.question,
        outcomeName: "Yes",
        price: bestYesPrice,
        quantity: yesInvestment / bestYesPrice,
        url: bestYesPlatform.url,
      },
      {
        platform: bestNoPlatform.platform,
        marketId: bestNoPlatform.id,
        marketQuestion: bestNoPlatform.question,
        outcomeName: "No",
        price: bestNoPrice,
        quantity: noInvestment / bestNoPrice,
        url: bestNoPlatform.url,
      },
    ];

    opportunities.push({
      description:
        `CROSS-MARKET ARB: "${marketA.question.slice(0, 50)}" — ` +
        `YES@${bestYesPrice.toFixed(3)} on ${bestYesPlatform.platform}, ` +
        `NO@${bestNoPrice.toFixed(3)} on ${bestNoPlatform.platform} ` +
        `(combined ${combinedCost.toFixed(4)}, ${profitPct.toFixed(2)}% profit)`,
      profitPct,
      legs,
      totalCost: tradeSize,
      guaranteedPayout: tradeSize / combinedCost,
      detectedAt: new Date().toISOString(),
    });
  }

  return opportunities;
}

export function matchCrossPlatformMarkets(
  marketsA: Market[],
  marketsB: Market[],
  minSimilarity: number = 0.65
): CrossMarketPair[] {
  const pairs: CrossMarketPair[] = [];

  for (const ma of marketsA) {
    let bestMatch: Market | null = null;
    let bestScore = 0;

    const qA = normalizeQuestion(ma.question);

    for (const mb of marketsB) {
      const qB = normalizeQuestion(mb.question);
      const score = similarityScore(qA, qB);

      if (score > bestScore) {
        bestScore = score;
        bestMatch = mb;
      }
    }

    if (bestMatch && bestScore >= minSimilarity) {
      pairs.push({
        marketA: ma,
        marketB: bestMatch,
        similarityScore: bestScore,
      });
    }
  }

  return pairs;
}

function findOutcomePrice(market: Market, outcomeName: string): number | null {
  const target = outcomeName.toLowerCase();
  for (const outcome of market.outcomes) {
    if (outcome.name.toLowerCase() === target) {
      return outcome.price;
    }
  }
  return null;
}

function normalizeQuestion(question: string): string {
  let q = question.toLowerCase().trim();
  for (const noise of ["will ", "is ", "does ", "do ", "?", "."]) {
    q = q.replaceAll(noise, "");
  }
  return q.trim();
}

/** Simple bigram-based similarity (Dice coefficient). */
function similarityScore(a: string, b: string): number {
  if (a === b) return 1.0;
  if (a.length < 2 || b.length < 2) return 0.0;

  const bigramsA = new Set<string>();
  for (let i = 0; i < a.length - 1; i++) {
    bigramsA.add(a.slice(i, i + 2));
  }

  const bigramsB = new Set<string>();
  for (let i = 0; i < b.length - 1; i++) {
    bigramsB.add(b.slice(i, i + 2));
  }

  let intersection = 0;
  for (const bg of bigramsA) {
    if (bigramsB.has(bg)) intersection++;
  }

  return (2 * intersection) / (bigramsA.size + bigramsB.size);
}
