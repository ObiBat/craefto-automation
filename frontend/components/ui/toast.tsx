"use client"

import { useEffect, useState } from "react"
import { clsx } from "clsx"

let listeners: ((t: ToastData) => void)[] = []

export type ToastData = { title?: string; description?: string; variant?: 'default' | 'destructive' }

export function toast(data: ToastData) {
  listeners.forEach((l) => l(data))
}

export function Toaster() {
  const [queue, setQueue] = useState<ToastData[]>([])

  useEffect(() => {
    const handler = (t: ToastData) => {
      setQueue((q) => [...q, t])
      setTimeout(() => setQueue((q) => q.slice(1)), 3000)
    }
    listeners.push(handler)
    return () => {
      listeners = listeners.filter((l) => l !== handler)
    }
  }, [])

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2">
      {queue.map((t, i) => (
        <div key={i} className={clsx("w-80 rounded-md border p-4 shadow bg-card", t.variant === 'destructive' && 'border-destructive')}>
          {t.title && <div className="font-medium">{t.title}</div>}
          {t.description && <div className="text-sm text-muted-foreground">{t.description}</div>}
        </div>
      ))}
    </div>
  )
}
