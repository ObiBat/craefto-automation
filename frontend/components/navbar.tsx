"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { getApiStatus, type ApiHealth } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Logo } from "@/components/ui/logo"
import { Settings, Zap, Search, Wand2, Send, BarChart3, Brain, Menu } from "lucide-react"

function StatusBadge({ health }: { health?: ApiHealth | null }) {
  console.log('🔍 StatusBadge rendered with health:', health)
  const status = health?.status || "down"
  const getStatusStyle = (status: string) => {
    switch (status) {
      case "healthy":
        return "!bg-green-100 !text-green-800 !border-green-300"
      case "degraded":
        return "!bg-orange-100 !text-orange-800 !border-orange-300"
      default:
        return "!bg-red-100 !text-red-800 !border-red-300"
    }
  }
  const label = status === "healthy" ? "API: Healthy" : status === "degraded" ? "API: Degraded" : "API: Down"
  console.log('🔍 StatusBadge status:', status, 'label:', label)
  return <Badge className={`text-xs ${getStatusStyle(status)}`}>{label}{health?.latencyMs ? ` • ${health.latencyMs}ms` : ""}</Badge>
}

const FeatureDrawer = () => {
  const features = [
    {
      name: "Generate",
      href: "/generate", 
      icon: Wand2,
      description: "AI content & visual generation",
      status: "beta"
    },
    {
      name: "Publish",
      href: "/publish",
      icon: Send,
      description: "Multi-platform content publishing",
      status: "coming-soon"
    },
    {
      name: "Orchestrator",
      href: "/orchestrator",
      icon: Settings,
      description: "End-to-end automation workflows",
      status: "beta"
    },
    {
      name: "Monitoring",
      href: "/monitoring",
      icon: BarChart3,
      description: "Performance analytics & insights",
      status: "beta"
    },
    {
      name: "Intelligence",
      href: "/intelligence",
      icon: Brain,
      description: "AI-powered business insights",
      status: "beta"
    }
  ]

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "beta":
        return <Badge className="text-xs !bg-orange-100 !text-orange-800 !border-orange-300">Beta</Badge>
      case "coming-soon":
        return <Badge className="text-xs !bg-gray-100 !text-gray-800 !border-gray-300">Soon</Badge>
      default:
        return null
    }
  }

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm" className="h-9 px-3 bg-gradient-to-r from-slate-50 to-gray-50 hover:from-slate-100 hover:to-gray-100 border border-slate-200/50 hover:border-slate-300/50 transition-all duration-200">
          <Menu className="h-4 w-4 mr-2 text-slate-600" />
          <span className="text-slate-700 font-medium">Advanced Features</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-80 bg-gradient-to-br from-slate-50/50 to-gray-50/50">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-sm">
              <Zap className="h-4 w-4" />
            </div>
            <span className="bg-gradient-to-r from-slate-800 to-gray-700 bg-clip-text text-transparent font-semibold">
              Advanced Features
            </span>
          </SheetTitle>
          <SheetDescription className="text-slate-600">
            Explore powerful automation tools for scaling your content operations
          </SheetDescription>
        </SheetHeader>
        <div className="mt-6 space-y-3">
          {features.map((feature) => {
            const Icon = feature.icon
            return (
              <Link
                key={feature.name}
                href={feature.href}
                className="block p-4 rounded-xl border border-slate-200/60 hover:border-amber-300/60 bg-white/80 hover:bg-gradient-to-br hover:from-amber-50/30 hover:to-yellow-50/30 backdrop-blur-sm hover:shadow-lg hover:shadow-amber-100/50 transition-all duration-300 group"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2.5 rounded-lg bg-gradient-to-br from-slate-100 to-gray-100 text-slate-700 group-hover:from-amber-500 group-hover:to-yellow-500 group-hover:text-white group-hover:shadow-md transition-all duration-300">
                    <Icon className="h-4 w-4 group-hover:animate-pulse" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-sm text-slate-800 group-hover:text-amber-900 transition-colors duration-300">{feature.name}</h3>
                      {getStatusBadge(feature.status)}
                    </div>
                    <p className="text-xs text-slate-600 group-hover:text-amber-700 leading-relaxed transition-colors duration-300">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </Link>
            )
          })}
        </div>
        <div className="mt-6 p-4 rounded-xl bg-gradient-to-r from-slate-100/50 to-gray-100/50 border border-dashed border-slate-300/60">
          <p className="text-xs text-slate-500 text-center font-medium">
            ✨ Additional features in development
          </p>
        </div>
      </SheetContent>
    </Sheet>
  )
}

export default function Navbar() {
  const [health, setHealth] = useState<ApiHealth | null>(null)

  useEffect(() => {
    let mounted = true
    let timer: any
    const tick = async () => {
      console.log('🔍 Navbar tick called')
      try {
        const h = await getApiStatus()
        console.log('🔍 Navbar got health:', h)
        if (mounted) setHealth(h)
      } catch (error) {
        console.log('🔍 Navbar error:', error)
        if (mounted) setHealth({ ok: false, status: "down", message: "Error" })
      }
      timer = setTimeout(tick, 10_000)
    }
    tick()
    return () => { mounted = false; if (timer) clearTimeout(timer) }
  }, [])

  const linkCls = "text-sm font-medium text-muted-foreground hover:text-foreground transition-colors px-3 py-2 rounded-md hover:bg-muted"

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2 font-bold text-lg">
            <Logo size="md" />
            <span className="text-foreground">
              Craefto Automation
            </span>
          </Link>
          
          {/* Primary Navigation */}
          <nav className="flex items-center gap-1">
            <Link href="/research" className={linkCls}>Research</Link>
            <Link href="/dashboard" className={linkCls}>Content Generator</Link>
            <Link href="/preview" className={linkCls}>Content Preview</Link>
          </nav>
        </div>
        
        <div className="flex items-center gap-3">
          <FeatureDrawer />
          <StatusBadge health={health} />
        </div>
      </div>
    </header>
  )
}
