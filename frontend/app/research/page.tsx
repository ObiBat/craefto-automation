"use client"

import { useState } from "react"

export default function ResearchPage() {
  const [topics, setTopics] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const runTrending = async () => {
    try {
      setLoading(true)
      setError(null)
      setTopics(null)
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/research/trending`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-api-key": process.env.NEXT_PUBLIC_API_KEY || "user_access" },
        body: JSON.stringify({ keywords: ["AI", "SaaS"] })
      })
      const json = await res.json()
      setTopics(json)
    } catch (e: any) {
      setError(e?.message || "Failed to get trending")
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container py-10 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Research</h1>
        <button onClick={runTrending} className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-white hover:opacity-90">
          {loading ? "Running…" : "Find Trending"}
        </button>
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      {topics && (
        <pre className="mt-3 text-xs overflow-auto bg-muted p-3 rounded">{JSON.stringify(topics, null, 2)}</pre>
      )}
    </main>
  )
}
