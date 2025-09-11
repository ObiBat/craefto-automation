"use client"

import * as React from "react"
import { ConsoleEntry } from "@/components/live-console"

export function useLiveConsole() {
  const [entries, setEntries] = React.useState<ConsoleEntry[]>([])
  const [isRunning, setIsRunning] = React.useState(false)

  const addEntry = React.useCallback((
    level: ConsoleEntry["level"],
    message: string,
    data?: any,
    source?: string
  ) => {
    const entry: ConsoleEntry = {
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date(),
      level,
      message,
      data,
      source
    }
    setEntries(prev => [...prev, entry])
  }, [])

  const clearEntries = React.useCallback(() => {
    setEntries([])
  }, [])

  const resetConsole = React.useCallback(() => {
    setEntries([])
    setIsRunning(false)
  }, [])

  const startConsole = React.useCallback(() => {
    setIsRunning(true)
    addEntry("info", "Console started", null, "System")
  }, [addEntry])

  const stopConsole = React.useCallback(() => {
    setIsRunning(false)
    addEntry("info", "Console stopped", null, "System")
  }, [addEntry])

  // Convenience methods for different log levels
  const logInfo = React.useCallback((message: string, data?: any, source?: string) => {
    addEntry("info", message, data, source)
  }, [addEntry])

  const logSuccess = React.useCallback((message: string, data?: any, source?: string) => {
    addEntry("success", message, data, source)
  }, [addEntry])

  const logWarning = React.useCallback((message: string, data?: any, source?: string) => {
    addEntry("warning", message, data, source)
  }, [addEntry])

  const logError = React.useCallback((message: string, data?: any, source?: string) => {
    addEntry("error", message, data, source)
  }, [addEntry])

  const logDebug = React.useCallback((message: string, data?: any, source?: string) => {
    addEntry("debug", message, data, source)
  }, [addEntry])

  return {
    entries,
    isRunning,
    addEntry,
    clearEntries,
    resetConsole,
    startConsole,
    stopConsole,
    logInfo,
    logSuccess,
    logWarning,
    logError,
    logDebug
  }
}
