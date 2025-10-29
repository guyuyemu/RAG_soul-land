"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Network, Loader2, RefreshCw, Info } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { apiClient, type KnowledgeGraphStats } from "@/lib/api-client"

export function KnowledgeGraph() {
  const [loading, setLoading] = useState(false)
  const [graphUrl, setGraphUrl] = useState<string | null>(null)
  const [stats, setStats] = useState<KnowledgeGraphStats | null>(null)
  const [topN, setTopN] = useState(20)
  const { toast } = useToast()

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const statsData = await apiClient.getKnowledgeGraphStats()
      setStats(statsData)
      // If stats exist, set the graph URL
      setGraphUrl(apiClient.getKnowledgeGraphViewURL())
    } catch (error) {
      // Stats might not exist yet, that's okay
      console.log("No existing graph stats")
    }
  }

  const generateGraph = async () => {
    setLoading(true)
    try {
      const data = await apiClient.generateKnowledgeGraph(topN)

      setGraphUrl(apiClient.getKnowledgeGraphViewURL())
      setStats(data.statistics)

      toast({
        title: "生成成功",
        description: data.message,
      })
    } catch (error) {
      toast({
        title: "生成失败",
        description: error instanceof Error ? error.message : "请稍后重试",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Control Card */}
      <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="w-5 h-5 text-primary" />
            知识图谱生成
          </CardTitle>
          <CardDescription>基于上传的文档自动提取实体和关系,生成可视化知识图谱</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 mb-4">
            <div className="flex items-center gap-2 flex-1">
              <label htmlFor="topN" className="text-sm font-medium whitespace-nowrap">
                显示实体数（前N%）:
              </label>
              <Input
                id="topN"
                type="number"
                min={0}
                max={100}
                value={topN}
                onChange={(e) => setTopN(Number(e.target.value))}
                disabled={loading}
                className="w-32"
              />
              <span className="text-xs text-muted-foreground">
                <Info className="w-3 h-3 inline mr-1" />
                显示前N%个高频实体
              </span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Button onClick={generateGraph} disabled={loading} className="gap-2">
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  生成中...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  生成图谱
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Graph Display */}
      <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
        <CardContent className="p-0">
          {!graphUrl ? (
            <div className="text-center py-24 text-muted-foreground">
              <Network className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium mb-2">暂无图谱数据</p>
              <p className="text-sm">点击上方按钮生成知识图谱</p>
            </div>
          ) : (
            <div className="relative w-full" style={{ height: "70vh" }}>
              <iframe src={graphUrl} className="w-full h-full rounded-lg" title="知识图谱" />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Stats Card */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardDescription>总实体数</CardDescription>
              <CardTitle className="text-3xl text-primary">{stats.total_entities.toLocaleString()}</CardTitle>
            </CardHeader>
          </Card>
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardDescription>自定义实体</CardDescription>
              <CardTitle className="text-3xl text-accent">{stats.custom_entities.toLocaleString()}</CardTitle>
            </CardHeader>
          </Card>
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardDescription>关系数量</CardDescription>
              <CardTitle className="text-3xl text-chart-2">{stats.total_relations.toLocaleString()}</CardTitle>
            </CardHeader>
          </Card>
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardDescription>图谱节点</CardDescription>
              <CardTitle className="text-3xl text-chart-3">{stats.graph_nodes.toLocaleString()}</CardTitle>
            </CardHeader>
          </Card>
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardDescription>图谱边</CardDescription>
              <CardTitle className="text-3xl text-chart-4">{stats.graph_edges.toLocaleString()}</CardTitle>
            </CardHeader>
          </Card>
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardDescription>关系类型</CardDescription>
              <CardTitle className="text-3xl text-chart-5">{stats.relation_types}</CardTitle>
            </CardHeader>
          </Card>
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardDescription>平均度数</CardDescription>
              <CardTitle className="text-3xl text-primary">{stats.avg_degree.toFixed(1)}</CardTitle>
            </CardHeader>
          </Card>
        </div>
      )}
    </div>
  )
}
