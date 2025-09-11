"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/hooks/use-toast"
import { CodeBlock } from "@/components/ui/code-block"
import { ArrowRight, Zap, TrendingUp, FileText, BarChart3, Sparkles } from "lucide-react"

export default function Home() {
  const { addToast } = useToast()
  const [status, setStatus] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentUptime, setCurrentUptime] = useState<number>(0)

  const [researchRes, setResearchRes] = useState<any>(null)
  const [generateRes, setGenerateRes] = useState<any>(null)
  const [flowRes, setFlowRes] = useState<any>(null)

  // Format uptime to hours, minutes, seconds
  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    
    return {
      hours: hours.toString().padStart(2, '0'),
      minutes: minutes.toString().padStart(2, '0'),
      seconds: secs.toString().padStart(2, '0')
    }
  }

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        setError(null)
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/status`)
        const json = await res.json()
        setStatus(json)
        if (json.uptime_seconds) {
          setCurrentUptime(Math.floor(json.uptime_seconds))
        }
      } catch (e: any) {
        setError(e?.message || "Failed to load status")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  // Live uptime counter
  useEffect(() => {
    if (currentUptime > 0) {
      const interval = setInterval(() => {
        setCurrentUptime(prev => prev + 1)
      }, 1000)
      return () => clearInterval(interval)
    }
  }, [currentUptime])

  const runResearch = async () => {
    try {
      setResearchRes(null)
      const r = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/research/trending`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-api-key": process.env.NEXT_PUBLIC_API_KEY || "user_access" },
        body: JSON.stringify({ keywords: ["AI", "SaaS", "design"] })
      })
      const json = await r.json()
      setResearchRes(json)
      addToast({ title: "Research done" })
    } catch (e: any) {
      addToast({ title: "Research failed", description: e?.message, variant: "destructive" })
    }
  }

  const runGenerate = async () => {
    try {
      setGenerateRes(null)
      const topic = "SaaS conversion optimization"
      const r = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/generate/blog`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-api-key": process.env.NEXT_PUBLIC_API_KEY || "user_access" },
        body: JSON.stringify({ topic })
      })
      const json = await r.json()
      setGenerateRes(json)
      addToast({ title: "Generated blog" })
    } catch (e: any) {
      addToast({ title: "Generate failed", description: e?.message, variant: "destructive" })
    }
  }

  const runFlow = async () => {
    try {
      setFlowRes(null)
      // research
      const rr = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/research/trending`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-api-key": process.env.NEXT_PUBLIC_API_KEY || "user_access" },
        body: JSON.stringify({ keywords: ["AI", "SaaS"] })
      })
      const rj = await rr.json()
      // pick a topic
      let picked: string | null = null
      if (rj?.ideas?.length) picked = typeof rj.ideas[0] === 'string' ? rj.ideas[0] : (rj.ideas[0]?.title || rj.ideas[0]?.topic)
      if (!picked && rj?.topics?.length) picked = typeof rj.topics[0] === 'string' ? rj.topics[0] : (rj.topics[0]?.title || rj.topics[0]?.topic)
      if (!picked) picked = "SaaS growth strategy"
      // generate
      const gj = await (await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/generate/blog`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-api-key": process.env.NEXT_PUBLIC_API_KEY || "user_access" },
        body: JSON.stringify({ topic: picked })
      })).json()
      setFlowRes({ picked, research: rj, blog: gj })
      addToast({ title: "Flow succeeded" })
    } catch (e: any) {
      addToast({ title: "Flow failed", description: e?.message, variant: "destructive" })
    }
  }

  return (
    <main className="container py-8 space-y-8">
      {/* System Overview Header */}
      <div className="border-b pb-6">
        <h1 className="text-2xl font-semibold text-foreground mb-2">System Overview</h1>
        <p className="text-muted-foreground">
          Monitor your automation platform status and access core features
        </p>
      </div>

      {/* System Status Cards */}
      <div className="grid gap-6 md:grid-cols-5">
        <Card className="border-border hover:border-slate-200 transition-colors hover:shadow-sm md:col-span-2">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
                <BarChart3 className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="flex items-center gap-2 text-foreground">
                  System Health
                </CardTitle>
                <CardDescription>Backend status and performance</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? <Skeleton className="h-20" /> : (
              <div className="space-y-2">
                {status && (
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="text-muted-foreground">Status</div>
                      <div className={`font-medium capitalize flex items-center gap-2 ${
                        status.status === 'healthy' 
                          ? 'text-green-600' 
                          : status.status === 'running'
                          ? 'text-orange-600'
                          : 'text-foreground'
                      }`}>
                        {status.status === 'running' && (
                          <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-orange-500 rounded-full animate-ping"></div>
                            <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></div>
                          </div>
                        )}
                        {status.status || 'Unknown'}
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Uptime</div>
                      <div className="font-medium text-foreground">
                        {currentUptime > 0 ? (
                          <div className="flex items-center gap-1">
                            <span className="font-mono text-sm bg-orange-50 px-2 py-1 rounded border border-orange-200">
                              <span className="inline-block transition-all duration-300 ease-in-out transform hover:scale-110">
                                {formatUptime(currentUptime).hours}
                              </span>
                              <span className="text-orange-600 animate-pulse mx-1">:</span>
                              <span className="inline-block transition-all duration-300 ease-in-out transform hover:scale-110">
                                {formatUptime(currentUptime).minutes}
                              </span>
                              <span className="text-orange-600 animate-pulse mx-1">:</span>
                              <span className="inline-block transition-all duration-500 ease-in-out transform scale-105 text-gray-600">
                                {formatUptime(currentUptime).seconds}
                              </span>
                            </span>
                            <div className="flex flex-col text-xs text-muted-foreground ml-1">
                              <span>h:m:s</span>
                            </div>
                          </div>
                        ) : (
                          'N/A'
                        )}
                      </div>
                    </div>
                  </div>
                )}
                <CodeBlock value={status || {}} />
              </div>
            )}
          </CardContent>
        </Card>

        {/* One-Click Complete Automation Flow */}
        <Card className="border-2 border-dashed border-slate-200 hover:border-amber-300 hover:bg-gradient-to-br hover:from-amber-50/30 hover:to-yellow-50/30 hover:shadow-lg hover:shadow-amber-100/50 transition-all duration-300 group md:col-span-3">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-lg bg-slate-50 text-slate-600 group-hover:bg-gradient-to-br group-hover:from-amber-500 group-hover:to-yellow-500 group-hover:text-white group-hover:shadow-md transition-all duration-300">
              <Zap className="h-6 w-6 group-hover:animate-pulse" />
            </div>
            <div>
              <CardTitle className="text-xl text-foreground group-hover:text-amber-900 transition-colors duration-300">One-Click Complete Automation Flow</CardTitle>
              <CardDescription className="group-hover:text-amber-700 transition-colors duration-300">Execute the full research → generate → content pipeline</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4 group-hover:text-amber-600 transition-colors duration-300">
            <span className="flex items-center gap-1">
              <TrendingUp className="h-4 w-4 group-hover:text-amber-500 transition-colors duration-300" />
              Research
            </span>
            <ArrowRight className="h-4 w-4 group-hover:text-amber-400 transition-colors duration-300" />
            <span className="flex items-center gap-1">
              <Sparkles className="h-4 w-4 group-hover:text-yellow-500 transition-colors duration-300" />
              Generate
            </span>
            <ArrowRight className="h-4 w-4 group-hover:text-amber-400 transition-colors duration-300" />
            <span className="flex items-center gap-1">
              <FileText className="h-4 w-4 group-hover:text-amber-500 transition-colors duration-300" />
              Content
            </span>
          </div>
          <Button onClick={runFlow} variant="outline" className="gap-2 border-slate-200 text-slate-700 hover:bg-gradient-to-r hover:from-amber-50 hover:to-yellow-50 hover:border-amber-300 hover:text-amber-700 hover:shadow-md transition-all duration-300 group-hover:animate-pulse">
            <Zap className="h-4 w-4" />
            Execute Workflow
          </Button>
          <CodeBlock value={flowRes || { info: "Click to run the complete automation workflow" }} />
        </CardContent>
      </Card>
      </div>

      {/* Quick Access */}
      <div className="flex items-center justify-between pt-6 border-t">
        <p className="text-sm text-muted-foreground">Core Features:</p>
        <div className="flex gap-2">
          <Link href="/research">
            <Button variant="outline" size="sm" className="gap-2 border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300">
              <TrendingUp className="h-3 w-3" />
              Research
            </Button>
          </Link>
          <Link href="/dashboard">
            <Button variant="outline" size="sm" className="gap-2 border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300">
              <BarChart3 className="h-3 w-3" />
              Content Generator
            </Button>
          </Link>
           <Link href="/preview">
             <Button variant="outline" size="sm" className="gap-2 border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300">
               <FileText className="h-3 w-3" />
               Content Preview
             </Button>
           </Link>
        </div>
      </div>
    </main>
  )
}
