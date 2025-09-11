"use client"

import { useState } from "react"
import { clsx } from "clsx"
import { Button } from "@/components/ui/button"

export function CodeBlock({ value, className }: { value: any; className?: string }) {
  const [copied, setCopied] = useState(false)
  const text = typeof value === "string" ? value : JSON.stringify(value, null, 2)
  return (
    <div className={clsx("relative rounded-md border bg-muted p-3", className)}>
      <pre className="overflow-auto text-xs leading-relaxed whitespace-pre-wrap"><code>{text}</code></pre>
      <div className="absolute top-2 right-2">
        <Button size="sm" variant="outline" onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1500) }}>{copied ? "Copied" : "Copy"}</Button>
      </div>
    </div>
  )
}
