"use client"

import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { LoadingSpinner, LoadingDots } from "@/components/ui/loading-spinner"
import { LiveConsole, ConsoleEntry } from "@/components/live-console"
import { ProgressTracker, ProgressStep } from "@/components/progress-tracker"
import { useToast } from "@/hooks/use-toast"
import { 
  Play, 
  Square, 
  RotateCcw, 
  Wand2, 
  FileText, 
  Users, 
  Mail, 
  Sparkles, 
  Target, 
  TrendingUp, 
  Zap, 
  Clock,
  CheckCircle,
  AlertCircle,
  Settings,
  BarChart3,
  Brain,
  Lightbulb,
  ArrowRight,
  RefreshCw,
  Activity
} from "lucide-react"
import { generateContent, getApiStatus } from "@/lib/api"
import { useContentGeneration } from "@/hooks/use-content-generation"
import { useLiveConsole } from "@/hooks/use-live-console"

// Content type configurations
const contentTypes = [
  {
    id: 'blog',
    name: 'Blog Post',
    icon: FileText,
    description: 'Long-form articles and thought leadership',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    estimatedTime: '3-5 min'
  },
  {
    id: 'social',
    name: 'Social Media',
    icon: Users,
    description: 'Engaging posts for social platforms',
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    estimatedTime: '1-2 min'
  },
  {
    id: 'email',
    name: 'Email Campaign',
    icon: Mail,
    description: 'Persuasive email marketing content',
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    estimatedTime: '2-4 min'
  }
]

export default function Dashboard() {
  const { addToast } = useToast()
  const { 
    isGenerating, 
    steps, 
    currentStep, 
    overallProgress, 
    error, 
    generate, 
    reset 
  } = useContentGeneration()
  const {
    entries: consoleEntries,
    isRunning,
    clearEntries,
    resetConsole,
    startConsole,
    stopConsole,
    logInfo,
    logSuccess,
    logWarning,
    logError,
    logDebug
  } = useLiveConsole()
  const [apiStatus, setApiStatus] = React.useState<any>(null)

  // Form state
  const [topic, setTopic] = React.useState("AI-powered design automation")
  const [contentType, setContentType] = React.useState("blog")
  const [activeTab, setActiveTab] = React.useState("create")

  // Get selected content type config
  const selectedContentType = contentTypes.find(ct => ct.id === contentType) || contentTypes[0]

  // Combined reset function
  const handleReset = React.useCallback(() => {
    reset()
    resetConsole()
  }, [reset, resetConsole])

  // API status monitoring
  React.useEffect(() => {
    const checkApiStatus = async () => {
      try {
        const status = await getApiStatus()
        setApiStatus(status)
      } catch (error) {
        // ignore
      }
    }
    const interval = setInterval(checkApiStatus, 5000)
    checkApiStatus()
    return () => clearInterval(interval)
  }, [])

  // Content generation with progress tracking and live console
  const handleGenerateContent = async () => {
    if (isGenerating) return

    setActiveTab("monitor") // Auto-switch to monitor tab
    startConsole()
    addToast({ 
      title: "Generation Started", 
      description: `Creating ${selectedContentType.name} content for "${topic}"`,
      variant: "info",
      duration: 5000
    })

    try {
      await generate(topic, contentType, {
        logInfo,
        logSuccess,
        logWarning,
        logError,
        logDebug
      })
      
      addToast({ 
        title: "Content Generated!", 
        description: "Your content is ready! Check the Preview tab to view it.",
        variant: "success",
        duration: 5000
      })
    } catch (error) {
      logError("Generation process failed", error, "Dashboard")
      addToast({ 
        title: "Generation Failed", 
        description: "An error occurred during content generation",
        variant: "destructive",
        duration: 5000
      })
    } finally {
      stopConsole()
    }
  }

  // Quick actions
  const quickActions = [
    { 
      label: "Trending Topics", 
      icon: TrendingUp, 
      action: () => setTopic("Latest trends in AI and automation"),
      color: "text-green-600"
    },
    { 
      label: "How-to Guide", 
      icon: Lightbulb, 
      action: () => setTopic("Step-by-step guide to AI implementation"),
      color: "text-yellow-600"
    },
    { 
      label: "Case Study", 
      icon: BarChart3, 
      action: () => setTopic("Success story: AI transformation case study"),
      color: "text-blue-600"
    },
    { 
      label: "Product Review", 
      icon: Target, 
      action: () => setTopic("Comprehensive product review and analysis"),
      color: "text-purple-600"
    }
  ]

  const getWorkflowStatus = (stepIndex: number) => {
    if (currentStep > stepIndex) return 'completed'
    if (currentStep === stepIndex && isGenerating) return 'active'
    return 'pending'
  }

  return (
    <main className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl text-white">
              <Wand2 className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-foreground">Content Generator</h1>
              <p className="text-muted-foreground">AI-powered content creation with intelligent workflows</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {apiStatus && (
              <Badge className={`text-xs ${
                apiStatus.status === "healthy" 
                  ? "!bg-green-100 !text-green-800 !border-green-300" 
                  : "!bg-red-100 !text-red-800 !border-red-300"
              }`}>
                API: {apiStatus.status} • {apiStatus.latencyMs}ms
              </Badge>
            )}
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleReset}
              disabled={isGenerating}
              className="gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Reset
            </Button>
          </div>
        </div>

        {/* Workflow Progress Bar */}
        {isGenerating && (
          <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-4 border border-purple-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-purple-700">Generation Progress</span>
              <span className="text-sm text-purple-600">{Math.round(overallProgress)}%</span>
            </div>
            <div className="w-full bg-purple-200 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${overallProgress}%` }}
              />
            </div>
            {currentStep !== null && steps[currentStep] && (
              <p className="text-xs text-purple-600 mt-2">
                {steps[currentStep].name}...
              </p>
            )}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 h-[calc(100vh-250px)]">
        {/* Content Creation Panel */}
        <div className="xl:col-span-1">
          <Card className="h-full flex flex-col">
            <CardHeader className="flex-shrink-0">
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-purple-600" />
                Create Content
              </CardTitle>
              <CardDescription>Configure your AI content generation</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 space-y-6 overflow-auto">
              {/* Topic Input */}
              <div className="space-y-3">
                <Label htmlFor="topic" className="text-sm font-medium">Content Topic</Label>
                <Input
                  id="topic"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="Enter your content topic..."
                  disabled={isGenerating}
                  className="h-12"
                />
              </div>

              {/* Quick Topic Suggestions */}
              <div className="space-y-3">
                <Label className="text-sm font-medium">Quick Ideas</Label>
                <div className="grid grid-cols-2 gap-2">
                  {quickActions.map((action, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      size="sm"
                      onClick={action.action}
                      disabled={isGenerating}
                      className="justify-start gap-2 h-auto py-2 px-3"
                    >
                      <action.icon className={`h-3 w-3 ${action.color}`} />
                      <span className="text-xs">{action.label}</span>
                    </Button>
                  ))}
                </div>
              </div>

              {/* Content Type Selection */}
              <div className="space-y-3">
                <Label className="text-sm font-medium">Content Type</Label>
                <div className="grid gap-3">
                  {contentTypes.map((type) => {
                    const Icon = type.icon
                    const isSelected = contentType === type.id
                    return (
                      <div
                        key={type.id}
                        onClick={() => !isGenerating && setContentType(type.id)}
                        className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                          isSelected 
                            ? `${type.borderColor} ${type.bgColor}` 
                            : 'border-gray-200 hover:border-gray-300'
                        } ${isGenerating ? 'opacity-50 cursor-not-allowed' : ''}`}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`p-2 rounded-lg ${isSelected ? type.bgColor : 'bg-gray-50'}`}>
                            <Icon className={`h-4 w-4 ${isSelected ? type.color : 'text-gray-600'}`} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h4 className="font-medium text-sm">{type.name}</h4>
                            <p className="text-xs text-muted-foreground mt-1">{type.description}</p>
                            <div className="flex items-center gap-2 mt-2">
                              <Clock className="h-3 w-3 text-muted-foreground" />
                              <span className="text-xs text-muted-foreground">{type.estimatedTime}</span>
                            </div>
                          </div>
                          {isSelected && (
                            <CheckCircle className={`h-4 w-4 ${type.color}`} />
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Generate Button */}
              <div className="pt-4">
                <Button
                  onClick={handleGenerateContent}
                  disabled={isGenerating || !topic.trim()}
                  className="w-full h-12 text-base font-medium bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                >
                  {isGenerating ? (
                    <div className="flex items-center gap-2">
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      Generating {selectedContentType.name}...
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <Wand2 className="h-5 w-5" />
                      Generate {selectedContentType.name}
                    </div>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Area */}
        <div className="xl:col-span-2">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
            <TabsList className="grid w-full grid-cols-2 flex-shrink-0">
              <TabsTrigger value="create" className="flex items-center gap-2">
                <Brain className="h-4 w-4" />
                Workflow Overview
              </TabsTrigger>
              <TabsTrigger value="monitor" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Live Monitor
                {isGenerating && (
                  <Badge className="ml-1 !bg-blue-100 !text-blue-800 !border-blue-300 animate-pulse">
                    Active
                  </Badge>
                )}
              </TabsTrigger>
            </TabsList>

            {/* Workflow Overview Tab */}
            <TabsContent value="create" className="flex-1 overflow-hidden">
              <Card className="h-full flex flex-col">
                <CardHeader className="flex-shrink-0">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Brain className="h-5 w-5 text-blue-600" />
                        AI Generation Workflow
                      </CardTitle>
                      <CardDescription>
                        Visual representation of your content creation process
                      </CardDescription>
                    </div>
                    {isGenerating && (
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={() => setActiveTab("monitor")}
                        className="gap-2 animate-pulse border-blue-300 text-blue-700 hover:bg-blue-50"
                      >
                        <Activity className="h-4 w-4" />
                        View Live Monitor
                      </Button>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="flex-1 overflow-hidden">
                  <ScrollArea className="h-full">
                    <div className="space-y-4 pr-4">
                      {steps.map((step, index) => {
                        const status = getWorkflowStatus(index)
                        return (
                          <div
                            key={index}
                            className={`flex items-center gap-4 p-4 rounded-lg border transition-all ${
                              status === 'active' ? 'border-blue-300 bg-blue-50' :
                              status === 'completed' ? 'border-green-300 bg-green-50' :
                              'border-gray-200 bg-gray-50'
                            }`}
                          >
                            <div className="flex-shrink-0">
                              {status === 'active' && (
                                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                                  <RefreshCw className="h-4 w-4 text-white animate-spin" />
                                </div>
                              )}
                              {status === 'completed' && (
                                <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center">
                                  <CheckCircle className="h-4 w-4 text-white" />
                                </div>
                              )}
                              {status === 'pending' && (
                                <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center">
                                  <Clock className="h-4 w-4 text-gray-600" />
                                </div>
                              )}
                            </div>
                            <div className="flex-1">
                              <h4 className="font-medium text-sm">{step.name}</h4>
                              <p className="text-xs text-muted-foreground mt-1">{step.description}</p>
                              {status === 'active' && step.progress !== undefined && (
                                <div className="mt-2">
                                  <div className="w-full bg-blue-200 rounded-full h-1.5">
                                    <div 
                                      className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                                      style={{ width: `${step.progress}%` }}
                                    />
                                  </div>
                                </div>
                              )}
                            </div>
                            {index < steps.length - 1 && (
                              <ArrowRight className="h-4 w-4 text-gray-400" />
                            )}
                          </div>
                        )
                      })}

                      {!isGenerating && steps.length === 0 && (
                        <div className="text-center py-12 text-muted-foreground">
                          <Brain className="h-16 w-16 mx-auto mb-4 opacity-50" />
                          <h3 className="text-lg font-medium mb-2">Ready to Generate</h3>
                          <p className="text-sm">Configure your content and start the AI generation process</p>
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Live Monitor Tab */}
            <TabsContent value="monitor" className="flex-1 overflow-hidden">
              <Card className="h-full flex flex-col">
                <CardHeader className="flex-shrink-0">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <BarChart3 className="h-5 w-5 text-blue-600" />
                      <CardTitle>Live Generation Monitor</CardTitle>
                    </div>
                    <div className="flex items-center gap-2">
                      {isRunning && (
                        <Badge className="!bg-blue-100 !text-blue-800 !border-blue-300 animate-pulse">
                          <div className="w-2 h-2 bg-blue-600 rounded-full mr-1 animate-pulse"></div>
                          Live
                        </Badge>
                      )}
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={clearEntries}
                        disabled={isGenerating}
                        className="gap-1"
                      >
                        <RefreshCw className="h-3 w-3" />
                        Clear
                      </Button>
                    </div>
                  </div>
                  <CardDescription>
                    Real-time progress tracking with live console output
                  </CardDescription>
                </CardHeader>
                
                <CardContent className="flex-1 overflow-hidden p-0">
                  <div className="h-full flex flex-col">
                    {/* Progress Overview Bar */}
                    {(isGenerating || steps.length > 0) && (
                      <div className="flex-shrink-0 p-4 border-b bg-gradient-to-r from-blue-50 to-purple-50">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <Zap className="h-4 w-4 text-blue-600" />
                            <span className="text-sm font-medium text-blue-900">
                              {isGenerating ? 'Generation in Progress' : 'Generation Complete'}
                            </span>
                          </div>
                          <span className="text-sm font-medium text-blue-700">
                            {Math.round(overallProgress)}%
                          </span>
                        </div>
                        <div className="w-full bg-blue-200 rounded-full h-2 mb-3">
                          <div 
                            className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${overallProgress}%` }}
                          />
                        </div>
                        
                        {/* Compact Step Indicators */}
                        <div className="flex items-center gap-2 overflow-x-auto pb-1">
                          {steps.map((step, index) => {
                            const status = getWorkflowStatus(index)
                            return (
                              <div
                                key={index}
                                className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
                                  status === 'active' ? 'bg-blue-600 text-white' :
                                  status === 'completed' ? 'bg-green-600 text-white' :
                                  'bg-gray-200 text-gray-600'
                                }`}
                              >
                                {status === 'active' && <RefreshCw className="h-3 w-3 animate-spin" />}
                                {status === 'completed' && <CheckCircle className="h-3 w-3" />}
                                {status === 'pending' && <Clock className="h-3 w-3" />}
                                <span>{step.name}</span>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )}
                    
                    {/* Integrated Console Area */}
                    <div className="flex-1 overflow-hidden">
                      <div className="h-full flex flex-col">
                        {/* Console Header */}
                        <div className="flex-shrink-0 px-4 py-3 border-b bg-gray-50 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-red-400"></div>
                            <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
                            <div className="w-3 h-3 rounded-full bg-green-400"></div>
                            <span className="text-xs font-mono text-gray-600 ml-2">
                              craefto-console
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge className="text-xs !bg-gray-100 !text-gray-700 !border-gray-300">
                              {consoleEntries.length} entries
                            </Badge>
                            {isGenerating && (
                              <div className="flex items-center gap-1 text-xs text-green-600">
                                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                                Active
                              </div>
                            )}
                          </div>
                        </div>
                        
                        {/* Console Content */}
                        <ScrollArea className="flex-1 bg-gray-900">
                          <div className="p-4 space-y-1 font-mono text-sm">
                            {consoleEntries.length === 0 ? (
                              <div className="text-center py-8 text-gray-500">
                                <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
                                <p className="text-xs">Console ready - waiting for generation to start</p>
                                <p className="text-xs mt-1 opacity-75">Live logs will appear here during content creation</p>
                              </div>
                            ) : (
                              consoleEntries.map((entry, index) => {
                                const getEntryColor = (level: string) => {
                                  switch (level) {
                                    case 'error': return 'text-red-400'
                                    case 'warning': return 'text-yellow-400'
                                    case 'success': return 'text-green-400'
                                    case 'info': return 'text-blue-400'
                                    case 'debug': return 'text-purple-400'
                                    default: return 'text-gray-300'
                                  }
                                }
                                
                                const getEntryIcon = (level: string) => {
                                  switch (level) {
                                    case 'error': return '✗'
                                    case 'warning': return '⚠'
                                    case 'success': return '✓'
                                    case 'info': return 'ℹ'
                                    case 'debug': return '◦'
                                    default: return '•'
                                  }
                                }
                                
                                return (
                                  <div 
                                    key={index} 
                                    className={`flex items-start gap-2 py-1 ${getEntryColor(entry.level)} hover:bg-gray-800 rounded px-2 -mx-2 transition-colors`}
                                  >
                                    <span className="text-xs opacity-60 min-w-[60px] text-right">
                                      {entry.timestamp.toLocaleTimeString('en-US', { 
                                        hour12: false, 
                                        hour: '2-digit', 
                                        minute: '2-digit', 
                                        second: '2-digit' 
                                      })}
                                    </span>
                                    <span className="text-xs opacity-80">
                                      {getEntryIcon(entry.level)}
                                    </span>
                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs font-medium">{entry.message}</span>
                                        {entry.source && (
                                          <span className="text-xs opacity-60 bg-gray-800 px-1 rounded">
                                            {entry.source}
                                          </span>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                )
                              })
                            )}
                          </div>
                        </ScrollArea>
                        
                        {/* Console Footer */}
                        <div className="flex-shrink-0 px-4 py-2 border-t bg-gray-50 flex items-center justify-between text-xs text-gray-600">
                          <div className="flex items-center gap-4">
                            <span>Ready</span>
                            {currentStep !== null && steps[currentStep] && (
                              <span className="flex items-center gap-1">
                                <RefreshCw className="h-3 w-3 animate-spin" />
                                {steps[currentStep].name}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            <span>Entries: {consoleEntries.length}</span>
                            {isGenerating && (
                              <span className="flex items-center gap-1 text-blue-600">
                                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                                Generating
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>

    </main>
  )
}
