import { runScan } from "@/lib/scanner";
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const demo = searchParams.get("demo") !== "false"; // default to demo
  const minProfitPct = parseFloat(searchParams.get("minProfitPct") ?? "0.5");

  const result = await runScan({
    demo,
    minProfitPct,
    enablePolymarket: true,
    enableKalshi: true,
  });

  return NextResponse.json(result);
}
