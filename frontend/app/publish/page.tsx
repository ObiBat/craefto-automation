"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { toast } from "@/components/ui/toast"

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
      toast({ title: "Batch scheduled", description: "Publishing flow executed." })
    } catch (e: any) {
      setError(e?.message || "Failed")
      toast({ title: "Publish failed", description: e?.message, variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container py-10 space-y-6">
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>Publish</CardTitle>
            <CardDescription>Batch publish to platforms</CardDescription>
          </div>
          <Button onClick={run} disabled={loading}>{loading ? 'Working…' : 'Run Batch'}</Button>
        </CardHeader>
        <CardContent>
          {loading && <Skeleton className="h-6 w-64" />}
          {error && <p className="text-sm text-destructive">{error}</p>}
          {resp && <pre className="text-xs bg-muted p-3 rounded overflow-auto">{JSON.stringify(resp, null, 2)}</pre>}
        </CardContent>
      </Card>
    </main>
  )
}
