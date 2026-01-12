// API client for the Prompt-to-Video backend

import type {
  FullGenerationRequest,
  FullGenerationResponse,
  GenerationResult,
  JobProgress,
  LanguageDetectionResponse,
  TTSResponse,
  Voice,
  VoiceCloneResponse,
} from '../types'

const API_BASE = '/api'

class ApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `API error: ${response.status}`)
    }

    return response.json()
  }

  // Generic POST method
  async post<T>(endpoint: string, data: any): Promise<{ data: T }> {
    const result = await this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    })
    return { data: result }
  }

  // Generic GET method
  async get<T>(endpoint: string): Promise<{ data: T }> {
    const result = await this.request<T>(endpoint)
    return { data: result }
  }

  // Language Detection
  async detectLanguage(text: string): Promise<LanguageDetectionResponse> {
    return this.request('/language/detect', {
      method: 'POST',
      body: JSON.stringify({ text }),
    })
  }

  // Voice Cloning
  async cloneVoice(
    audioFile: File,
    name: string,
    description?: string
  ): Promise<VoiceCloneResponse> {
    const formData = new FormData()
    formData.append('audio_file', audioFile)
    formData.append('name', name)
    if (description) {
      formData.append('description', description)
    }

    const response = await fetch(`${API_BASE}/voice/clone`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || 'Failed to clone voice')
    }

    return response.json()
  }

  async synthesizeSpeech(
    text: string,
    voiceId?: string,
    language?: string,
    speed?: number
  ): Promise<TTSResponse> {
    return this.request('/voice/synthesize', {
      method: 'POST',
      body: JSON.stringify({
        text,
        voice_id: voiceId,
        language,
        speed: speed || 1.0,
      }),
    })
  }

  async listVoices(): Promise<{ voices: Voice[]; provider: string }> {
    return this.request('/voice/voices')
  }

  // Video Generation
  async createVideo(request: FullGenerationRequest): Promise<FullGenerationResponse> {
    return this.request('/generation/create', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  async getJobStatus(jobId: string): Promise<JobProgress> {
    return this.request(`/generation/status/${jobId}`)
  }

  async getJobResult(jobId: string): Promise<GenerationResult> {
    return this.request(`/generation/result/${jobId}`)
  }

  async cancelJob(jobId: string): Promise<{ status: string; job_id: string }> {
    return this.request(`/generation/jobs/${jobId}`, {
      method: 'DELETE',
    })
  }

  async estimateCost(
    duration: number,
    resolution: string
  ): Promise<{
    video_cost: number
    voice_cost: number
    total_cost: number
    duration_seconds: number
    providers: { video: string; voice: string }
  }> {
    return this.request(`/generation/estimate?duration=${duration}&resolution=${resolution}`)
  }

  // Health Check
  async healthCheck(): Promise<{
    status: string
    version: string
    providers: { video: string; voice: string; language: string }
  }> {
    return this.request('/health')
  }
}

export const api = new ApiClient()
export const apiClient = api  // Export as apiClient for consistency

// WebSocket helper for real-time progress
export function createProgressWebSocket(
  jobId: string,
  onProgress: (progress: JobProgress) => void,
  onError: (error: Error) => void
): WebSocket {
  const ws = new WebSocket(`ws://${window.location.host}/ws/progress/${jobId}`)

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      onProgress(data)
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e)
    }
  }

  ws.onerror = () => {
    onError(new Error('WebSocket connection error'))
  }

  // Keep connection alive
  const pingInterval = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send('ping')
    }
  }, 30000)

  ws.onclose = () => {
    clearInterval(pingInterval)
  }

  return ws
}
