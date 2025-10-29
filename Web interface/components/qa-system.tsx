"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Send, Bot, User, Loader2, Sparkles, FileText, Clock, Trash2 } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { apiClient, type RetrievedChunk } from "@/lib/api-client"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  chunks?: RetrievedChunk[]
  processingTime?: number
  followupQuestions?: string[]
  timestamp: Date
}

export function QASystem() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [cacheSize, setCacheSize] = useState<number>(0)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { toast } = useToast()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    loadCacheStats()
  }, [])

  const loadCacheStats = async () => {
    try {
      const stats = await apiClient.getCacheStats()
      setCacheSize(stats.cache_size)
    } catch (error) {
      console.log("Failed to load cache stats")
    }
  }

  const handleClearCache = async () => {
    try {
      await apiClient.clearCache()
      setCacheSize(0)
      toast({
        title: "缓存已清除",
        description: "问答缓存已成功清除",
      })
    } catch (error) {
      toast({
        title: "清除失败",
        description: error instanceof Error ? error.message : "请稍后重试",
        variant: "destructive",
      })
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setLoading(true)

    try {
      const data = await apiClient.askQuestion({
        query: input,
        top_k: 10,
        use_cache: true,
        enable_followup: true,
      })

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.answer,
        chunks: data.retrieved_chunks,
        processingTime: data.processing_time,
        followupQuestions: data.followup_questions,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])

      loadCacheStats()
    } catch (error) {
      toast({
        title: "查询失败",
        description: error instanceof Error ? error.message : "请稍后重试",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleSuggestedQuestion = (question: string) => {
    setInput(question)
  }

  const suggestedQuestions = ["唐三的武魂是什么?", "唐门有哪些绝技?", "史莱克七怪都有谁?", "魂师的等级划分是怎样的?"]

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Chat Card */}
      <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-primary" />
                智能问答
              </CardTitle>
              <CardDescription>基于 RAG 技术,结合知识库为您提供准确的答案</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="gap-1">
                缓存: {cacheSize}
              </Badge>
              {cacheSize > 0 && (
                <Button variant="ghost" size="icon" onClick={handleClearCache}>
                  <Trash2 className="w-4 h-4" />
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Messages */}
          <div className="space-y-4 mb-6 max-h-[500px] overflow-y-auto pr-4">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <Bot className="w-16 h-16 mx-auto mb-4 text-primary opacity-50" />
                <p className="text-lg font-medium mb-2">开始对话</p>
                <p className="text-sm text-muted-foreground mb-6">向我提问关于斗罗大陆的任何问题</p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {suggestedQuestions.map((q, i) => (
                    <Button
                      key={i}
                      variant="outline"
                      size="sm"
                      onClick={() => handleSuggestedQuestion(q)}
                      className="text-xs"
                    >
                      {q}
                    </Button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  {message.role === "assistant" && (
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center flex-shrink-0">
                      <Bot className="w-5 h-5 text-primary-foreground" />
                    </div>
                  )}
                  <div
                    className={`max-w-[80%] rounded-lg p-4 ${
                      message.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>

                    {message.processingTime && (
                      <div className="mt-2 flex items-center gap-1 text-xs text-muted-foreground">
                        <Clock className="w-3 h-3" />
                        <span>处理时间: {message.processingTime.toFixed(2)}秒</span>
                      </div>
                    )}

                    {message.chunks && message.chunks.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-border/50">
                        <p className="text-xs font-medium mb-2 flex items-center gap-1">
                          <FileText className="w-3 h-3" />
                          参考来源 ({message.chunks.length}):
                        </p>
                        <div className="space-y-2">
                          {message.chunks.slice(0, 3).map((chunk, i) => (
                            <div key={i} className="text-xs bg-background/50 rounded p-2">
                              <div className="flex items-center justify-between mb-1">
                                <span className="font-medium">{chunk.title}</span>
                                <Badge variant="secondary" className="text-xs">
                                  相关度: {(chunk.score * 100).toFixed(1)}%
                                </Badge>
                              </div>
                              <p className="text-muted-foreground line-clamp-2">{chunk.content}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {message.followupQuestions && message.followupQuestions.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-border/50">
                        <p className="text-xs font-medium mb-2">相关问题:</p>
                        <div className="flex flex-wrap gap-1">
                          {message.followupQuestions.map((q, i) => (
                            <Button
                              key={i}
                              variant="outline"
                              size="sm"
                              onClick={() => handleSuggestedQuestion(q)}
                              className="text-xs h-7"
                            >
                              {q}
                            </Button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  {message.role === "user" && (
                    <div className="w-8 h-8 rounded-lg bg-secondary flex items-center justify-center flex-shrink-0">
                      <User className="w-5 h-5 text-secondary-foreground" />
                    </div>
                  )}
                </div>
              ))
            )}
            {loading && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-primary-foreground" />
                </div>
                <div className="bg-muted rounded-lg p-4">
                  <Loader2 className="w-5 h-5 animate-spin text-primary" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="输入您的问题..."
              className="min-h-[60px] resize-none"
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmit(e)
                }
              }}
            />
            <Button type="submit" disabled={!input.trim() || loading} size="icon" className="h-[60px] w-[60px]">
              <Send className="w-5 h-5" />
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
