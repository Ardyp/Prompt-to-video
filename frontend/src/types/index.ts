// API Types

export type JobStatus = 
  | 'pending'
  | 'detecting_language'
  | 'cloning_voice'
  | 'generating_speech'
  | 'generating_video'
  | 'merging'
  | 'completed'
  | 'failed'

export interface LanguageInfo {
  code: string
  name: string
  confidence: number
}

export interface LanguageDetectionResponse {
  detected_language: LanguageInfo
  alternatives: LanguageInfo[]
  processing_time_ms: number
}

export interface VoiceCloneResponse {
  voice_id: string
  name: string
  status: string
  created_at: string
}

export interface TTSResponse {
  audio_url: string
  duration_seconds: number
  format: string
}

export interface FullGenerationRequest {
  prompt: string
  voice_id?: string
  video_duration: number
  aspect_ratio: string
  resolution: string
  video_style?: string
  detect_language: boolean
}

export interface FullGenerationResponse {
  job_id: string
  status: JobStatus
  message: string
  websocket_url: string
}

export interface JobProgress {
  job_id: string
  status: JobStatus
  progress: number
  current_step: string
  message?: string
  error?: string
  created_at: string
  updated_at: string
  estimated_completion?: string
}

export interface GenerationResult {
  job_id: string
  status: JobStatus
  video_url: string
  audio_url?: string
  thumbnail_url?: string
  duration_seconds: number
  detected_language?: LanguageInfo
  processing_time_seconds: number
  cost_estimate?: number
  metadata: Record<string, unknown>
}

export interface Voice {
  voice_id: string
  name: string
  preview_url?: string
}

// UI State types
export interface GenerationState {
  isGenerating: boolean
  jobId: string | null
  progress: JobProgress | null
  result: GenerationResult | null
  error: string | null
}
