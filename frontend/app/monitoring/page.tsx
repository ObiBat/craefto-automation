"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { toast } from "@/components/ui/toast"

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
      toast({ title: "Monitoring updated" })
    } catch (e: any) {
      setError(e?.message || "Failed")
      toast({ title: "Monitoring failed", description: e?.message, variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container py-10 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Monitoring</h1>
        <Button onClick={run} disabled={loading}>{loading ? 'Loading…' : 'Refresh'}</Button>
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Health</CardTitle>
            <CardDescription>System availability and score</CardDescription>
          </CardHeader>
          <CardContent>
            {loading && <Skeleton className="h-6 w-64" />}
            {health ? <pre className="text-xs bg-muted p-3 rounded overflow-auto">{JSON.stringify(health, null, 2)}</pre> : <p className="text-sm text-muted-foreground">No data</p>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Performance</CardTitle>
            <CardDescription>Throughput, latency, costs</CardDescription>
          </CardHeader>
          <CardContent>
            {loading && <Skeleton className="h-6 w-64" />}
            {perf ? <pre className="text-xs bg-muted p-3 rounded overflow-auto">{JSON.stringify(perf, null, 2)}</pre> : <p className="text-sm text-muted-foreground">No data</p>}
          </CardContent>
        </Card>
      </div>
    </main>
  )
}
