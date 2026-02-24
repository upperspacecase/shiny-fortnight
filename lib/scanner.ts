/**
 * Main scanner — ties together clients, analysis, and arbitrage detection.
 */

import { rankMarkets } from "./analyzer";
import {
  findCrossMarketArbs,
  findIntraMarketArbs,
  matchCrossPlatformMarkets,
} from "./arbitrage";
import { fetchKalshiMarkets, fetchPolymarketMarkets } from "./clients";
import {
  getSampleKalshiMarkets,
  getSamplePolymarketMarkets,
} from "./sample-data";
import type {
  ArbitrageOpportunity,
  Market,
  MarketAnalysis,
  ScanResult,
} from "./types";

export interface ScanOptions {
  demo?: boolean;
  enablePolymarket?: boolean;
  enableKalshi?: boolean;
  minProfitPct?: number;
  minSimilarity?: number;
  limit?: number;
}

export async function runScan(options: ScanOptions = {}): Promise<ScanResult> {
  const {
    demo = true,
    enablePolymarket = true,
    enableKalshi = true,
    minProfitPct = 0.5,
    minSimilarity = 0.65,
    limit = 100,
  } = options;

  let polyMarkets: Market[] = [];
  let kalshiMarkets: Market[] = [];

  if (demo) {
    if (enablePolymarket) polyMarkets = getSamplePolymarketMarkets();
    if (enableKalshi) kalshiMarkets = getSampleKalshiMarkets();
  } else {
    const fetches: Promise<void>[] = [];

    if (enablePolymarket) {
      fetches.push(
        fetchPolymarketMarkets(limit)
          .then((m) => {
            polyMarkets = m;
          })
          .catch((e) => {
            console.error("Failed to fetch Polymarket:", e);
          })
      );
    }

    if (enableKalshi) {
      fetches.push(
        fetchKalshiMarkets(limit)
          .then((m) => {
            kalshiMarkets = m;
          })
          .catch((e) => {
            console.error("Failed to fetch Kalshi:", e);
          })
      );
    }

    await Promise.all(fetches);
  }

  const allMarkets = [...polyMarkets, ...kalshiMarkets];

  // 1. Intra-market arbitrage
  const intraArbs = findIntraMarketArbs(allMarkets, minProfitPct);

  // 2. Cross-market arbitrage
  let crossArbs: ArbitrageOpportunity[] = [];
  if (polyMarkets.length > 0 && kalshiMarkets.length > 0) {
    const pairs = matchCrossPlatformMarkets(
      polyMarkets,
      kalshiMarkets,
      minSimilarity
    );
    crossArbs = findCrossMarketArbs(pairs, minProfitPct);
  }

  const allOpps = [...intraArbs, ...crossArbs].sort(
    (a, b) => b.profitPct - a.profitPct
  );

  // 3. Analyze markets for mispricing signals
  const analyses = rankMarkets(allMarkets);

  return {
    marketsScanned: allMarkets.length,
    intraArbsFound: intraArbs.length,
    crossArbsFound: crossArbs.length,
    tradesExecuted: allOpps.length,
    opportunities: allOpps,
    topAnalyses: analyses.slice(0, 20),
  };
}
