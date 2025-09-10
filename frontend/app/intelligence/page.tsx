"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { toast } from "@/components/ui/toast"

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
      toast({ title: "Loaded", description: path })
    } catch (e: any) {
      setError(e?.message || "Failed")
      toast({ title: "Request failed", description: e?.message, variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container py-10 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Intelligence</CardTitle>
          <CardDescription>Insights and reports</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => call('/intelligence/performance?days=7')} disabled={loading}>{loading ? '…' : 'Performance (7d)'}</Button>
            <Button onClick={() => call('/intelligence/report?report_type=daily')} disabled={loading}>{loading ? '…' : 'Daily Report'}</Button>
            <Button onClick={() => call('/intelligence/insights')} disabled={loading}>{loading ? '…' : 'Insights'}</Button>
            <Button onClick={() => call('/intelligence/competitors')} disabled={loading}>{loading ? '…' : 'Competitors'}</Button>
          </div>
          {loading && <Skeleton className="h-6 w-64" />}
          {error && <p className="text-sm text-destructive">{error}</p>}
          {data && <pre className="text-xs bg-muted p-3 rounded overflow-auto">{JSON.stringify(data, null, 2)}</pre>}
        </CardContent>
      </Card>
    </main>
  )
}
