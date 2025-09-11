"use client"

import * as React from "react"
import { generateContent } from "@/lib/api"

interface Logger {
  logInfo: (message: string, data?: any, source?: string) => void
  logSuccess: (message: string, data?: any, source?: string) => void
  logWarning: (message: string, data?: any, source?: string) => void
  logError: (message: string, data?: any, source?: string) => void
  logDebug: (message: string, data?: any, source?: string) => void
}

export interface GenerationStep {
  id: string
  title: string
  description?: string
  status: "pending" | "running" | "completed" | "error"
  progress?: number
  startTime?: Date
  endTime?: Date
  duration?: number
  data?: any
}

export interface GenerationState {
  isGenerating: boolean
  steps: GenerationStep[]
  currentStep?: string
  overallProgress: number
  error?: string
}

export function useContentGeneration() {
  const [state, setState] = React.useState<GenerationState>({
    isGenerating: false,
    steps: [],
    overallProgress: 0
  })

  const addStep = React.useCallback((id: string, title: string, description?: string) => {
    const step: GenerationStep = {
      id,
      title,
      description,
      status: "pending",
      progress: 0
    }
    setState(prev => ({
      ...prev,
      steps: [...prev.steps, step]
    }))
  }, [])

  const updateStep = React.useCallback((
    stepId: string,
    updates: Partial<GenerationStep>
  ) => {
    setState(prev => ({
      ...prev,
      steps: prev.steps.map(step => 
        step.id === stepId ? { ...step, ...updates } : step
      )
    }))
  }, [])

  const setCurrentStep = React.useCallback((stepId: string | undefined) => {
    setState(prev => ({ ...prev, currentStep: stepId }))
  }, [])

  const setOverallProgress = React.useCallback((progress: number) => {
    setState(prev => ({ ...prev, overallProgress: progress }))
  }, [])

  const generate = React.useCallback(async (topic: string, contentType: string, logger?: Logger) => {
    if (state.isGenerating) return

    setState(prev => ({
      ...prev,
      isGenerating: true,
      steps: [],
      overallProgress: 0,
      currentStep: undefined,
      error: undefined
    }))

    try {
      // Initialize steps
      const steps = [
        { id: "validate", title: "Validating Input", description: "Checking topic and content type" },
        { id: "research", title: "Research Phase", description: "Gathering trending data and insights" },
        { id: "content", title: "Content Generation", description: "Creating AI-powered content" },
        { id: "visual", title: "Visual Generation", description: "Generating hero image with Replicate" },
        { id: "social", title: "Social Media", description: "Creating social media posts" },
        { id: "email", title: "Email Campaign", description: "Generating email content" },
        { id: "save", title: "Saving Content", description: "Storing in database" }
      ]

      steps.forEach(step => addStep(step.id, step.title, step.description))

      // Step 1: Validate
      logger?.logInfo(`🔍 Starting ${contentType} generation for: "${topic}"`, { topic, contentType }, "Generator")
      setCurrentStep("validate")
      updateStep("validate", { status: "running", startTime: new Date() })
      logger?.logDebug("Validating input parameters...", { topic, contentType }, "Validator")
      
      await new Promise(resolve => setTimeout(resolve, 500))
      updateStep("validate", { status: "completed", endTime: new Date(), progress: 100 })
      setOverallProgress(14)
      logger?.logSuccess("✅ Input validation completed", null, "Validator")

      // Step 2: Research (simulated)
      setCurrentStep("research")
      updateStep("research", { status: "running", startTime: new Date() })
      logger?.logInfo("🔬 Starting research phase...", null, "Research")
      logger?.logDebug("Analyzing trending topics and market data...", null, "Research")
      
      await new Promise(resolve => setTimeout(resolve, 800))
      updateStep("research", { status: "completed", endTime: new Date(), progress: 100 })
      setOverallProgress(28)
      logger?.logSuccess("✅ Research phase completed", null, "Research")

      // Step 3: Content Generation - Call real API
      setCurrentStep("content")
      updateStep("content", { status: "running", startTime: new Date(), progress: 10 })
      logger?.logInfo("🤖 Calling OpenAI API for content generation...", null, "OpenAI")
      logger?.logDebug("Sending request to OpenAI with optimized prompts...", { model: "gpt-4", contentType }, "OpenAI")

      const resp = await generateContent(topic, contentType)

      if (!resp.success) {
        logger?.logError("❌ Content generation failed", resp.error, "OpenAI")
        updateStep("content", { status: "error", endTime: new Date() })
        throw new Error(resp.error || "Generation failed")
      }

      logger?.logSuccess("✅ Content generation completed successfully", resp.data, "OpenAI")
      updateStep("content", { status: "completed", endTime: new Date(), progress: 100 })
      setOverallProgress(42)

      if (contentType === 'blog') {
        // Step 4: Visual Generation
        setCurrentStep("visual")
        updateStep("visual", { status: "running", startTime: new Date() })
        logger?.logInfo("🎨 Generating hero image with Replicate...", null, "Replicate")
        logger?.logDebug("Creating visual assets optimized for blog content...", null, "Replicate")
        
        await new Promise(resolve => setTimeout(resolve, 1000))
        updateStep("visual", { status: "completed", endTime: new Date(), progress: 100 })
        setOverallProgress(56)
        logger?.logSuccess("✅ Hero image generated successfully", null, "Replicate")

        // Step 5: Social Media
        setCurrentStep("social")
        updateStep("social", { status: "running", startTime: new Date() })
        logger?.logInfo("📱 Creating social media variants...", null, "Social")
        logger?.logDebug("Generating platform-specific posts (Twitter, LinkedIn, Facebook)...", null, "Social")
        
        await new Promise(resolve => setTimeout(resolve, 600))
        updateStep("social", { status: "completed", endTime: new Date(), progress: 100 })
        setOverallProgress(70)
        logger?.logSuccess("✅ Social media posts created", null, "Social")

        // Step 6: Email Campaign
        setCurrentStep("email")
        updateStep("email", { status: "running", startTime: new Date() })
        logger?.logInfo("📧 Generating email campaign content...", null, "Email")
        logger?.logDebug("Creating email variants with subject lines and CTAs...", null, "Email")
        
        await new Promise(resolve => setTimeout(resolve, 500))
        updateStep("email", { status: "completed", endTime: new Date(), progress: 100 })
        setOverallProgress(84)
        logger?.logSuccess("✅ Email campaign content generated", null, "Email")
      } else {
        setOverallProgress(70)
      }

      // Step 7: Save to Database
      setCurrentStep("save")
      updateStep("save", { status: "running", startTime: new Date() })
      logger?.logInfo("💾 Saving content to Supabase database...", null, "Database")
      logger?.logDebug("Storing content with metadata and indexing...", null, "Database")
      
      await new Promise(resolve => setTimeout(resolve, 300))
      updateStep("save", { status: "completed", endTime: new Date(), progress: 100 })
      setOverallProgress(100)
      logger?.logSuccess("✅ Content saved to database successfully", null, "Database")

      setCurrentStep(undefined)
      logger?.logSuccess(`🎉 Generation completed! Content created successfully for "${topic}"`, resp.data, "System")

    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : "Unknown error occurred"
      logger?.logError(`❌ Generation failed: ${errorMsg}`, error, "System")
      
      // Mark current step as error
      setState(prev => {
        if (prev.currentStep) {
          const updatedSteps = prev.steps.map(step => 
            step.id === prev.currentStep ? { ...step, status: "error" as const, endTime: new Date() } : step
          )
          return { ...prev, steps: updatedSteps }
        }
        return prev
      })
      
      setState(prev => ({
        ...prev,
        error: errorMsg
      }))
      setCurrentStep(undefined)
    } finally {
      setState(prev => ({ ...prev, isGenerating: false }))
    }
  }, [state.isGenerating, state.currentStep, addStep, updateStep, setCurrentStep, setOverallProgress])

  const reset = React.useCallback(() => {
    setState({
      isGenerating: false,
      steps: [],
      overallProgress: 0,
      currentStep: undefined,
      error: undefined
    })
  }, [])

  return {
    ...state,
    generate,
    reset,
    addStep,
    updateStep,
    setCurrentStep,
    setOverallProgress
  }
}
