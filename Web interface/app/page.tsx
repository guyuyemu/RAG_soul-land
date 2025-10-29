"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { FileManager } from "@/components/file-manager"
import { KnowledgeGraph } from "@/components/knowledge-graph"
import { QASystem } from "@/components/qa-system"
import { Brain, FileText, MessageSquare } from "lucide-react"

export default function Home() {
  const [activeTab, setActiveTab] = useState("qa")

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
      {/* Header */}
      <header className="border-b border-border/40 bg-card/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                <Brain className="w-6 h-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                  斗罗大陆 RAG 系统
                </h1>
                <p className="text-xs text-muted-foreground">智能知识问答与图谱可视化</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full max-w-md mx-auto grid-cols-3 mb-8 bg-card/50 backdrop-blur-sm">
            <TabsTrigger value="qa" className="gap-2">
              <MessageSquare className="w-4 h-4" />
              问答系统
            </TabsTrigger>
            <TabsTrigger value="graph" className="gap-2">
              <Brain className="w-4 h-4" />
              知识图谱
            </TabsTrigger>
            <TabsTrigger value="files" className="gap-2">
              <FileText className="w-4 h-4" />
              文件管理
            </TabsTrigger>
          </TabsList>

          <TabsContent value="qa" className="mt-0">
            <QASystem />
          </TabsContent>

          <TabsContent value="graph" className="mt-0">
            <KnowledgeGraph />
          </TabsContent>

          <TabsContent value="files" className="mt-0">
            <FileManager />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
