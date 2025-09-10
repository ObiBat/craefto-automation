"use client"

import { useState } from "react"

export default function OrchestratorPage() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const call = async (path: string, body: any) => {
    try {
      setLoading(true)
      setError(null)
      setData(null)
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-api-key": process.env.NEXT_PUBLIC_API_KEY || "user_access" },
        body: JSON.stringify(body)
      })
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
      <h1 className="text-xl font-semibold">Orchestrator</h1>
      <div className="flex flex-wrap gap-2">
        <button onClick={() => call('/orchestrator/content-sprint', { focus: 'gtm' })} className="rounded-md bg-primary px-4 py-2 text-white">{loading ? '…' : 'Manual Content Sprint'}</button>
        <button onClick={() => call('/orchestrator/gtm-test', { hypothesis: 'Visual templates drive 3x engagement' })} className="rounded-md bg-primary px-4 py-2 text-white">{loading ? '…' : 'Run GTM Test'}</button>
        <button onClick={() => call('/orchestrator/optimization-cycle', {})} className="rounded-md bg-primary px-4 py-2 text-white">{loading ? '…' : 'Optimization Cycle'}</button>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}
      {data && <pre className="text-xs bg-muted p-3 rounded overflow-auto">{JSON.stringify(data, null, 2)}</pre>}
    </main>
  )
}
