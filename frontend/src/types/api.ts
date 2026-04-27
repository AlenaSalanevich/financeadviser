// Upload
export interface UploadResponse {
  filename: string
  size_bytes: number
  chunks_stored: number
  message: string
}

// Agent / Chat
export interface AgentRequest {
  query: string
  k?: number
  source?: string | null
}

export interface SummaryResponse {
  summary: string
  query: string
  documents_used: number
  sources: string[]
  model: string
}

export interface RecommendationsResponse {
  recommendations: string
  query: string
  documents_used: number
  sources: string[]
  model: string
}

// Search
export interface RetrievalRequest {
  query: string
  k?: number
  source?: string | null
}

export interface DocumentResult {
  content: string
  source: string
  page: number
  score?: number
  metadata: Record<string, unknown>
}

export interface RetrievalResponse {
  query: string
  documents: DocumentResult[]
  count: number
}

export interface RetrievalWithScoresResponse {
  query: string
  results: DocumentResult[]
  count: number
}
