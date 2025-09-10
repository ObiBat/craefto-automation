"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { toast } from "@/components/ui/toast"

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
      toast({ title: "Generated", description: "Content created." })
    } catch (e: any) {
      setError(e?.message || "Request failed")
      toast({ title: "Generation failed", description: e?.message, variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container py-10 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Generate</CardTitle>
          <CardDescription>Create content and campaigns</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <input value={topic} onChange={(e) => setTopic(e.target.value)} className="w-full rounded-md border px-3 py-2" />
            <Button onClick={() => call('/api/generate/blog', { topic })} disabled={loading}>{loading ? '...' : 'Blog'}</Button>
            <Button onClick={() => call('/api/generate/campaign', { topic })} disabled={loading}>{loading ? '...' : 'Email'}</Button>
          </div>

          {loading && <Skeleton className="h-6 w-64" />}
          {error && <p className="text-sm text-destructive">{error}</p>}
          {result && <pre className="text-xs bg-muted p-3 rounded overflow-auto">{JSON.stringify(result, null, 2)}</pre>}
        </CardContent>
      </Card>
    </main>
  )
}
