import type { NextRequest } from "next/server"

export const runtime = "nodejs"

const BACKEND_URL = process.env.ANALYST_API_URL ?? "http://localhost:8000"

export async function POST(req: NextRequest) {
  const formData = await req.formData()

  const upstream = await fetch(`${BACKEND_URL}/api/analyze`, {
    method: "POST",
    body: formData,
  })

  if (!upstream.ok || !upstream.body) {
    return new Response(
      JSON.stringify({ type: "error", message: `Backend returned ${upstream.status}` }) + "\n",
      {
        status: upstream.status,
        headers: { "content-type": "application/x-ndjson; charset=utf-8" },
      },
    )
  }

  return new Response(upstream.body, {
    headers: {
      "content-type": "application/x-ndjson; charset=utf-8",
      "cache-control": "no-cache, no-transform",
    },
  })
}
