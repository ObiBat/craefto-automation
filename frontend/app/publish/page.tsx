"use client"

import { useState } from "react"

export default function PublishPage() {
  const [resp, setResp] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = async () => {
    try {
      setLoading(true)
      setError(null)
      setResp(null)
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/publish/batch`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-api-key": process.env.NEXT_PUBLIC_API_KEY || "user_access" },
        body: JSON.stringify({ platforms: ["twitter", "linkedin"] })
      })
      const json = await res.json()
      setResp(json)
    } catch (e: any) {
      setError(e?.message || "Failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container py-10 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Publish</h1>
        <button onClick={run} className="rounded-md bg-primary px-4 py-2 text-white">{loading ? 'Working…' : 'Run Batch'}</button>
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      {resp && <pre className="text-xs bg-muted p-3 rounded overflow-auto">{JSON.stringify(resp, null, 2)}</pre>}
    </main>
  )
}
