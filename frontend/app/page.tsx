"use client"

import Link from "next/link"
import { useEffect, useState } from "react"

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
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <main className="container py-10 space-y-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">CRAEFTO Automation Dashboard</h1>
        <p className="text-muted-foreground">End-to-end controls for research, generation, publishing, and monitoring.</p>
      </header>

      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[
          { href: "/research", title: "Research", desc: "Find trends and competitor intel" },
          { href: "/generate", title: "Generate", desc: "Create content and visuals" },
          { href: "/publish", title: "Publish", desc: "Schedule and cross-post" },
          { href: "/orchestrator", title: "Orchestrator", desc: "Run sprints and GTM tests" },
          { href: "/monitoring", title: "Monitoring", desc: "Health, cost, errors" },
          { href: "/intelligence", title: "Intelligence", desc: "Insights and reports" },
        ].map((card) => (
          <Link key={card.href} href={card.href} className="group rounded-lg border p-5 hover:shadow-sm transition">
            <div className="flex items-center justify-between">
              <h3 className="font-medium">{card.title}</h3>
              <span className="text-primary group-hover:translate-x-0.5 transition">→</span>
            </div>
            <p className="text-sm text-muted-foreground mt-1">{card.desc}</p>
          </Link>
        ))}
      </section>

      <section className="rounded-lg border p-5">
        <div className="flex items-center justify-between">
          <h2 className="font-medium">Backend status</h2>
          {loading && <div className="animate-pulse text-sm text-muted-foreground">Loading…</div>}
        </div>
        {error && <p className="text-sm text-destructive mt-2">{error}</p>}
        {!error && status && (
          <pre className="mt-3 text-xs overflow-auto bg-muted p-3 rounded">{JSON.stringify(status, null, 2)}</pre>
        )}
      </section>
    </main>
  )
}
