import axios from 'axios'
import type {
  UploadResponse,
  AgentRequest,
  SummaryResponse,
  RecommendationsResponse,
  RetrievalRequest,
  RetrievalWithScoresResponse,
} from '../types/api'

const http = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

export const api = {
  uploadPdf: async (file: File): Promise<UploadResponse> => {
    const form = new FormData()
    form.append('file', file)
    const { data } = await http.post<UploadResponse>('/data/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  getSummary: async (req: AgentRequest): Promise<SummaryResponse> => {
    const { data } = await http.post<SummaryResponse>('/chat/summary', req)
    return data
  },

  getRecommendations: async (req: AgentRequest): Promise<RecommendationsResponse> => {
    const { data } = await http.post<RecommendationsResponse>('/chat/recommendations', req)
    return data
  },

  searchWithScores: async (req: RetrievalRequest): Promise<RetrievalWithScoresResponse> => {
    const { data } = await http.post<RetrievalWithScoresResponse>(
      '/search/search-with-scores',
      req,
    )
    return data
  },
}
