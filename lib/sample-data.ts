/**
 * Sample market data for demo mode.
 *
 * Realistic prediction market data with deliberately seeded arbitrage
 * opportunities so the bot can demonstrate its detection capabilities
 * without needing live API access.
 */

import { Market } from "./types";

function daysFromNow(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString();
}

const now = () => new Date().toISOString();

export function getSamplePolymarketMarkets(): Market[] {
  return [
    // Intra-market arb: prices sum to 0.94 (6.4% profit)
    {
      id: "pm-btc-100k",
      platform: "polymarket",
      question: "Will Bitcoin exceed $100,000 by March 31, 2026?",
      outcomes: [
        { name: "Yes", price: 0.52, tokenId: "tok-btc-yes" },
        { name: "No", price: 0.42, tokenId: "tok-btc-no" },
      ],
      status: "open",
      volume: 1_250_000,
      liquidity: 320_000,
      endDate: daysFromNow(35),
      url: "https://polymarket.com/event/btc-100k",
      category: "Crypto",
      fetchedAt: now(),
    },
    // Normal market (no arb)
    {
      id: "pm-fed-rate",
      platform: "polymarket",
      question: "Will the Fed cut rates in March 2026?",
      outcomes: [
        { name: "Yes", price: 0.35, tokenId: "tok-fed-yes" },
        { name: "No", price: 0.68, tokenId: "tok-fed-no" },
      ],
      status: "open",
      volume: 890_000,
      liquidity: 210_000,
      endDate: daysFromNow(20),
      url: "https://polymarket.com/event/fed-rate-march",
      category: "Economics",
      fetchedAt: now(),
    },
    // Cross-market candidate: priced differently on Kalshi
    {
      id: "pm-oscar-best-pic",
      platform: "polymarket",
      question: "Will 'The Brutalist' win Best Picture at the Oscars?",
      outcomes: [
        { name: "Yes", price: 0.4, tokenId: "tok-oscar-yes" },
        { name: "No", price: 0.63, tokenId: "tok-oscar-no" },
      ],
      status: "open",
      volume: 420_000,
      liquidity: 95_000,
      endDate: daysFromNow(10),
      url: "https://polymarket.com/event/oscars-best-picture",
      category: "Entertainment",
      fetchedAt: now(),
    },
    // Intra-market arb: 3-way market sums to 0.88 (13.6% profit)
    {
      id: "pm-nba-mvp",
      platform: "polymarket",
      question: "Who will win NBA MVP 2025-26?",
      outcomes: [
        { name: "Nikola Jokic", price: 0.38, tokenId: "tok-mvp-jokic" },
        { name: "Shai Gilgeous-Alexander", price: 0.3, tokenId: "tok-mvp-sga" },
        { name: "Luka Doncic", price: 0.2, tokenId: "tok-mvp-luka" },
      ],
      status: "open",
      volume: 680_000,
      liquidity: 45_000,
      endDate: daysFromNow(90),
      url: "https://polymarket.com/event/nba-mvp",
      category: "Sports",
      fetchedAt: now(),
    },
    // Low-liquidity longshot market
    {
      id: "pm-ufo-disclosure",
      platform: "polymarket",
      question:
        "Will the US government confirm extraterrestrial contact by 2026?",
      outcomes: [
        { name: "Yes", price: 0.03, tokenId: "tok-ufo-yes" },
        { name: "No", price: 0.98, tokenId: "tok-ufo-no" },
      ],
      status: "open",
      volume: 15_000,
      liquidity: 2_500,
      endDate: daysFromNow(300),
      url: "https://polymarket.com/event/ufo-disclosure",
      category: "Science",
      fetchedAt: now(),
    },
    // Tight overround
    {
      id: "pm-trump-approval",
      platform: "polymarket",
      question: "Will Trump approval rating exceed 50% in February 2026?",
      outcomes: [
        { name: "Yes", price: 0.28, tokenId: "tok-trump-yes" },
        { name: "No", price: 0.73, tokenId: "tok-trump-no" },
      ],
      status: "open",
      volume: 1_100_000,
      liquidity: 280_000,
      endDate: daysFromNow(4),
      url: "https://polymarket.com/event/trump-approval",
      category: "Politics",
      fetchedAt: now(),
    },
    // Cross-market candidate
    {
      id: "pm-recession-2026",
      platform: "polymarket",
      question: "Will the US enter a recession in 2026?",
      outcomes: [
        { name: "Yes", price: 0.22, tokenId: "tok-recess-yes" },
        { name: "No", price: 0.8, tokenId: "tok-recess-no" },
      ],
      status: "open",
      volume: 2_300_000,
      liquidity: 560_000,
      endDate: daysFromNow(280),
      url: "https://polymarket.com/event/us-recession-2026",
      category: "Economics",
      fetchedAt: now(),
    },
  ];
}

export function getSampleKalshiMarkets(): Market[] {
  return [
    // Matches pm-oscar-best-pic — cross-arb
    // Poly YES=0.40, Kalshi NO=0.55 → combined=0.95 → 5.3% profit
    {
      id: "OSCAR-BESTPIC-BRUTALIST",
      platform: "kalshi",
      question: "Will 'The Brutalist' win Best Picture at the Oscars?",
      outcomes: [
        { name: "Yes", price: 0.45 },
        { name: "No", price: 0.55 },
      ],
      status: "open",
      volume: 180_000,
      liquidity: 42_000,
      endDate: daysFromNow(10),
      url: "https://kalshi.com/markets/OSCAR-BESTPIC-BRUTALIST",
      category: "Entertainment",
      fetchedAt: now(),
    },
    // Matches pm-recession-2026 — cross-arb
    // Poly YES=0.22, Kalshi NO=0.72 → combined=0.94 → 6.4% profit
    {
      id: "RECESSION-26-US",
      platform: "kalshi",
      question: "Will the US enter a recession in 2026?",
      outcomes: [
        { name: "Yes", price: 0.28 },
        { name: "No", price: 0.72 },
      ],
      status: "open",
      volume: 950_000,
      liquidity: 230_000,
      endDate: daysFromNow(280),
      url: "https://kalshi.com/markets/RECESSION-26-US",
      category: "Economics",
      fetchedAt: now(),
    },
    // Matches pm-fed-rate — NO arb (prices align)
    {
      id: "FED-RATE-MAR26",
      platform: "kalshi",
      question: "Will the Fed cut rates in March 2026?",
      outcomes: [
        { name: "Yes", price: 0.34 },
        { name: "No", price: 0.67 },
      ],
      status: "open",
      volume: 620_000,
      liquidity: 150_000,
      endDate: daysFromNow(20),
      url: "https://kalshi.com/markets/FED-RATE-MAR26",
      category: "Economics",
      fetchedAt: now(),
    },
    // Intra-market arb: sum=0.92 (8.7% profit)
    {
      id: "MIDTERM-SENATE-CONTROL",
      platform: "kalshi",
      question: "Will Democrats control the Senate after 2026 midterms?",
      outcomes: [
        { name: "Yes", price: 0.42 },
        { name: "No", price: 0.5 },
      ],
      status: "open",
      volume: 540_000,
      liquidity: 120_000,
      endDate: daysFromNow(250),
      url: "https://kalshi.com/markets/MIDTERM-SENATE-CONTROL",
      category: "Politics",
      fetchedAt: now(),
    },
    // Normal market
    {
      id: "SP500-5500-MAR26",
      platform: "kalshi",
      question: "Will S&P 500 close above 5,500 on March 31, 2026?",
      outcomes: [
        { name: "Yes", price: 0.62 },
        { name: "No", price: 0.41 },
      ],
      status: "open",
      volume: 1_800_000,
      liquidity: 430_000,
      endDate: daysFromNow(35),
      url: "https://kalshi.com/markets/SP500-5500-MAR26",
      category: "Economics",
      fetchedAt: now(),
    },
    // Matches pm-btc-100k — similar pricing, no cross-arb
    {
      id: "BTC-100K-MAR26",
      platform: "kalshi",
      question: "Will Bitcoin exceed $100,000 by March 31, 2026?",
      outcomes: [
        { name: "Yes", price: 0.54 },
        { name: "No", price: 0.48 },
      ],
      status: "open",
      volume: 780_000,
      liquidity: 190_000,
      endDate: daysFromNow(35),
      url: "https://kalshi.com/markets/BTC-100K-MAR26",
      category: "Crypto",
      fetchedAt: now(),
    },
  ];
}
