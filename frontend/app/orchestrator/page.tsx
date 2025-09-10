"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { toast } from "@/components/ui/toast"

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
      toast({ title: "Started", description: path })
    } catch (e: any) {
      setError(e?.message || "Failed")
      toast({ title: "Orchestration failed", description: e?.message, variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container py-10 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Orchestrator</CardTitle>
          <CardDescription>Run sprints and optimization cycles</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => call('/orchestrator/content-sprint', { focus: 'gtm' })} disabled={loading}>{loading ? '…' : 'Manual Content Sprint'}</Button>
            <Button onClick={() => call('/orchestrator/gtm-test', { hypothesis: 'Visual templates drive 3x engagement' })} disabled={loading}>{loading ? '…' : 'Run GTM Test'}</Button>
            <Button onClick={() => call('/orchestrator/optimization-cycle', {})} disabled={loading}>{loading ? '…' : 'Optimization Cycle'}</Button>
          </div>
          {loading && <Skeleton className="h-6 w-64" />}
          {error && <p className="text-sm text-destructive">{error}</p>}
          {data && <pre className="text-xs bg-muted p-3 rounded overflow-auto">{JSON.stringify(data, null, 2)}</pre>}
        </CardContent>
      </Card>
    </main>
  )
}
