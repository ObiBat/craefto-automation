"use client"

import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Trash2, Play, Pause, RotateCcw } from "lucide-react"
import { cn } from "@/lib/utils"

export interface ConsoleEntry {
  id: string
  timestamp: Date
  level: "info" | "success" | "warning" | "error" | "debug"
  message: string
  data?: any
  source?: string
}

interface LiveConsoleProps {
  entries: ConsoleEntry[]
  onClear: () => void
  onStart: () => void
  onStop: () => void
  onReset: () => void
  isRunning: boolean
  className?: string
}

const levelColors = {
  info: "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-100",
  success: "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-100",
  warning: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-100",
  error: "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-100",
  debug: "bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-100",
}

const levelIcons = {
  info: "ℹ️",
  success: "✅",
  warning: "⚠️",
  error: "❌",
  debug: "🔍",
}

export function LiveConsole({
  entries,
  onClear,
  onStart,
  onStop,
  onReset,
  isRunning,
  className
}: LiveConsoleProps) {
  const scrollAreaRef = React.useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new entries are added
  React.useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }, [entries])

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour12: false, 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      fractionalSecondDigits: 3
    })
  }

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <div className={cn(
              "w-2 h-2 rounded-full",
              isRunning ? "bg-green-500 animate-pulse" : "bg-gray-400"
            )} />
            Live Console
            <Badge className="ml-2 !bg-gray-100 !text-gray-800 !border-gray-300">
              {entries.length} entries
            </Badge>
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={isRunning ? onStop : onStart}
              className="flex items-center gap-1"
            >
              {isRunning ? <Pause className="h-3 w-3" /> : <Play className="h-3 w-3" />}
              {isRunning ? "Stop" : "Start"}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={onReset}
              className="flex items-center gap-1"
            >
              <RotateCcw className="h-3 w-3" />
              Reset
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={onClear}
              className="flex items-center gap-1"
            >
              <Trash2 className="h-3 w-3" />
              Clear
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea ref={scrollAreaRef} className="h-64 w-full">
          <div className="p-4 space-y-2">
            {entries.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                <div className="text-4xl mb-2">📝</div>
                <p>Console is empty</p>
                <p className="text-sm">Start an operation to see live logs</p>
              </div>
            ) : (
              entries.map((entry) => (
                <div
                  key={entry.id}
                  className="flex items-start gap-3 p-2 rounded-md hover:bg-muted/50 transition-colors"
                >
                  <div className="flex-shrink-0 mt-0.5">
                    <span className="text-sm">{levelIcons[entry.level]}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge
                        variant="secondary"
                        className={cn("text-xs", levelColors[entry.level])}
                      >
                        {entry.level.toUpperCase()}
                      </Badge>
                      <span className="text-xs text-muted-foreground font-mono">
                        {formatTimestamp(entry.timestamp)}
                      </span>
                      {entry.source && (
                        <Badge className="text-xs !bg-blue-100 !text-blue-800 !border-blue-300">
                          {entry.source}
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-foreground break-words">
                      {entry.message}
                    </p>
                    {entry.data && (
                      <details className="mt-2">
                        <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
                          View Data
                        </summary>
                        <pre className="mt-1 text-xs bg-muted p-2 rounded overflow-x-auto">
                          {JSON.stringify(entry.data, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
