/**
 * API clients for Polymarket and Kalshi prediction markets.
 */

import { Market, Outcome, Platform } from "./types";

const GAMMA_API_BASE = "https://gamma-api.polymarket.com";
const KALSHI_API_BASE = "https://api.elections.kalshi.com/trade-api/v2";

export async function fetchPolymarketMarkets(
  limit: number = 100
): Promise<Market[]> {
  const markets: Market[] = [];

  const params = new URLSearchParams({
    limit: String(limit),
    active: "true",
    closed: "false",
    order: "volume24hr",
    ascending: "false",
  });

  const resp = await fetch(`${GAMMA_API_BASE}/markets?${params}`, {
    headers: { Accept: "application/json" },
  });

  if (!resp.ok) {
    throw new Error(`Polymarket API error: ${resp.status} ${resp.statusText}`);
  }

  const data = await resp.json();

  for (const item of data) {
    const market = parsePolymarketMarket(item);
    if (market) markets.push(market);
  }

  return markets;
}

function parsePolymarketMarket(data: Record<string, unknown>): Market | null {
  let outcomeNames: string[];
  let outcomePrices: string[];

  try {
    const rawOutcomes = data.outcomes as string;
    const rawPrices = data.outcomePrices as string;
    outcomeNames =
      typeof rawOutcomes === "string" ? JSON.parse(rawOutcomes) : rawOutcomes;
    outcomePrices =
      typeof rawPrices === "string" ? JSON.parse(rawPrices) : rawPrices;
  } catch {
    return null;
  }

  if (
    !Array.isArray(outcomeNames) ||
    !Array.isArray(outcomePrices) ||
    outcomeNames.length !== outcomePrices.length ||
    outcomeNames.length === 0
  ) {
    return null;
  }

  const outcomes: Outcome[] = outcomeNames.map((name, i) => ({
    name: String(name),
    price: parseFloat(String(outcomePrices[i])),
  }));

  if (outcomes.some((o) => isNaN(o.price))) return null;

  // Attach token IDs if available
  let tokenIds: string[] = [];
  try {
    const raw = data.clobTokenIds as string;
    tokenIds = typeof raw === "string" ? JSON.parse(raw) : raw || [];
  } catch {
    /* ignore */
  }
  if (Array.isArray(tokenIds) && tokenIds.length === outcomes.length) {
    outcomes.forEach((o, i) => (o.tokenId = String(tokenIds[i])));
  }

  return {
    id: String(data.id ?? ""),
    platform: "polymarket" as Platform,
    question: String(data.question ?? ""),
    outcomes,
    status: "open",
    volume: parseFloat(String(data.volume ?? 0)) || 0,
    liquidity: parseFloat(String(data.liquidity ?? 0)) || 0,
    endDate: data.endDate ? String(data.endDate) : null,
    url: `https://polymarket.com/event/${data.slug ?? ""}`,
    category: String(data.category ?? ""),
    fetchedAt: new Date().toISOString(),
  };
}

export async function fetchKalshiMarkets(
  limit: number = 100
): Promise<Market[]> {
  const markets: Market[] = [];

  const params = new URLSearchParams({
    limit: String(limit),
    status: "open",
  });

  const resp = await fetch(`${KALSHI_API_BASE}/markets?${params}`, {
    headers: { Accept: "application/json" },
  });

  if (!resp.ok) {
    throw new Error(`Kalshi API error: ${resp.status} ${resp.statusText}`);
  }

  const data = await resp.json();

  for (const item of (data.markets ?? [])) {
    const market = parseKalshiMarket(item);
    if (market) markets.push(market);
  }

  return markets;
}

function parseKalshiMarket(data: Record<string, unknown>): Market | null {
  const yesRaw = (data.yes_bid ?? data.last_price) as number | undefined;
  if (yesRaw == null) return null;

  let yesPrice = Number(yesRaw) / 100.0;
  let noPrice = 1.0 - yesPrice;

  const noBid = data.no_bid as number | undefined;
  if (noBid != null) {
    noPrice = Number(noBid) / 100.0;
  }

  const ticker = String(data.ticker ?? "");

  return {
    id: ticker,
    platform: "kalshi" as Platform,
    question: String(data.title ?? ""),
    outcomes: [
      { name: "Yes", price: yesPrice },
      { name: "No", price: noPrice },
    ],
    status: "open",
    volume: parseFloat(String(data.volume ?? 0)) || 0,
    liquidity: parseFloat(String(data.open_interest ?? 0)) || 0,
    endDate: data.close_time ? String(data.close_time) : null,
    url: `https://kalshi.com/markets/${ticker}`,
    category: String(data.category ?? ""),
    fetchedAt: new Date().toISOString(),
  };
}
