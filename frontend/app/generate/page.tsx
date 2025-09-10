"use client"

import { useState } from "react"

export default function GeneratePage() {
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [topic, setTopic] = useState("SaaS Growth Strategies")

  const call = async (path: string, body: any) => {
    try {
      setLoading(true)
      setError(null)
      setResult(null)
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-api-key": process.env.NEXT_PUBLIC_API_KEY || "user_access" },
        body: JSON.stringify(body)
      })
      const json = await res.json()
      setResult(json)
    } catch (e: any) {
      setError(e?.message || "Request failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container py-10 space-y-6">
      <h1 className="text-xl font-semibold">Generate</h1>

      <div className="flex gap-2">
        <input value={topic} onChange={(e) => setTopic(e.target.value)} className="w-full rounded-md border px-3 py-2" />
        <button onClick={() => call('/api/generate/blog', { topic })} className="rounded-md bg-primary px-4 py-2 text-white">{loading ? '...' : 'Blog'}</button>
        <button onClick={() => call('/api/generate/campaign', { topic })} className="rounded-md bg-primary px-4 py-2 text-white">{loading ? '...' : 'Email'}</button>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}
      {result && <pre className="text-xs bg-muted p-3 rounded overflow-auto">{JSON.stringify(result, null, 2)}</pre>}
    </main>
  )
}
