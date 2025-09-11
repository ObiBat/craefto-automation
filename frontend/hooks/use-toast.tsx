"use client"

import * as React from "react"

export interface ToastData {
  id: string
  title?: string
  description?: string
  variant?: "default" | "destructive" | "success" | "warning" | "info"
  duration?: number
}

interface ToastContextType {
  toasts: ToastData[]
  addToast: (toast: Omit<ToastData, "id">) => void
  removeToast: (id: string) => void
  clearToasts: () => void
}

const ToastContext = React.createContext<ToastContextType | undefined>(undefined)

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<ToastData[]>([])

  const addToast = React.useCallback((toast: Omit<ToastData, "id">) => {
    const id = Math.random().toString(36).substr(2, 9)
    setToasts((prev) => [...prev, { ...toast, id }])
  }, [])

  const removeToast = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  const clearToasts = React.useCallback(() => {
    setToasts([])
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, clearToasts }}>
      {children}
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = React.useContext(ToastContext)
  if (context === undefined) {
    throw new Error("useToast must be used within a ToastProvider")
  }
  return context
}

// Convenience functions
export const toast = {
  success: (title: string, description?: string, duration?: number) => {
    // This will be used with the hook
    return { title, description, variant: "success" as const, duration }
  },
  error: (title: string, description?: string, duration?: number) => {
    return { title, description, variant: "destructive" as const, duration }
  },
  warning: (title: string, description?: string, duration?: number) => {
    return { title, description, variant: "warning" as const, duration }
  },
  info: (title: string, description?: string, duration?: number) => {
    return { title, description, variant: "info" as const, duration }
  },
  default: (title: string, description?: string, duration?: number) => {
    return { title, description, variant: "default" as const, duration }
  },
}
