"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { toast } from "@/components/ui/toast"

export default function Home() {
  const [status, setStatus] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        setError(null)
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/status`)
        const json = await res.json()
        setStatus(json)
      } catch (e: any) {
        setError(e?.message || "Failed to load status")
        toast({ title: "Failed to load", description: e?.message, variant: 'destructive' })
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const cards = [
    { href: "/research", title: "Research", desc: "Find trends and competitor intel" },
    { href: "/generate", title: "Generate", desc: "Create content and visuals" },
    { href: "/publish", title: "Publish", desc: "Schedule and cross-post" },
    { href: "/orchestrator", title: "Orchestrator", desc: "Run sprints and GTM tests" },
    { href: "/monitoring", title: "Monitoring", desc: "Health, cost, errors" },
    { href: "/intelligence", title: "Intelligence", desc: "Insights and reports" },
  ]

  return (
    <main className="container py-10 space-y-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">CRAEFTO Automation Dashboard</h1>
        <p className="text-muted-foreground">End-to-end controls for research, generation, publishing, and monitoring.</p>
      </header>

      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards.map((card) => (
          <Card key={card.href} className="hover:shadow-sm transition">
            <CardHeader>
              <CardTitle>{card.title}</CardTitle>
              <CardDescription>{card.desc}</CardDescription>
            </CardHeader>
            <CardContent>
              <Link href={card.href}>
                <Button>Open</Button>
              </Link>
            </CardContent>
          </Card>
        ))}
      </section>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle>Backend status</CardTitle>
          <Button variant="outline" onClick={() => window.location.reload()}>Refresh</Button>
        </CardHeader>
        <CardContent>
          {loading && <Skeleton className="h-6 w-48" />}
          {error && <p className="text-sm text-destructive mt-2">{error}</p>}
          {!error && status && (
            <pre className="mt-3 text-xs overflow-auto bg-muted p-3 rounded">{JSON.stringify(status, null, 2)}</pre>
          )}
        </CardContent>
      </Card>
    </main>
  )
}
