"use client"

import { useState } from "react"

export default function MonitoringPage() {
  const [health, setHealth] = useState<any>(null)
  const [perf, setPerf] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = async () => {
    try {
      setLoading(true)
      setError(null)
      const [h, p] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/monitor/health`).then(r => r.json()).catch(() => null),
        fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/monitor/performance`).then(r => r.json()).catch(() => null),
      ])
      setHealth(h)
      setPerf(p)
    } catch (e: any) {
      setError(e?.message || "Failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container py-10 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Monitoring</h1>
        <button onClick={run} className="rounded-md bg-primary px-4 py-2 text-white">{loading ? 'Loading…' : 'Refresh'}</button>
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-lg border p-4">
          <h2 className="font-medium mb-2">Health</h2>
          {health ? <pre className="text-xs bg-muted p-3 rounded overflow-auto">{JSON.stringify(health, null, 2)}</pre> : <p className="text-sm text-muted-foreground">No data</p>}
        </div>
        <div className="rounded-lg border p-4">
          <h2 className="font-medium mb-2">Performance</h2>
          {perf ? <pre className="text-xs bg-muted p-3 rounded overflow-auto">{JSON.stringify(perf, null, 2)}</pre> : <p className="text-sm text-muted-foreground">No data</p>}
        </div>
      </div>
    </main>
  )
}
