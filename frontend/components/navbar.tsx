"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { getApiStatus, type ApiHealth } from "@/lib/api"
import { Badge } from "@/components/ui/badge"

function StatusBadge({ health }: { health?: ApiHealth | null }) {
  const status = health?.status || "down"
  const variant = status === "healthy" ? "default" : status === "degraded" ? "secondary" : "destructive"
  const label = status === "healthy" ? "API: Healthy" : status === "degraded" ? "API: Degraded" : "API: Down"
  return <Badge variant={variant}>{label}{health?.latencyMs ? ` • ${health.latencyMs}ms` : ""}</Badge>
}

export default function Navbar() {
  const [health, setHealth] = useState<ApiHealth | null>(null)

  useEffect(() => {
    let mounted = true
    let timer: any
    const tick = async () => {
      const h = await getApiStatus()
      if (mounted) setHealth(h)
      timer = setTimeout(tick, 10_000)
    }
    tick()
    return () => { mounted = false; if (timer) clearTimeout(timer) }
  }, [])

  const linkCls = "text-sm text-muted-foreground hover:text-foreground"

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/80 backdrop-blur">
      <div className="container flex h-14 items-center justify-between">
        <nav className="flex items-center gap-4">
          <Link href="/" className="font-semibold">CRAEFTO</Link>
          <Link href="/research" className={linkCls}>Research</Link>
          <Link href="/generate" className={linkCls}>Generate</Link>
          <Link href="/publish" className={linkCls}>Publish</Link>
          <Link href="/orchestrator" className={linkCls}>Orchestrator</Link>
          <Link href="/monitoring" className={linkCls}>Monitoring</Link>
          <Link href="/intelligence" className={linkCls}>Intelligence</Link>
        </nav>
        <div className="flex items-center gap-2">
          <StatusBadge health={health} />
        </div>
      </div>
    </header>
  )
}
