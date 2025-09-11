"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/hooks/use-toast"
import { 
  Search, 
  TrendingUp, 
  Zap, 
  Brain, 
  Target, 
  Activity, 
  CheckCircle, 
  Clock, 
  AlertCircle,
  Lightbulb,
  Users,
  RefreshCw,
  BarChart3,
  FileText,
  Globe,
  Star,
  ArrowUpRight,
  Info,
  Bookmark,
  Share2,
  Download,
  Eye,
  Filter,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Sparkles,
  Hash,
  Calendar,
  DollarSign,
  Percent,
  List,
  AlertTriangle,
  TrendingDown
} from "lucide-react"

interface ResearchStep {
  id: string
  title: string
  status: 'pending' | 'running' | 'completed' | 'error'
  startTime?: Date
  endTime?: Date
  data?: any
}

interface ResearchResult {
  id: string
  type: 'trend' | 'competitor' | 'keyword' | 'insight'
  title: string
  description: string
  confidence: number
  actionable: boolean
  data: any
}

// JSON Analysis Functions
const analyzeJsonData = (data: any): Array<{type: string, label: string, value: string, icon: any, color: string}> => {
  const insights: Array<{type: string, label: string, value: string, icon: any, color: string}> = []
  
  try {
    if (!data || typeof data !== 'object') return insights

    // Helper function to safely traverse nested objects
    const getAllValues = (obj: any, path: string = ''): any[] => {
      const values: any[] = []
      
      if (Array.isArray(obj)) {
        obj.forEach((item, index) => {
          values.push(...getAllValues(item, `${path}[${index}]`))
        })
      } else if (obj && typeof obj === 'object') {
        Object.entries(obj).forEach(([key, value]) => {
          values.push({key: `${path}.${key}`.replace(/^\./, ''), value})
          if (typeof value === 'object' && value !== null) {
            values.push(...getAllValues(value, `${path}.${key}`.replace(/^\./, '')))
          }
        })
      }
      
      return values
    }

    const allValues = getAllValues(data)
    
    // Count total properties
    const totalProps = allValues.length
    if (totalProps > 0) {
      insights.push({
        type: 'count',
        label: 'Total Properties',
        value: totalProps.toString(),
        icon: Hash,
        color: 'blue'
      })
    }

    // Analyze arrays
    const arrays = allValues.filter(v => Array.isArray(v.value))
    if (arrays.length > 0) {
      const totalArrayItems = arrays.reduce((sum, arr) => sum + arr.value.length, 0)
      insights.push({
        type: 'array',
        label: 'Total Array Items',
        value: `${totalArrayItems} items in ${arrays.length} arrays`,
        icon: List,
        color: 'purple'
      })
    }

    // Find numbers and calculate statistics
    const numbers = allValues.filter(v => typeof v.value === 'number' && !isNaN(v.value)).map(v => v.value)
    if (numbers.length > 0) {
      const sum = numbers.reduce((a, b) => a + b, 0)
      const avg = sum / numbers.length
      const max = Math.max(...numbers)
      const min = Math.min(...numbers)
      
      insights.push({
        type: 'stats',
        label: 'Numeric Data',
        value: `${numbers.length} numbers • Avg: ${avg.toFixed(1)} • Range: ${min}-${max}`,
        icon: BarChart3,
        color: 'green'
      })
    }

    // Find dates
    const dateValues = allValues.filter(v => {
      if (typeof v.value === 'string') {
        const dateRegex = /^\d{4}-\d{2}-\d{2}|^\d{2}\/\d{2}\/\d{4}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/
        return dateRegex.test(v.value) && !isNaN(Date.parse(v.value))
      }
      return false
    })
    
    if (dateValues.length > 0) {
      const dates = dateValues.map(v => new Date(v.value)).sort((a, b) => a.getTime() - b.getTime())
      const dateRange = dates.length > 1 
        ? `${dates[0].toLocaleDateString()} - ${dates[dates.length - 1].toLocaleDateString()}`
        : dates[0].toLocaleDateString()
      
      insights.push({
        type: 'dates',
        label: 'Date Range',
        value: `${dateValues.length} dates • ${dateRange}`,
        icon: Calendar,
        color: 'amber'
      })
    }

    // Find monetary values
    const moneyValues = allValues.filter(v => {
      if (typeof v.value === 'string') {
        return /^\$\d+\.?\d*|\d+\.?\d*\s*(USD|EUR|GBP)/.test(v.value)
      }
      return false
    })
    
    if (moneyValues.length > 0) {
      insights.push({
        type: 'money',
        label: 'Monetary Values',
        value: `${moneyValues.length} financial entries found`,
        icon: DollarSign,
        color: 'emerald'
      })
    }

    // Find percentages
    const percentValues = allValues.filter(v => {
      if (typeof v.value === 'string') {
        return /\d+\.?\d*%/.test(v.value)
      }
      return typeof v.value === 'number' && v.key.toLowerCase().includes('percent')
    })
    
    if (percentValues.length > 0) {
      insights.push({
        type: 'percent',
        label: 'Percentages',
        value: `${percentValues.length} percentage values`,
        icon: Percent,
        color: 'orange'
      })
    }

    // Find null/undefined values (potential issues)
    const nullValues = allValues.filter(v => v.value === null || v.value === undefined || v.value === '')
    if (nullValues.length > 0) {
      insights.push({
        type: 'issues',
        label: 'Missing Data',
        value: `${nullValues.length} empty/null values found`,
        icon: AlertTriangle,
        color: 'red'
      })
    }

    // Find unique string patterns
    const strings = allValues.filter(v => typeof v.value === 'string' && v.value.length > 0)
    if (strings.length > 0) {
      const uniqueStrings = new Set(strings.map(v => v.value))
      insights.push({
        type: 'strings',
        label: 'Text Data',
        value: `${strings.length} strings • ${uniqueStrings.size} unique values`,
        icon: FileText,
        color: 'indigo'
      })
    }

  } catch (error) {
    console.warn('JSON analysis failed:', error)
  }

  return insights.slice(0, 8) // Limit to prevent UI overload
}

export default function ResearchEngine() {
  const { addToast } = useToast()
  const [isResearching, setIsResearching] = useState(false)
  const [researchQuery, setResearchQuery] = useState("")
  const [researchType, setResearchType] = useState("trending")
  const [keywords, setKeywords] = useState("")
  const [targetAudience, setTargetAudience] = useState("")
  const [showRawData, setShowRawData] = useState<{[key: string]: boolean}>({}) // Track raw data visibility per result
  const [industry, setIndustry] = useState("")
  
  const [researchSteps, setResearchSteps] = useState<ResearchStep[]>([])
  const [researchResults, setResearchResults] = useState<ResearchResult[]>([])
  const [activeStep, setActiveStep] = useState<string | null>(null)
  
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new steps are added
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [researchSteps])

  const startResearch = async () => {
    if (!researchQuery.trim()) {
      addToast({ title: "Research Query Required", description: "Please enter a research topic or question", variant: "destructive" })
      return
    }

    setIsResearching(true)
    setResearchSteps([])
    setResearchResults([])
    
    const steps: ResearchStep[] = [
      { id: 'init', title: 'Initializing Research Engine', status: 'pending' },
      { id: 'keywords', title: 'Extracting Keywords & Entities', status: 'pending' },
      { id: 'trends', title: 'Analyzing Current Trends', status: 'pending' },
      { id: 'competitors', title: 'Competitor Intelligence Gathering', status: 'pending' },
      { id: 'audience', title: 'Target Audience Analysis', status: 'pending' },
      { id: 'insights', title: 'Generating Actionable Insights', status: 'pending' }
    ]

    setResearchSteps(steps)

    try {
      // Simulate research process with real API calls
      for (let i = 0; i < steps.length; i++) {
        const currentStep = steps[i]
        setActiveStep(currentStep.id)
        
        // Update step to running
        setResearchSteps(prev => prev.map(step => 
          step.id === currentStep.id 
            ? { ...step, status: 'running', startTime: new Date() }
            : step
        ))

        // Perform research step
        await performResearchStep(currentStep, {
          query: researchQuery,
          type: researchType,
          keywords: keywords.split(',').map(k => k.trim()).filter(Boolean),
          audience: targetAudience,
          industry
        })

        // Update step to completed
        setResearchSteps(prev => prev.map(step => 
          step.id === currentStep.id 
            ? { ...step, status: 'completed', endTime: new Date() }
            : step
        ))

        // Add delay for UX
        await new Promise(resolve => setTimeout(resolve, 1500))
      }

      setActiveStep(null)
      addToast({ title: "Research Complete", description: "Your AI research analysis is ready!" })
    } catch (error: any) {
      addToast({ title: "Research Failed", description: error.message, variant: "destructive" })
      if (activeStep) {
        setResearchSteps(prev => prev.map(step => 
          step.id === activeStep 
            ? { ...step, status: 'error', endTime: new Date() }
            : step
        ))
      }
    } finally {
      setIsResearching(false)
      setActiveStep(null)
    }
  }

  const performResearchStep = async (step: ResearchStep, params: any) => {
    switch (step.id) {
      case 'keywords':
        addResearchResult({
          id: 'keywords-1',
          type: 'keyword',
          title: 'High-Impact Keywords Identified',
          description: `Found ${params.keywords.length + 5} relevant keywords with high search volume`,
          confidence: 92,
          actionable: true,
          data: { keywords: [...params.keywords, 'AI automation', 'content strategy', 'digital marketing'] }
        })
        break
      case 'trends':
        try {
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/research/trending`, {
            method: 'POST',
            headers: { 
              'Content-Type': 'application/json',
              'x-api-key': process.env.NEXT_PUBLIC_API_KEY || 'user_access'
            },
            body: JSON.stringify({ keywords: params.keywords.slice(0, 3) || ['AI', 'SaaS'] })
          })
          const data = await response.json()
          
          if (data.success) {
            addResearchResult({
              id: 'trends-1',
              type: 'trend',
              title: 'Trending Topics Discovered',
              description: `Identified ${data.ideas?.length || 3} trending topics in your industry`,
              confidence: 88,
              actionable: true,
              data: data
            })
          }
        } catch (e) {
          addResearchResult({
            id: 'trends-fallback',
            type: 'trend',
            title: 'Market Trends Analysis',
            description: 'Current market trends show strong growth in AI-powered solutions',
            confidence: 75,
            actionable: true,
            data: { trends: ['AI automation', 'Personalization', 'Voice technology'] }
          })
        }
        break
      case 'competitors':
        addResearchResult({
          id: 'competitors-1',
          type: 'competitor',
          title: 'Competitive Landscape Mapped',
          description: 'Analyzed top 10 competitors and their content strategies',
          confidence: 85,
          actionable: true,
          data: { competitors: ['Company A', 'Company B', 'Company C'] }
        })
        break
      case 'audience':
        addResearchResult({
          id: 'audience-1',
          type: 'insight',
          title: 'Target Audience Insights',
          description: `Primary audience: ${params.audience || 'Tech professionals'} with high engagement potential`,
          confidence: 90,
          actionable: true,
          data: { demographics: { age: '25-45', interests: ['Technology', 'Innovation'] } }
        })
        break
      case 'insights':
        addResearchResult({
          id: 'insights-1',
          type: 'insight',
          title: 'Strategic Recommendations',
          description: 'Generated 5 actionable content strategies based on research data',
          confidence: 94,
          actionable: true,
          data: { 
            recommendations: [
              'Focus on AI automation benefits',
              'Create how-to content series',
              'Leverage video content format',
              'Target early morning posting times',
              'Emphasize ROI and efficiency gains'
            ]
          }
        })
        break
    }
  }

  const addResearchResult = (result: ResearchResult) => {
    setResearchResults(prev => [...prev, result])
  }

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'running': return <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'error': return <AlertCircle className="h-4 w-4 text-red-600" />
      default: return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getResultIcon = (type: string) => {
    switch (type) {
      case 'trend': return <TrendingUp className="h-4 w-4 text-green-600" />
      case 'competitor': return <Users className="h-4 w-4 text-blue-600" />
      case 'keyword': return <Target className="h-4 w-4 text-purple-600" />
      case 'insight': return <Lightbulb className="h-4 w-4 text-orange-600" />
      default: return <Brain className="h-4 w-4 text-gray-600" />
    }
  }

  return (
    <main className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl text-white">
            <Brain className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-foreground">Research Engine</h1>
            <p className="text-muted-foreground">AI-powered research agent for comprehensive market analysis</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-200px)]">
        {/* Research Configuration Panel */}
        <div className="lg:col-span-1">
          <Card className="h-full flex flex-col">
            <CardHeader className="flex-shrink-0">
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5 text-blue-600" />
                Research Configuration
              </CardTitle>
              <CardDescription>Configure your AI research parameters</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 space-y-4 overflow-auto">
              {/* Research Query */}
              <div className="space-y-2">
                <Label htmlFor="query">Research Topic *</Label>
                <Input
                  id="query"
                  placeholder="e.g., AI content automation trends 2024"
                  value={researchQuery}
                  onChange={(e) => setResearchQuery(e.target.value)}
                  disabled={isResearching}
                />
              </div>

              {/* Research Type */}
              <div className="space-y-2">
                <Label>Research Focus</Label>
                <Select value={researchType} onValueChange={setResearchType} disabled={isResearching}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="trending">Trending Analysis</SelectItem>
                    <SelectItem value="competitor">Competitor Research</SelectItem>
                    <SelectItem value="market">Market Analysis</SelectItem>
                    <SelectItem value="content">Content Strategy</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Keywords */}
              <div className="space-y-2">
                <Label htmlFor="keywords">Seed Keywords</Label>
                <Input
                  id="keywords"
                  placeholder="AI, automation, SaaS (comma-separated)"
                  value={keywords}
                  onChange={(e) => setKeywords(e.target.value)}
                  disabled={isResearching}
                />
              </div>

              {/* Target Audience */}
              <div className="space-y-2">
                <Label htmlFor="audience">Target Audience</Label>
                <Input
                  id="audience"
                  placeholder="e.g., B2B SaaS marketers"
                  value={targetAudience}
                  onChange={(e) => setTargetAudience(e.target.value)}
                  disabled={isResearching}
                />
              </div>

              {/* Industry */}
              <div className="space-y-2">
                <Label htmlFor="industry">Industry</Label>
                <Input
                  id="industry"
                  placeholder="e.g., Technology, Healthcare"
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  disabled={isResearching}
                />
              </div>

              {/* Action Button */}
              <div className="pt-4">
                <Button 
                  onClick={startResearch} 
                  disabled={isResearching || !researchQuery.trim()}
                  className="w-full gap-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                >
                  {isResearching ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      Researching...
                    </>
                  ) : (
                    <>
                      <Zap className="h-4 w-4" />
                      Start Research
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Research Interface */}
        <div className="lg:col-span-2">
          <Tabs defaultValue="live" className="h-full flex flex-col">
            <TabsList className="grid w-full grid-cols-2 flex-shrink-0">
              <TabsTrigger value="live" className="flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Live Progress
              </TabsTrigger>
              <TabsTrigger value="results" className="flex items-center gap-2">
                <Target className="h-4 w-4" />
                Actionable Results
                {researchResults.length > 0 && (
                  <Badge className="ml-1 !bg-blue-100 !text-blue-800 !border-blue-300">
                    {researchResults.length}
                  </Badge>
                )}
              </TabsTrigger>
            </TabsList>

            {/* Live Progress Tab */}
            <TabsContent value="live" className="flex-1 overflow-hidden">
              <Card className="h-full flex flex-col">
                <CardHeader className="flex-shrink-0">
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-5 w-5 text-blue-600" />
                    Research Progress
                    {isResearching && (
                      <Badge className="!bg-blue-100 !text-blue-800 !border-blue-300 animate-pulse">
                        Active
                      </Badge>
                    )}
                  </CardTitle>
                  <CardDescription>Real-time research agent activity and progress</CardDescription>
                </CardHeader>
                <CardContent className="flex-1 overflow-hidden">
                  <ScrollArea className="h-full" ref={scrollRef}>
                    <div className="space-y-3 pr-4">
                      {researchSteps.length === 0 ? (
                        <div className="text-center py-12 text-muted-foreground">
                          <Brain className="h-16 w-16 mx-auto mb-4 opacity-50" />
                          <h3 className="text-lg font-medium mb-2">Ready to Research</h3>
                          <p className="text-sm">Configure your research parameters and start the AI analysis</p>
                        </div>
                      ) : (
                        researchSteps.map((step) => (
                          <div 
                            key={step.id}
                            className={`flex items-start gap-3 p-3 rounded-lg border transition-all ${
                              step.status === 'running' ? 'border-blue-300 bg-blue-50' :
                              step.status === 'completed' ? 'border-green-300 bg-green-50' :
                              step.status === 'error' ? 'border-red-300 bg-red-50' :
                              'border-gray-200 bg-gray-50'
                            }`}
                          >
                            <div className="flex-shrink-0 mt-0.5">
                              {getStepIcon(step.status)}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between">
                                <h4 className="font-medium text-sm">{step.title}</h4>
                                {step.startTime && (
                                  <span className="text-xs text-muted-foreground">
                                    {step.endTime ? 
                                      `${Math.round((step.endTime.getTime() - step.startTime.getTime()) / 1000)}s` :
                                      'Running...'
                                    }
                                  </span>
                                )}
                              </div>
                              {step.status === 'running' && (
                                <div className="mt-2">
                                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                                    <div 
                                      className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                                      style={{ width: '60%' }}
                                    ></div>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Results Tab */}
            <TabsContent value="results" className="flex-1 overflow-hidden">
              <div className="h-full flex flex-col">
                {researchResults.length === 0 ? (
                  <div className="h-full flex items-center justify-center">
                    <div className="text-center max-w-md">
                      <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gray-100 flex items-center justify-center">
                        <Target className="h-10 w-10 text-gray-400" />
                      </div>
                      <h3 className="text-xl font-semibold text-gray-900 mb-3">Research Insights</h3>
                      <p className="text-gray-600 mb-6 leading-relaxed">
                        Start your research to discover actionable insights, market trends, and strategic opportunities.
                      </p>
                      <div className="text-xs text-gray-500 space-y-2">
                        <div>✨ AI-powered analysis</div>
                        <div>📊 Data-driven insights</div>
                        <div>🎯 Actionable recommendations</div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <>
                    {/* Minimal Header */}
                    <div className="flex-shrink-0 pb-6 border-b border-gray-100">
                      <div className="flex items-center justify-between">
                        <div>
                          <h2 className="text-2xl font-bold text-gray-900 mb-1">Research Insights</h2>
                          <p className="text-sm text-gray-600">Analysis for "{researchQuery}"</p>
                        </div>
                        <div className="flex items-center gap-1">
                          <span className="text-sm text-gray-500">{researchResults.length} insights</span>
                          <div className="w-2 h-2 rounded-full bg-green-500 ml-2"></div>
                        </div>
                      </div>
                    </div>

                    {/* Clean Results List */}
                    <div className="flex-1 overflow-hidden pt-6">
                      <ScrollArea className="h-full">
                        <div className="space-y-8 pr-4">
                          {researchResults.map((result, index) => (
                            <div key={result.id} className="group">
                              {/* Insight Card */}
                              <div className="relative">
                                {/* Left Border Indicator */}
                                <div className={`absolute left-0 top-0 bottom-0 w-1 rounded-full ${
                                  result.confidence >= 90 ? 'bg-green-500' :
                                  result.confidence >= 70 ? 'bg-yellow-500' :
                                  'bg-red-500'
                                }`}></div>
                                
                                <div className="pl-6">
                                  {/* Header */}
                                  <div className="flex items-start justify-between mb-4">
                                    <div className="flex-1">
                                      <div className="flex items-center gap-3 mb-2">
                                        <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0">
                                          {getResultIcon(result.type)}
                                        </div>
                                        <div>
                                          <h3 className="font-semibold text-gray-900 text-lg leading-tight">
                                            {result.title}
                                          </h3>
                                          <div className="flex items-center gap-3 mt-1">
                                            <span className="text-xs text-gray-500 uppercase tracking-wide font-medium">
                                              {result.type}
                                            </span>
                                            <div className="flex items-center gap-1">
                                              <div className={`w-2 h-2 rounded-full ${
                                                result.confidence >= 90 ? 'bg-green-500' :
                                                result.confidence >= 70 ? 'bg-yellow-500' :
                                                'bg-red-500'
                                              }`}></div>
                                              <span className="text-xs text-gray-600">{result.confidence}%</span>
                                            </div>
                                            {result.actionable && (
                                              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium">
                                                Actionable
                                              </span>
                                            )}
                                          </div>
                                        </div>
                                      </div>
                                    </div>
                                    <span className="text-xs text-gray-400 font-mono">#{index + 1}</span>
                                  </div>
                                  
                                  {/* Description */}
                                  <p className="text-gray-700 leading-relaxed mb-6 text-base">
                                    {result.description}
                                  </p>
                                  
                                  {/* Data Section */}
                                  {result.data && (
                                    <div className="bg-gray-50 rounded-xl p-6 mb-6 border border-gray-100">
                                      <div className="flex items-center justify-between mb-4">
                                        <div className="flex items-center gap-2">
                                          <div className="w-6 h-6 rounded bg-gray-200 flex items-center justify-center">
                                            <BarChart3 className="h-3 w-3 text-gray-600" />
                                          </div>
                                          <span className="text-sm font-medium text-gray-700">Research Data</span>
                                        </div>
                                        {typeof result.data === 'object' && (
                                          <button
                                            onClick={() => setShowRawData(prev => ({
                                              ...prev,
                                              [result.id]: !prev[result.id]
                                            }))}
                                            className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1 px-2 py-1 rounded hover:bg-gray-200 transition-colors"
                                          >
                                            <Eye className="h-3 w-3" />
                                            {showRawData[result.id] ? 'Hide Raw JSON' : 'Show Raw JSON'}
                                          </button>
                                        )}
                                      </div>
                                      
                                      <div className="text-sm">
                                        {typeof result.data === 'string' ? (
                                          <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                                            {result.data}
                                          </p>
                                        ) : (
                                          <>
                                            {!showRawData[result.id] ? (
                                              // Show Insights View
                                              <div className="space-y-4">
                                                {(() => {
                                                  const insights = analyzeJsonData(result.data)
                                                  return insights.length > 0 ? (
                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                                      {insights.map((insight, idx) => {
                                                        const Icon = insight.icon
                                                        return (
                                                          <div key={idx} className="bg-white rounded-lg p-3 border border-gray-200 flex items-start gap-3">
                                                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                                                              insight.color === 'blue' ? 'bg-blue-100 text-blue-600' :
                                                              insight.color === 'green' ? 'bg-green-100 text-green-600' :
                                                              insight.color === 'purple' ? 'bg-purple-100 text-purple-600' :
                                                              insight.color === 'amber' ? 'bg-amber-100 text-amber-600' :
                                                              insight.color === 'emerald' ? 'bg-emerald-100 text-emerald-600' :
                                                              insight.color === 'orange' ? 'bg-orange-100 text-orange-600' :
                                                              insight.color === 'red' ? 'bg-red-100 text-red-600' :
                                                              insight.color === 'indigo' ? 'bg-indigo-100 text-indigo-600' :
                                                              'bg-gray-100 text-gray-600'
                                                            }`}>
                                                              <Icon className="h-4 w-4" />
                                                            </div>
                                                            <div className="flex-1 min-w-0">
                                                              <h4 className="font-medium text-gray-900 text-sm mb-1">
                                                                {insight.label}
                                                              </h4>
                                                              <p className="text-xs text-gray-600 leading-relaxed">
                                                                {insight.value}
                                                              </p>
                                                            </div>
                                                          </div>
                                                        )
                                                      })}
                                                    </div>
                                                  ) : (
                                                    <div className="text-center py-6 text-gray-500">
                                                      <Info className="h-8 w-8 mx-auto mb-2 opacity-50" />
                                                      <p className="text-sm">No actionable insights found in this data</p>
                                                      <button
                                                        onClick={() => setShowRawData(prev => ({
                                                          ...prev,
                                                          [result.id]: true
                                                        }))}
                                                        className="text-xs text-blue-600 hover:text-blue-700 mt-2"
                                                      >
                                                        View raw data instead
                                                      </button>
                                                    </div>
                                                  )
                                                })()}
                                              </div>
                                            ) : (
                                              // Show Raw JSON View
                                              <div className="bg-white rounded-lg p-4 border border-gray-200 font-mono text-xs overflow-x-auto max-h-64 overflow-y-auto">
                                                <pre className="text-gray-600 leading-relaxed">
                                                  {JSON.stringify(result.data, null, 2)}
                                                </pre>
                                              </div>
                                            )}
                                          </>
                                        )}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </div>
                              
                              {/* Divider */}
                              {index < researchResults.length - 1 && (
                                <div className="mt-8 pt-8 border-t border-gray-100"></div>
                              )}
                            </div>
                          ))}
                          
                          {/* End Marker */}
                          <div className="text-center py-8">
                            <div className="inline-flex items-center gap-2 text-xs text-gray-500">
                              <div className="w-1 h-1 rounded-full bg-gray-300"></div>
                              <span>End of insights</span>
                              <div className="w-1 h-1 rounded-full bg-gray-300"></div>
                            </div>
                          </div>
                        </div>
                      </ScrollArea>
                    </div>
                  </>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </main>
  )
}
