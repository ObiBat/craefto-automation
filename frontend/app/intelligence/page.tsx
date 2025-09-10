"use client"

import { useState } from "react"

export default function IntelligencePage() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const call = async (path: string) => {
    try {
      setLoading(true)
      setError(null)
      setData(null)
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}${path}`)
      const json = await res.json()
      setData(json)
    } catch (e: any) {
      setError(e?.message || "Failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container py-10 space-y-6">
      <h1 className="text-xl font-semibold">Intelligence</h1>
      <div className="flex flex-wrap gap-2">
        <button onClick={() => call('/intelligence/performance?days=7')} className="rounded-md bg-primary px-4 py-2 text-white">{loading ? '…' : 'Performance (7d)'}</button>
        <button onClick={() => call('/intelligence/report?report_type=daily')} className="rounded-md bg-primary px-4 py-2 text-white">{loading ? '…' : 'Daily Report'}</button>
        <button onClick={() => call('/intelligence/insights')} className="rounded-md bg-primary px-4 py-2 text-white">{loading ? '…' : 'Insights'}</button>
        <button onClick={() => call('/intelligence/competitors')} className="rounded-md bg-primary px-4 py-2 text-white">{loading ? '…' : 'Competitors'}</button>
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      {data && <pre className="text-xs bg-muted p-3 rounded overflow-auto">{JSON.stringify(data, null, 2)}</pre>}
    </main>
  )
}
