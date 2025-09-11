"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useToast } from "@/hooks/use-toast"
import { getGeneratedContent, getContentDetails, GeneratedContentItem, ContentDetails } from "@/lib/api"
import { Calendar, FileText, Image, Users, Eye, RefreshCw, Filter, Code, Search, Sparkles, BarChart3, Clock, CheckCircle, Mail } from "lucide-react"

// Shared color utility functions
const getContentTypeColor = (type: string) => {
  switch (type) {
    case 'blog': return '!bg-blue-100 !text-blue-800 !border-blue-300'
    case 'social': return '!bg-purple-100 !text-purple-800 !border-purple-300'
    case 'email': return '!bg-indigo-100 !text-indigo-800 !border-indigo-300'
    default: return '!bg-gray-100 !text-gray-800 !border-gray-300'
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'published': return '!bg-green-100 !text-green-800 !border-green-300'
    case 'draft': return '!bg-orange-100 !text-orange-800 !border-orange-300'
    case 'scheduled': return '!bg-yellow-100 !text-yellow-800 !border-yellow-300'
    default: return '!bg-gray-100 !text-gray-800 !border-gray-300'
  }
}

export default function ContentPreview() {
  const { addToast } = useToast()
  const [contentList, setContentList] = useState<GeneratedContentItem[]>([])
  const [selectedContent, setSelectedContent] = useState<ContentDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [contentTypeFilter, setContentTypeFilter] = useState<string>('all')
  const [pagination, setPagination] = useState({ page: 1, limit: 20, total: 0 })

  const loadContent = async () => {
    try {
      setLoading(true)
      const response = await getGeneratedContent(
        pagination.limit,
        (pagination.page - 1) * pagination.limit,
        contentTypeFilter === 'all' ? undefined : contentTypeFilter
      )
      
      if (response.content) {
        setContentList(response.content)
        setPagination(prev => ({ ...prev, total: response.pagination?.total || 0 }))
      }
    } catch (error) {
      console.error('Failed to load content:', error)
      addToast({
        title: "Error loading content",
        description: "Failed to fetch generated content. Please try again.",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const handleContentSelect = async (id: string) => {
    try {
      setLoadingDetails(true)
      const response = await getContentDetails(id)
      console.log('🔍 Content details response:', response)
      
      // Handle both direct content and wrapped response
      const details = response.content || response
      setSelectedContent(details as ContentDetails)
    } catch (error) {
      console.error('Failed to load content details:', error)
      addToast({
        title: "Error loading details",
        description: "Failed to fetch content details. Please try again.",
        variant: "destructive"
      })
    } finally {
      setLoadingDetails(false)
    }
  }

  const handleFilterChange = (value: string) => {
    setContentTypeFilter(value)
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  useEffect(() => {
    loadContent()
  }, [contentTypeFilter])

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <main className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl text-white">
              <Eye className="h-6 w-6" />
            </div>
        <div>
              <h1 className="text-3xl font-bold text-foreground">Content Preview</h1>
              <p className="text-muted-foreground">Review and manage your AI-generated content library</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <BarChart3 className="h-4 w-4" />
              <span>{pagination.total} items total</span>
        </div>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={loadContent} 
              disabled={loading}
              className="gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

        {/* Quick Stats Bar */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <FileText className="h-4 w-4 text-green-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">Total Content</p>
                <p className="text-2xl font-bold text-green-600">{pagination.total}</p>
              </div>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Users className="h-4 w-4 text-purple-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">Social Posts</p>
                <p className="text-2xl font-bold text-purple-600">{contentList.filter(c => c.content_type === 'social').length}</p>
              </div>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-100 rounded-lg">
                <Mail className="h-4 w-4 text-indigo-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">Email Campaigns</p>
                <p className="text-2xl font-bold text-indigo-600">{contentList.filter(c => c.content_type === 'email').length}</p>
              </div>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <FileText className="h-4 w-4 text-blue-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">Blog Posts</p>
                <p className="text-2xl font-bold text-blue-600">{contentList.filter(c => c.content_type === 'blog').length}</p>
              </div>
            </div>
          </Card>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 h-[calc(100vh-400px)]">
        {/* Enhanced Content Library */}
        <div className="xl:col-span-1">
          <Card className="h-full flex flex-col">
            <CardHeader className="flex-shrink-0">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Search className="h-5 w-5 text-emerald-600" />
                  <CardTitle>Content Library</CardTitle>
                </div>
                <Badge className="!bg-emerald-100 !text-emerald-800 !border-emerald-300">
                  {contentList.length} of {pagination.total}
                </Badge>
              </div>
              <CardDescription>Browse and select content to preview</CardDescription>
              
              {/* Enhanced Filter Section */}
              <div className="flex items-center gap-3 pt-4">
                <div className="flex items-center gap-2 flex-1">
                  <Filter className="h-4 w-4 text-gray-500" />
                <Select value={contentTypeFilter} onValueChange={handleFilterChange}>
                    <SelectTrigger className="h-9 focus:ring-0 focus:ring-offset-0">
                    <SelectValue placeholder="All content types" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                      <SelectItem value="blog">📝 Blog Posts</SelectItem>
                      <SelectItem value="social">📱 Social Media</SelectItem>
                      <SelectItem value="email">✉️ Email Campaigns</SelectItem>
                  </SelectContent>
                </Select>
                </div>
              </div>
            </CardHeader>

            <CardContent className="flex-1 space-y-3 overflow-auto">
              <div className="grid gap-3">
                  {loading ? (
                    Array.from({ length: 6 }).map((_, i) => (
                      <Card key={i} className="p-4">
                        <Skeleton className="h-4 w-3/4 mb-3" />
                        <div className="flex justify-between items-center mb-2">
                          <Skeleton className="h-3 w-20" />
                          <Skeleton className="h-3 w-16" />
                        </div>
                        <Skeleton className="h-3 w-full" />
                      </Card>
                    ))
                  ) : contentList.length === 0 ? (
                    <div className="text-center py-12 text-muted-foreground">
                      <Search className="h-16 w-16 mx-auto mb-4 opacity-50" />
                      <h3 className="text-lg font-medium mb-2">No Content Found</h3>
                      <p className="text-sm">Try adjusting your filter or generate some content first</p>
                    </div>
                  ) : (
                    contentList.map((item) => (
                      <div
                        key={item.id} 
                        onClick={() => handleContentSelect(item.id)}
                        className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                          selectedContent?.id === item.id 
                            ? 'border-emerald-400 bg-emerald-50' 
                            : 'border-gray-200 hover:border-emerald-300'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          {/* Content Type Icon */}
                          <div className={`p-2 rounded-lg ${
                            selectedContent?.id === item.id 
                              ? 'bg-emerald-100' 
                              : 'bg-gray-50'
                          }`}>
                            {item.content_type === 'blog' && (
                              <FileText className={`h-4 w-4 ${
                                selectedContent?.id === item.id 
                                  ? 'text-emerald-600' 
                                  : 'text-gray-600'
                              }`} />
                            )}
                            {item.content_type === 'social' && (
                              <Users className={`h-4 w-4 ${
                                selectedContent?.id === item.id 
                                  ? 'text-emerald-600' 
                                  : 'text-gray-600'
                              }`} />
                            )}
                            {item.content_type === 'email' && (
                              <Mail className={`h-4 w-4 ${
                                selectedContent?.id === item.id 
                                  ? 'text-emerald-600' 
                                  : 'text-gray-600'
                              }`} />
                            )}
                            {!['blog', 'social', 'email'].includes(item.content_type) && (
                              <FileText className={`h-4 w-4 ${
                                selectedContent?.id === item.id 
                                  ? 'text-emerald-600' 
                                  : 'text-gray-600'
                              }`} />
                            )}
                          </div>
                          
                          {/* Content Details */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2 mb-1">
                              <h4 className="font-medium text-sm line-clamp-2 flex-1">
                                {item.title || `Untitled ${item.content_type}`}
                              </h4>
                              <Badge className={`text-xs flex-shrink-0 ${getContentTypeColor(item.content_type)}`}>
                                {item.content_type}
                              </Badge>
                            </div>
                            
                            {/* Preview snippet */}
                            {item.preview && 'snippet' in item.preview && item.preview.snippet && (
                              <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                                {String(item.preview.snippet)}
                              </p>
                            )}
                            
                            {/* Metadata */}
                            <div className="flex items-center gap-2">
                              <Calendar className="h-3 w-3 text-muted-foreground" />
                              <span className="text-xs text-muted-foreground">{formatDate(item.created_at)}</span>
                              {item.preview.word_count && (
                                <>
                                  <span className="text-xs text-muted-foreground">•</span>
                                  <span className="text-xs text-muted-foreground">{item.preview.word_count}w</span>
                                </>
                              )}
                              {item.preview.has_image && (
                                <>
                                  <span className="text-xs text-muted-foreground">•</span>
                                  <Image className="h-3 w-3 text-emerald-500" />
                                </>
                              )}
                            </div>
                          </div>

                          {/* Selection Indicator */}
                          {selectedContent?.id === item.id && (
                            <CheckCircle className="h-4 w-4 text-emerald-600 flex-shrink-0" />
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
            </CardContent>
          </Card>
        </div>

        {/* Enhanced Content Preview Area */}
        <div className="xl:col-span-2">
          {selectedContent ? (
            <ContentPreviewDetails content={selectedContent} loading={loadingDetails} />
          ) : (
            <Card className="h-full flex flex-col">
              {/* Only show when no content selected */}
              <CardHeader className="flex-shrink-0">
                <div className="text-center py-8">
                  <div className="mb-4">
                    <Eye className="h-8 w-8 mx-auto text-gray-400" />
                  </div>
                  <h3 className="text-lg font-medium text-foreground mb-2">Select Content to Preview</h3>
                  <p className="text-sm text-muted-foreground mb-4 max-w-md mx-auto">
                    Choose any item from your content library to view its complete details, formatted content, and raw data. 
                    Get insights into your AI-generated content with our enhanced preview system.
                  </p>
                  
                  {/* Feature Highlights */}
                  <div className="grid grid-cols-3 gap-4 text-center max-w-sm mx-auto">
                    <div className="space-y-1">
                      <div className="w-6 h-6 bg-gray-100 rounded flex items-center justify-center mx-auto">
                        <Sparkles className="h-3 w-3 text-gray-500" />
                      </div>
                      <h4 className="font-medium text-xs">Rich Preview</h4>
                      <p className="text-xs text-muted-foreground">Formatted content display</p>
                    </div>
                    <div className="space-y-1">
                      <div className="w-6 h-6 bg-gray-100 rounded flex items-center justify-center mx-auto">
                        <FileText className="h-3 w-3 text-gray-500" />
                      </div>
                      <h4 className="font-medium text-xs">All Formats</h4>
                      <p className="text-xs text-muted-foreground">Blog, social, email support</p>
                    </div>
                    <div className="space-y-1">
                      <div className="w-6 h-6 bg-gray-100 rounded flex items-center justify-center mx-auto">
                        <BarChart3 className="h-3 w-3 text-gray-500" />
                      </div>
                      <h4 className="font-medium text-xs">Live Data</h4>
                      <p className="text-xs text-muted-foreground">Real-time content analysis</p>
                    </div>
                  </div>
              </div>
              </CardHeader>

              <CardContent className="flex-1 flex items-center justify-center">
                <p className="text-muted-foreground text-center">
                  Click on any content item from the library to start previewing
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </main>
  )
}

function ContentPreviewDetails({ content, loading }: { content: ContentDetails, loading: boolean }) {
  if (loading) {
    return (
      <Card className="h-full flex flex-col">
        <CardHeader className="flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-100 rounded-lg">
              <Sparkles className="h-5 w-5 text-emerald-600 animate-pulse" />
            </div>
            <div className="space-y-2 flex-1">
              <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            </div>
          </div>
        </CardHeader>
        <CardContent className="flex-1 space-y-6">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    )
  }

  // Debug: Log the actual content structure
  console.log('🔍 ContentPreviewDetails received:', content)

  // The API returns the data directly, not nested under 'content'
  const contentData = content.data || {}
  const contentType = content.content_type || 'unknown'
  const title = content.title || `Untitled ${contentType} content`
  const createdAt = content.created_at ? new Date(content.created_at).toLocaleDateString() : 'Unknown date'
  const status = content.status || 'unknown'

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-100 rounded-lg">
              <Sparkles className="h-5 w-5 text-emerald-600" />
            </div>
          <div>
              <CardTitle className="text-xl leading-tight">{title}</CardTitle>
              <CardDescription className="flex items-center gap-3 mt-1">
                <span className="capitalize">{contentType} content</span>
                <span>•</span>
                <span>Created {createdAt}</span>
            </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge className={`${getContentTypeColor(contentType)}`}>
              {contentType}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col overflow-hidden p-0">
        <Tabs defaultValue="preview" className="h-full flex flex-col">
          <div className="px-6 py-4 border-b border-gray-200">
            <TabsList className="grid w-full grid-cols-2 h-11">
              <TabsTrigger value="preview" className="flex items-center gap-2 font-medium">
                <Eye className="h-4 w-4" />
                Content Preview
              </TabsTrigger>
              <TabsTrigger value="raw" className="flex items-center gap-2 font-medium">
                <Code className="h-4 w-4" />
                Raw Data
              </TabsTrigger>
          </TabsList>
          </div>

          <TabsContent value="preview" className="flex-1 overflow-hidden m-0">
            <ScrollArea className="h-full">
              <div className="p-6 space-y-6">
            {!contentData || Object.keys(contentData).length === 0 ? (
                  <div className="text-center py-16 text-muted-foreground">
                    <FileText className="h-20 w-20 mx-auto mb-6 opacity-30" />
                    <h3 className="text-xl font-semibold mb-3">No Content Data Available</h3>
                    <p className="text-sm max-w-md mx-auto">This content may have been generated with an older version of the system or the data is still being processed.</p>
              </div>
                ) : (
                  <>
                    {/* Enhanced Content Display */}
                    {Object.entries(contentData).map(([key, value]) => {
                      if (!value || (typeof value === 'object' && Object.keys(value).length === 0)) return null
                      
                      return (
                        <div key={key} className="bg-gradient-to-r from-gray-50 to-white rounded-lg border p-6 space-y-4">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
                            <h4 className="font-bold text-lg text-gray-900 capitalize">
                              {key.replace(/_/g, ' ')}
                            </h4>
                          </div>
                          <ContentSection data={value} contentType={contentType} />
                        </div>
                      )
                    })}
                  </>
                )}
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="raw" className="flex-1 overflow-hidden m-0">
            <ScrollArea className="h-full">
              <div className="p-6">
                <div className="bg-gray-900 rounded-lg p-6 border">
                  <div className="flex items-center gap-2 mb-4 pb-3 border-b border-gray-700">
                    <Code className="h-4 w-4 text-gray-400" />
                    <span className="text-sm font-medium text-gray-300">Raw JSON Data</span>
                            </div>
                  <pre className="text-xs text-green-400 whitespace-pre-wrap font-mono leading-relaxed overflow-x-auto">
                    {JSON.stringify(content, null, 2)}
                  </pre>
                </div>
              </div>
                </ScrollArea>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}

function ContentSection({ data, contentType }: { data: any; contentType?: string }) {
  if (typeof data === 'string') {
    // Check if the string contains HTML tags and is email content
    const isHTML = /<[a-z][\s\S]*>/i.test(data)
    const isEmail = contentType === 'email'
    
    if (isHTML && isEmail) {
      return (
        <div className="space-y-4">
          {/* HTML Preview */}
          <div className="border rounded-lg overflow-hidden bg-white">
            <div className="bg-gray-50 px-3 py-2 border-b">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <div className="w-2 h-2 rounded-full bg-red-400"></div>
                  <div className="w-2 h-2 rounded-full bg-yellow-400"></div>
                  <div className="w-2 h-2 rounded-full bg-green-400"></div>
                </div>
                <span className="text-xs text-gray-600 font-medium">Email Preview</span>
              </div>
            </div>
            <div className="p-4 max-h-96 overflow-auto">
              <iframe
                srcDoc={`
                  <!DOCTYPE html>
                  <html>
                    <head>
                      <meta charset="UTF-8">
                      <meta name="viewport" content="width=device-width, initial-scale=1.0">
                      <style>
                        body {
                          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                          line-height: 1.6;
                          color: #333;
                          max-width: 600px;
                          margin: 0 auto;
                          padding: 20px;
                        }
                        img { max-width: 100%; height: auto; }
                        a { color: #007bff; text-decoration: none; }
                        a:hover { text-decoration: underline; }
                        table { width: 100%; border-collapse: collapse; }
                        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                      </style>
                    </head>
                    <body>
                      ${data}
                    </body>
                  </html>
                `}
                className="w-full min-h-[300px] border-0"
                title="Email HTML Preview"
                sandbox="allow-same-origin"
              />
            </div>
          </div>
          
          {/* Raw HTML Toggle */}
          <details className="group">
            <summary className="cursor-pointer text-sm font-medium text-gray-600 hover:text-gray-800 flex items-center gap-2">
              <Code className="h-4 w-4" />
              View HTML Source
              <span className="text-xs text-gray-400 group-open:hidden">(click to expand)</span>
            </summary>
            <div className="mt-2 p-3 bg-gray-50 rounded-md border">
              <pre className="text-xs text-gray-700 whitespace-pre-wrap overflow-x-auto">
                <code>{data}</code>
              </pre>
            </div>
          </details>
        </div>
      )
    }
    
    return (
      <div className="prose prose-sm max-w-none">
        <p className="whitespace-pre-wrap">{data}</p>
      </div>
    )
  }

  if (Array.isArray(data)) {
    return (
      <div className="space-y-3">
        {data.map((item, index) => (
          <div key={index} className="p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Badge className="text-xs !bg-blue-100 !text-blue-800 !border-blue-300">
                Item {index + 1}
              </Badge>
            </div>
            <ContentSection data={item} contentType={contentType} />
          </div>
        ))}
      </div>
    )
  }

  if (typeof data === 'object' && data !== null) {
    // Handle image objects specially
    if (data.primary_url || data.image_url || data.url) {
      const imageUrl = data.primary_url || data.image_url || data.url
      return (
        <div className="space-y-3">
          <div className="relative bg-muted rounded-lg overflow-hidden max-w-md">
            <img 
              src={imageUrl} 
              alt={data.alt_text || 'Generated image'}
              className="w-full h-auto object-contain max-h-64"
              onError={(e) => {
                e.currentTarget.style.display = 'none'
              }}
            />
          </div>
          {data.alt_text && (
            <p className="text-sm text-muted-foreground italic">{data.alt_text}</p>
          )}
          {(data.source || data.dimensions) && (
            <div className="text-xs text-muted-foreground">
              {data.source && <span>Source: {data.source}</span>}
              {data.dimensions && <span> • {data.dimensions.width}x{data.dimensions.height}</span>}
            </div>
          )}
        </div>
      )
    }

    // Handle other objects
    return (
      <div className="space-y-2">
        {Object.entries(data).map(([key, value]) => (
          <div key={key} className="pl-4 border-l-2 border-gray-200">
            <div className="font-medium text-sm text-muted-foreground mb-1">
              {key.replace(/_/g, ' ')}:
            </div>
            <ContentSection data={value} contentType={contentType} />
          </div>
        ))}
      </div>
    )
  }

  return (
    <span className="text-sm">{String(data)}</span>
  )
}