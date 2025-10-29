"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Upload, File, Trash2, Download, Loader2, RefreshCw, Eye, X, FileText, ImageIcon } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { apiClient, type FileInfo } from "@/lib/api-client"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"

export function FileManager() {
  const [files, setFiles] = useState<FileInfo[]>([])
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [previewFile, setPreviewFile] = useState<FileInfo | null>(null)
  const [previewContent, setPreviewContent] = useState<string>("")
  const [previewLoading, setPreviewLoading] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    loadFiles()
  }, [])

  const loadFiles = async () => {
    setLoading(true)
    try {
      const fileList = await apiClient.getFiles()
      setFiles(fileList)
    } catch (error) {
      toast({
        title: "加载失败",
        description: error instanceof Error ? error.message : "无法加载文件列表",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setSelectedFiles(Array.from(files))
  }

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return

    setUploading(true)

    try {
      const uploadPromises = selectedFiles.map((file) => apiClient.uploadFile(file))
      await Promise.all(uploadPromises)
      await loadFiles()

      toast({
        title: "上传成功",
        description: `已上传 ${selectedFiles.length} 个文件`,
      })

      setSelectedFiles([])
    } catch (error) {
      toast({
        title: "上传失败",
        description: error instanceof Error ? error.message : "请稍后重试",
        variant: "destructive",
      })
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (filename: string) => {
    try {
      await apiClient.deleteFile(filename)
      setFiles((prev) => prev.filter((f) => f.filename !== filename))

      toast({
        title: "删除成功",
        description: "文件已删除",
      })
    } catch (error) {
      toast({
        title: "删除失败",
        description: error instanceof Error ? error.message : "请稍后重试",
        variant: "destructive",
      })
    }
  }

  const handleDownload = async (filename: string) => {
    try {
      const blob = await apiClient.downloadFile(filename)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast({
        title: "下载成功",
        description: `${filename} 已下载`,
      })
    } catch (error) {
      toast({
        title: "下载失败",
        description: error instanceof Error ? error.message : "请稍后重试",
        variant: "destructive",
      })
    }
  }

  const handlePreview = async (file: FileInfo) => {
    setPreviewFile(file)
    setPreviewLoading(true)
    setPreviewContent("")

    try {
      const blob = await apiClient.downloadFile(file.filename)
      const fileExtension = file.filename.split(".").pop()?.toLowerCase()

      if (fileExtension === "txt" || fileExtension === "md") {
        const text = await blob.text()
        setPreviewContent(text)
      } else if (fileExtension === "pdf") {
        const url = window.URL.createObjectURL(blob)
        setPreviewContent(url)
      } else if (["jpg", "jpeg", "png", "gif", "webp"].includes(fileExtension || "")) {
        const url = window.URL.createObjectURL(blob)
        setPreviewContent(url)
      } else {
        setPreviewContent("此文件类型不支持预览")
      }
    } catch (error) {
      toast({
        title: "预览失败",
        description: error instanceof Error ? error.message : "无法预览文件",
        variant: "destructive",
      })
      setPreviewFile(null)
    } finally {
      setPreviewLoading(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B"
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + " KB"
    return (bytes / (1024 * 1024)).toFixed(2) + " MB"
  }

  const getFileIcon = (filename: string) => {
    const ext = filename.split(".").pop()?.toLowerCase()
    if (["jpg", "jpeg", "png", "gif", "webp"].includes(ext || "")) {
      return <ImageIcon className="w-5 h-5 text-blue-500" />
    }
    return <FileText className="w-5 h-5 text-primary" />
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Upload Card */}
      <Card className="border-border/40 bg-gradient-to-br from-card/80 to-card/40 backdrop-blur-xl shadow-lg">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-xl">
            <div className="p-2 rounded-lg bg-primary/10">
              <Upload className="w-5 h-5 text-primary" />
            </div>
            上传文档
          </CardTitle>
          <CardDescription className="text-base">
            支持 TXT、PDF、DOCX、MD 等格式，上传后将自动处理并建立索引
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="relative flex-1">
              <Input
                type="file"
                multiple
                accept=".txt,.pdf,.docx,.doc,.md"
                onChange={handleFileSelect}
                disabled={uploading}
                className="cursor-pointer file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
              />
            </div>
            <Button
              onClick={handleUpload}
              disabled={uploading || selectedFiles.length === 0}
              className="gap-2 px-6 shadow-md hover:shadow-lg transition-shadow"
              size="lg"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  上传中...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  上传 {selectedFiles.length > 0 && `(${selectedFiles.length})`}
                </>
              )}
            </Button>
          </div>

          {selectedFiles.length > 0 && (
            <div className="p-4 rounded-lg bg-muted/50 border border-border/40">
              <p className="text-sm font-medium mb-2">已选择 {selectedFiles.length} 个文件：</p>
              <div className="flex flex-wrap gap-2">
                {selectedFiles.map((file, index) => (
                  <Badge key={index} variant="secondary" className="gap-1">
                    <File className="w-3 h-3" />
                    {file.name}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Files List */}
      <Card className="border-border/40 bg-gradient-to-br from-card/80 to-card/40 backdrop-blur-xl shadow-lg">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-xl">
                <div className="p-2 rounded-lg bg-primary/10">
                  <File className="w-5 h-5 text-primary" />
                </div>
                文档列表
              </CardTitle>
              <CardDescription className="text-base mt-1">共 {files.length} 个文档</CardDescription>
            </div>
            <Button
              variant="outline"
              size="icon"
              onClick={loadFiles}
              disabled={loading}
              className="shadow-sm hover:shadow-md transition-shadow bg-transparent"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-16">
              <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-primary" />
              <p className="text-muted-foreground">加载中...</p>
            </div>
          ) : files.length === 0 ? (
            <div className="text-center py-16 text-muted-foreground">
              <div className="p-4 rounded-full bg-muted/50 w-fit mx-auto mb-4">
                <File className="w-12 h-12 opacity-50" />
              </div>
              <p className="text-lg font-medium">暂无文档</p>
              <p className="text-sm mt-1">请上传文件开始使用</p>
            </div>
          ) : (
            <div className="grid gap-3">
              {files.map((file) => (
                <div
                  key={file.filename}
                  className="group flex items-center justify-between p-4 rounded-xl border border-border/40 bg-gradient-to-r from-background/80 to-background/40 hover:from-accent/20 hover:to-accent/5 transition-all duration-200 hover:shadow-md"
                >
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    <div className="p-2 rounded-lg bg-primary/5 group-hover:bg-primary/10 transition-colors">
                      {getFileIcon(file.filename)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate text-base">{file.filename}</p>
                      <p className="text-sm text-muted-foreground mt-0.5">
                        {formatFileSize(file.size)} • {new Date(file.upload_time).toLocaleString("zh-CN")}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handlePreview(file)}
                      className="hover:bg-primary/10 hover:text-primary"
                    >
                      <Eye className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDownload(file.filename)}
                      className="hover:bg-primary/10 hover:text-primary"
                    >
                      <Download className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(file.filename)}
                      className="hover:bg-destructive/10 hover:text-destructive"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={previewFile !== null} onOpenChange={() => setPreviewFile(null)}>
        <DialogContent className="max-w-4xl max-h-[85vh] p-0">
          <DialogHeader className="p-6 pb-4 border-b">
            <div className="flex items-center justify-between">
              <DialogTitle className="flex items-center gap-2 text-lg">
                {previewFile && getFileIcon(previewFile.filename)}
                {previewFile?.filename}
              </DialogTitle>
              <Button variant="ghost" size="icon" onClick={() => setPreviewFile(null)}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          </DialogHeader>
          <ScrollArea className="h-[calc(85vh-8rem)] p-6">
            {previewLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : previewFile ? (
              <div>
                {previewFile.filename.endsWith(".txt") || previewFile.filename.endsWith(".md") ? (
                  <pre className="whitespace-pre-wrap font-mono text-sm bg-muted/30 p-4 rounded-lg">
                    {previewContent}
                  </pre>
                ) : previewFile.filename.endsWith(".pdf") ? (
                  <iframe src={previewContent} className="w-full h-[600px] rounded-lg border" title="PDF Preview" />
                ) : ["jpg", "jpeg", "png", "gif", "webp"].some((ext) =>
                    previewFile.filename.toLowerCase().endsWith(ext),
                  ) ? (
                  <img
                    src={previewContent || "/placeholder.svg"}
                    alt={previewFile.filename}
                    className="max-w-full h-auto rounded-lg"
                  />
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>{previewContent}</p>
                  </div>
                )}
              </div>
            ) : null}
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </div>
  )
}
