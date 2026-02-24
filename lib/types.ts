/** Core data types for prediction markets. */

export type Platform = "polymarket" | "kalshi";

export type MarketStatus = "open" | "closed" | "resolved";

export interface Outcome {
  name: string;
  /** Price from 0.0 to 1.0 — represents implied probability / cost per share. */
  price: number;
  tokenId?: string;
}

export interface Market {
  id: string;
  platform: Platform;
  question: string;
  outcomes: Outcome[];
  status: MarketStatus;
  volume: number;
  liquidity: number;
  endDate: string | null;
  url: string;
  category: string;
  fetchedAt: string;
}

export interface TradeLeg {
  platform: Platform;
  marketId: string;
  marketQuestion: string;
  outcomeName: string;
  price: number;
  quantity: number;
  url: string;
}

export interface ArbitrageOpportunity {
  description: string;
  profitPct: number;
  legs: TradeLeg[];
  totalCost: number;
  guaranteedPayout: number;
  detectedAt: string;
}

export interface CrossMarketPair {
  marketA: Market;
  marketB: Market;
  similarityScore: number;
}

export interface MarketAnalysis {
  market: Market;
  overround: number;
  mispricingScore: number;
  edgeEstimatePct: number;
  notes: string[];
  analyzedAt: string;
}

export interface ScanResult {
  marketsScanned: number;
  intraArbsFound: number;
  crossArbsFound: number;
  tradesExecuted: number;
  opportunities: ArbitrageOpportunity[];
  topAnalyses: MarketAnalysis[];
}

// Market helper functions

export function getOverround(market: Market): number {
  return market.outcomes.reduce((sum, o) => sum + o.price, 0);
}

export function hasIntraArb(market: Market): boolean {
  return getOverround(market) < 1.0 && market.outcomes.length >= 2;
}

export function getIntraArbProfitPct(market: Market): number {
  const overround = getOverround(market);
  if (!hasIntraArb(market)) return 0;
  return (1.0 / overround - 1.0) * 100.0;
}
