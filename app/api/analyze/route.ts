import { runScan } from "@/lib/scanner";
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const demo = searchParams.get("demo") !== "false";
  const top = parseInt(searchParams.get("top") ?? "20", 10);

  const result = await runScan({ demo });

  return NextResponse.json({
    marketsScanned: result.marketsScanned,
    analyses: result.topAnalyses.slice(0, top),
  });
}
