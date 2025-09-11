"use client"

import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, Circle, Clock, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"

export interface ProgressStep {
  id: string
  title: string
  description?: string
  status: "pending" | "running" | "completed" | "error"
  progress?: number
  startTime?: Date
  endTime?: Date
  duration?: number
}

interface ProgressTrackerProps {
  steps: ProgressStep[]
  currentStep?: string
  overallProgress: number
  className?: string
}

const statusIcons = {
  pending: Circle,
  running: Clock,
  completed: CheckCircle,
  error: AlertCircle,
}

const statusColors = {
  pending: "text-muted-foreground",
  running: "text-green-500 animate-pulse",
  completed: "text-green-500",
  error: "text-red-500",
}

export function ProgressTracker({
  steps,
  currentStep,
  overallProgress,
  className
}: ProgressTrackerProps) {
  const getStepStatus = (step: ProgressStep) => {
    if (step.id === currentStep) return "running"
    return step.status
  }

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    return `${(ms / 60000).toFixed(1)}m`
  }

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">
            Progress Tracker
          </CardTitle>
          <Badge className="text-sm !bg-blue-100 !text-blue-800 !border-blue-300">
            {Math.round(overallProgress)}% Complete
          </Badge>
        </div>
        <Progress value={overallProgress} className="mt-2" />
      </CardHeader>
      <CardContent className="space-y-4">
        {steps.map((step, index) => {
          const stepStatus = getStepStatus(step)
          const Icon = statusIcons[stepStatus]
          const isActive = step.id === currentStep
          const isCompleted = step.status === "completed"
          const hasError = step.status === "error"

          return (
            <div
              key={step.id}
              className={cn(
                "flex items-start gap-3 p-3 rounded-lg border transition-all",
                isActive && "border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950/20",
                isCompleted && "border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950/20",
                hasError && "border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950/20"
              )}
            >
              <div className="flex-shrink-0 mt-1">
                <Icon
                  className={cn(
                    "h-5 w-5",
                    statusColors[stepStatus]
                  )}
                />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="text-sm font-medium text-foreground">
                    {step.title}
                  </h4>
                  <Badge
                    variant="outline"
                    className={cn(
                      "text-xs",
                      stepStatus === "running" && "border-green-500 text-green-700",
                      stepStatus === "completed" && "border-green-500 text-green-700",
                      stepStatus === "error" && "border-red-500 text-red-700"
                    )}
                  >
                    {stepStatus.toUpperCase()}
                  </Badge>
                </div>
                {step.description && (
                  <p className="text-xs text-muted-foreground mb-2">
                    {step.description}
                  </p>
                )}
                {step.progress !== undefined && stepStatus === "running" && (
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Progress</span>
                      <span>{Math.round(step.progress)}%</span>
                    </div>
                    <Progress value={step.progress} className="h-1" />
                  </div>
                )}
                {step.duration && (
                  <div className="text-xs text-muted-foreground mt-1">
                    Duration: {formatDuration(step.duration)}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
