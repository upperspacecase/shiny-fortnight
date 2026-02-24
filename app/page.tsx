import { runScan } from "@/lib/scanner";
import type {
  ArbitrageOpportunity,
  MarketAnalysis,
  ScanResult,
} from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function Dashboard() {
  const result: ScanResult = await runScan({ demo: true });

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "2rem 1rem" }}>
      <header style={{ marginBottom: "2rem" }}>
        <h1
          style={{
            fontSize: "1.75rem",
            fontWeight: 700,
            margin: 0,
            color: "#fff",
          }}
        >
          Prediction Market Arbitrage Bot
        </h1>
        <p style={{ color: "#888", marginTop: "0.25rem", fontSize: "0.9rem" }}>
          Scans Polymarket &amp; Kalshi for guaranteed-profit opportunities
        </p>
      </header>

      {/* Summary cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "1rem",
          marginBottom: "2rem",
        }}
      >
        <StatCard label="Markets Scanned" value={result.marketsScanned} />
        <StatCard
          label="Intra-Market Arbs"
          value={result.intraArbsFound}
          color="#22c55e"
        />
        <StatCard
          label="Cross-Market Arbs"
          value={result.crossArbsFound}
          color="#3b82f6"
        />
        <StatCard
          label="Total Opportunities"
          value={result.opportunities.length}
          color="#f59e0b"
        />
      </div>

      {/* Arbitrage opportunities */}
      <section style={{ marginBottom: "2.5rem" }}>
        <h2
          style={{ fontSize: "1.25rem", fontWeight: 600, marginBottom: "1rem" }}
        >
          Arbitrage Opportunities
        </h2>
        {result.opportunities.length === 0 ? (
          <p style={{ color: "#888" }}>
            No arbitrage opportunities found. This is normal — true arb
            opportunities are rare and fleeting.
          </p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr
                  style={{
                    borderBottom: "1px solid #333",
                    textAlign: "left",
                  }}
                >
                  <Th>#</Th>
                  <Th>Type</Th>
                  <Th>Description</Th>
                  <Th align="right">Profit %</Th>
                  <Th align="right">Cost</Th>
                  <Th align="right">Payout</Th>
                </tr>
              </thead>
              <tbody>
                {result.opportunities.map(
                  (opp: ArbitrageOpportunity, i: number) => (
                    <tr
                      key={i}
                      style={{ borderBottom: "1px solid #222" }}
                    >
                      <Td>{i + 1}</Td>
                      <Td>
                        <TypeBadge
                          type={
                            opp.description.includes("INTRA")
                              ? "INTRA"
                              : "CROSS"
                          }
                        />
                      </Td>
                      <Td style={{ maxWidth: 400 }}>
                        {formatDescription(opp.description)}
                      </Td>
                      <Td
                        align="right"
                        style={{ color: "#22c55e", fontWeight: 600 }}
                      >
                        {opp.profitPct.toFixed(2)}%
                      </Td>
                      <Td align="right">${opp.totalCost.toFixed(2)}</Td>
                      <Td align="right">
                        ${opp.guaranteedPayout.toFixed(2)}
                      </Td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Trade legs detail */}
      {result.opportunities.length > 0 && (
        <section style={{ marginBottom: "2.5rem" }}>
          <h2
            style={{
              fontSize: "1.25rem",
              fontWeight: 600,
              marginBottom: "1rem",
            }}
          >
            Trade Details
          </h2>
          {result.opportunities.map((opp: ArbitrageOpportunity, i: number) => (
            <div
              key={i}
              style={{
                border: "1px solid #333",
                borderRadius: 8,
                padding: "1rem",
                marginBottom: "0.75rem",
                backgroundColor: "#111",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "0.5rem",
                }}
              >
                <strong style={{ color: "#fff" }}>
                  Trade #{i + 1} — {opp.profitPct.toFixed(2)}% guaranteed
                  profit
                </strong>
                <TypeBadge
                  type={
                    opp.description.includes("INTRA") ? "INTRA" : "CROSS"
                  }
                />
              </div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                  gap: "0.5rem",
                }}
              >
                {opp.legs.map((leg, j) => (
                  <div
                    key={j}
                    style={{
                      padding: "0.5rem 0.75rem",
                      backgroundColor: "#1a1a1a",
                      borderRadius: 6,
                      fontSize: "0.85rem",
                    }}
                  >
                    <div>
                      <span style={{ color: "#22c55e" }}>BUY</span>{" "}
                      <strong>{leg.outcomeName}</strong> @{" "}
                      <span style={{ color: "#f59e0b" }}>
                        ${leg.price.toFixed(3)}
                      </span>
                    </div>
                    <div style={{ color: "#888", marginTop: 2 }}>
                      on {leg.platform} &middot;{" "}
                      {leg.marketQuestion.slice(0, 50)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </section>
      )}

      {/* Market analysis */}
      <section>
        <h2
          style={{ fontSize: "1.25rem", fontWeight: 600, marginBottom: "1rem" }}
        >
          Mispricing Signals
        </h2>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr
                style={{
                  borderBottom: "1px solid #333",
                  textAlign: "left",
                }}
              >
                <Th>Score</Th>
                <Th>Platform</Th>
                <Th>Question</Th>
                <Th align="right">Overround</Th>
                <Th align="right">Edge Est.</Th>
                <Th>Notes</Th>
              </tr>
            </thead>
            <tbody>
              {result.topAnalyses
                .filter((a: MarketAnalysis) => a.mispricingScore > 0)
                .map((a: MarketAnalysis, i: number) => (
                  <tr
                    key={i}
                    style={{ borderBottom: "1px solid #222" }}
                  >
                    <Td>
                      <ScoreBadge score={a.mispricingScore} />
                    </Td>
                    <Td>
                      <PlatformBadge platform={a.market.platform} />
                    </Td>
                    <Td style={{ maxWidth: 300 }}>
                      {a.market.question.slice(0, 60)}
                    </Td>
                    <Td align="right">{a.overround.toFixed(4)}</Td>
                    <Td align="right">
                      {a.edgeEstimatePct > 0
                        ? `${a.edgeEstimatePct.toFixed(2)}%`
                        : "—"}
                    </Td>
                    <Td style={{ maxWidth: 300, fontSize: "0.8rem" }}>
                      {a.notes.slice(0, 2).join("; ")}
                    </Td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* API info */}
      <footer
        style={{
          marginTop: "3rem",
          paddingTop: "1.5rem",
          borderTop: "1px solid #222",
          color: "#666",
          fontSize: "0.8rem",
        }}
      >
        <p>
          <strong>API Endpoints:</strong>{" "}
          <code style={{ color: "#888" }}>GET /api/scan</code> &middot;{" "}
          <code style={{ color: "#888" }}>GET /api/analyze</code> &middot;
          Add <code style={{ color: "#888" }}>?demo=false</code> for live data
        </p>
      </footer>
    </div>
  );
}

// ----- UI Components -----

function StatCard({
  label,
  value,
  color = "#fff",
}: {
  label: string;
  value: number;
  color?: string;
}) {
  return (
    <div
      style={{
        border: "1px solid #333",
        borderRadius: 8,
        padding: "1rem 1.25rem",
        backgroundColor: "#111",
      }}
    >
      <div style={{ fontSize: "0.8rem", color: "#888", marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: "1.75rem", fontWeight: 700, color }}>{value}</div>
    </div>
  );
}

function Th({
  children,
  align = "left",
}: {
  children: React.ReactNode;
  align?: "left" | "right";
}) {
  return (
    <th
      style={{
        padding: "0.5rem 0.75rem",
        fontSize: "0.75rem",
        fontWeight: 600,
        color: "#888",
        textTransform: "uppercase",
        letterSpacing: "0.05em",
        textAlign: align,
      }}
    >
      {children}
    </th>
  );
}

function Td({
  children,
  align = "left",
  style = {},
}: {
  children: React.ReactNode;
  align?: "left" | "right";
  style?: React.CSSProperties;
}) {
  return (
    <td
      style={{
        padding: "0.6rem 0.75rem",
        fontSize: "0.85rem",
        textAlign: align,
        ...style,
      }}
    >
      {children}
    </td>
  );
}

function TypeBadge({ type }: { type: "INTRA" | "CROSS" }) {
  const color = type === "INTRA" ? "#22c55e" : "#3b82f6";
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 8px",
        borderRadius: 4,
        backgroundColor: `${color}22`,
        color,
        fontSize: "0.75rem",
        fontWeight: 600,
      }}
    >
      {type}
    </span>
  );
}

function ScoreBadge({ score }: { score: number }) {
  const color = score >= 50 ? "#ef4444" : score >= 20 ? "#f59e0b" : "#22c55e";
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 8px",
        borderRadius: 4,
        backgroundColor: `${color}22`,
        color,
        fontSize: "0.85rem",
        fontWeight: 700,
        minWidth: 32,
        textAlign: "center",
      }}
    >
      {score}
    </span>
  );
}

function PlatformBadge({ platform }: { platform: string }) {
  const color = platform === "polymarket" ? "#8b5cf6" : "#06b6d4";
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 8px",
        borderRadius: 4,
        backgroundColor: `${color}22`,
        color,
        fontSize: "0.75rem",
        fontWeight: 500,
      }}
    >
      {platform}
    </span>
  );
}

function formatDescription(desc: string): string {
  // Pull out the quoted question for cleaner display
  const match = desc.match(/"([^"]+)"/);
  return match ? match[1] : desc.slice(0, 80);
}
