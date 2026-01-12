import { useState } from 'react'
import { apiClient } from '../api/client'

export interface EnhancementResult {
  success: boolean
  method: string
  enhanced_prompt: string
  negative_prompt: string
  frame_guidance: Array<{
    time_range: string
    focus: string
    motion: string
    transition: string
  }>
  aesthetic_score: {
    overall: number
    composition: number
    clarity: number
    creativity: number
    technical: number
    cultural: number
    motion: number
    audio: number
  }
  concepts_detected: Array<{
    type: string
    value: string
    confidence: number
    cultural_context?: string
  }>
  styles_detected: Array<{
    category: string
    value: string
    confidence: number
  }>
  cultural_notes: string[]
  technical_specs: {
    camera_work?: string
    lighting?: string
    color_palette?: string[]
    mood?: string
  }
  validation?: {
    passed: boolean
    warnings: string[]
  }
  metadata: {
    original_prompt: string
    llm_confidence?: number
    llm_reasoning?: string
    processing_time_ms?: number
    tokens_used?: number
    model_used?: string
    enhancement_iterations?: number
    final_confidence?: number
  }
}

export function usePromptEnhancement() {
  const [enhancedData, setEnhancedData] = useState<EnhancementResult | null>(null)
  const [isEnhancing, setIsEnhancing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const enhance = async (
    prompt: string,
    duration: number = 10,
    method: 'hybrid' | 'llm' | 'rule_based' = 'hybrid'
  ) => {
    if (!prompt.trim()) {
      setError('Please enter a prompt first')
      return
    }

    setIsEnhancing(true)
    setError(null)

    try {
      const response = await apiClient.post<EnhancementResult>('/api/prompt/enhance', {
        prompt,
        duration,
        enhancement_method: method,
      })

      setEnhancedData(response.data)
    } catch (err: any) {
      console.error('Enhancement error:', err)
      setError(
        err.response?.data?.detail ||
        err.message ||
        'Failed to enhance prompt. The system may have fallen back to rule-based enhancement.'
      )

      // If it's a fallback, we might still have data
      if (err.response?.data?.enhanced_prompt) {
        setEnhancedData(err.response.data as EnhancementResult)
      }
    } finally {
      setIsEnhancing(false)
    }
  }

  const reset = () => {
    setEnhancedData(null)
    setError(null)
  }

  return {
    enhance,
    enhancedData,
    isEnhancing,
    error,
    reset,
  }
}
