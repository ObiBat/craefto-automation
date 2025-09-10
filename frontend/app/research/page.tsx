"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { toast } from "@/components/ui/toast"

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
      toast({ title: "Trending ready", description: "Fetched trending ideas." })
    } catch (e: any) {
      setError(e?.message || "Failed to get trending")
      toast({ title: "Research failed", description: e?.message, variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container py-10 space-y-6">
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>Research</CardTitle>
            <CardDescription>Run trending topic detection</CardDescription>
          </div>
          <Button onClick={runTrending} disabled={loading}>{loading ? "Running…" : "Find Trending"}</Button>
        </CardHeader>
        <CardContent>
          {loading && <Skeleton className="h-6 w-64" />}
          {error && <p className="text-sm text-destructive">{error}</p>}
          {topics && (
            <pre className="mt-3 text-xs overflow-auto bg-muted p-3 rounded">{JSON.stringify(topics, null, 2)}</pre>
          )}
        </CardContent>
      </Card>
    </main>
  )
}
