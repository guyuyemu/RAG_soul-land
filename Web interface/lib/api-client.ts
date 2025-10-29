const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://36.213.46.197:4210"

// Type definitions based on API.md
export interface FileInfo {
  filename: string
  size: number
  upload_time: string
  path: string
}

export interface UploadResponse {
  message: string
  filename: string
  size: number
  path: string
}

export interface DeleteResponse {
  message: string
  filename: string
}

export interface KnowledgeGraphStats {
  total_entities: number
  custom_entities: number
  total_relations: number
  graph_nodes: number
  graph_edges: number
  relation_types: number
  avg_degree: number
}

export interface KnowledgeGraphResponse {
  message: string
  html_url: string
  statistics: KnowledgeGraphStats
}

export interface EntityRelation {
  target?: string
  source?: string
  relation: string
  weight: number
}

export interface EntityInfo {
  entity: string
  outgoing: EntityRelation[]
  incoming: EntityRelation[]
}

export interface RetrievedChunk {
  title: string
  content: string
  score: number
  chunk_index: number
}

export interface QAResponse {
  query: string
  answer: string
  retrieved_chunks: RetrievedChunk[]
  processing_time: number
  followup_questions?: string[]
}

export interface QARequest {
  query: string
  top_k?: number
  use_cache?: boolean
  custom_instruction?: string | null
  enable_followup?: boolean
}

export interface CacheStats {
  cache_size: number
  cache_dir: string
  cache_file: string
}

export interface SystemStats {
  documents: {
    total: number
    chunks: number
    titles: string[]
  }
  retriever: {
    model_name: string
    model_type: string
    embedding_dimension: number
    retrieval_method: string
  }
  cache: {
    size: number
  }
  config: {
    chunk_size: number
    chunk_overlap: number
    default_top_k: number
    rerank_top_k: number
    custom_words_count: number
  }
}

export interface HealthResponse {
  status: string
  rag_system: string
  kg_builder: string
  timestamp: string
}

// API Client Class
class APIClient {
  private baseURL: string

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL
  }

  // Health Check
  async checkHealth(): Promise<HealthResponse> {
    const response = await fetch(`${this.baseURL}/api/health`)
    if (!response.ok) throw new Error("Health check failed")
    return response.json()
  }

  // File Management
  async getFiles(): Promise<FileInfo[]> {
    const response = await fetch(`${this.baseURL}/api/files`)
    if (!response.ok) throw new Error("Failed to fetch files")
    return response.json()
  }

  async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append("file", file)

    const response = await fetch(`${this.baseURL}/api/files/upload`, {
      method: "POST",
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Upload failed" }))
      throw new Error(error.detail || "Upload failed")
    }

    return response.json()
  }

  async deleteFile(filename: string): Promise<DeleteResponse> {
    const response = await fetch(`${this.baseURL}/api/files/${encodeURIComponent(filename)}`, {
      method: "DELETE",
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Delete failed" }))
      throw new Error(error.detail || "Delete failed")
    }

    return response.json()
  }

  async downloadFile(filename: string): Promise<Blob> {
    const response = await fetch(`${this.baseURL}/api/files/${encodeURIComponent(filename)}/download`)

    if (!response.ok) throw new Error("Download failed")

    return response.blob()
  }

  // Knowledge Graph
  async generateKnowledgeGraph(topN = 500): Promise<KnowledgeGraphResponse> {
    const response = await fetch(`${this.baseURL}/api/knowledge-graph/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ top_n: topN }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Generation failed" }))
      throw new Error(error.detail || "Generation failed")
    }

    return response.json()
  }



  async getEntityInfo(entityName: string): Promise<EntityInfo> {
    const response = await fetch(`${this.baseURL}/api/knowledge-graph/entity/${encodeURIComponent(entityName)}`)
    if (!response.ok) throw new Error("Failed to fetch entity info")
    return response.json()
  }

  getKnowledgeGraphViewURL(): string {
    return `${this.baseURL}/api/knowledge-graph/view`
  }

  // Q&A System
  async askQuestion(request: QARequest): Promise<QAResponse> {
    const response = await fetch(`${this.baseURL}/api/qa`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Query failed" }))
      throw new Error(error.detail || "Query failed")
    }

    return response.json()
  }

  async getCacheStats(): Promise<CacheStats> {
    const response = await fetch(`${this.baseURL}/api/qa/cache/stats`)
    if (!response.ok) throw new Error("Failed to fetch cache stats")
    return response.json()
  }

  async clearCache(): Promise<{ message: string }> {
    const response = await fetch(`${this.baseURL}/api/qa/cache`, {
      method: "DELETE",
    })

    if (!response.ok) throw new Error("Failed to clear cache")
    return response.json()
  }

  // System Stats
  async getSystemStats(): Promise<SystemStats> {
    const response = await fetch(`${this.baseURL}/api/system/stats`)
    if (!response.ok) throw new Error("Failed to fetch system stats")
    return response.json()
  }
}

// Export singleton instance
export const apiClient = new APIClient()
