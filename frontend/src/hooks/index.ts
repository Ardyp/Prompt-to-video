import { useState, useRef, useCallback, useEffect } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { api, createProgressWebSocket } from '../api/client'
import type {
  FullGenerationRequest,
  GenerationResult,
  GenerationState,
  JobProgress,
  LanguageInfo,
} from '../types'

// Hook for audio recording
export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [duration, setDuration] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<number | null>(null)

  const startRecording = useCallback(async () => {
    try {
      setError(null)
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/wav' })
        setAudioBlob(blob)
        stream.getTracks().forEach((track) => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
      setDuration(0)

      timerRef.current = window.setInterval(() => {
        setDuration((d) => d + 1)
      }, 1000)
    } catch (err) {
      setError('Microphone access denied')
      console.error('Recording error:', err)
    }
  }, [])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
  }, [isRecording])

  const clearRecording = useCallback(() => {
    setAudioBlob(null)
    setDuration(0)
    setError(null)
  }, [])

  return {
    isRecording,
    audioBlob,
    duration,
    error,
    startRecording,
    stopRecording,
    clearRecording,
  }
}

// Hook for language detection with debounce
export function useLanguageDetection(text: string, delay: number = 500) {
  const [detectedLanguage, setDetectedLanguage] = useState<LanguageInfo | null>(null)
  const [isDetecting, setIsDetecting] = useState(false)

  useEffect(() => {
    if (text.length < 10) {
      setDetectedLanguage(null)
      return
    }

    setIsDetecting(true)
    const timer = setTimeout(async () => {
      try {
        const result = await api.detectLanguage(text)
        setDetectedLanguage(result.detected_language)
      } catch (err) {
        console.error('Language detection error:', err)
      } finally {
        setIsDetecting(false)
      }
    }, delay)

    return () => clearTimeout(timer)
  }, [text, delay])

  return { detectedLanguage, isDetecting }
}

// Hook for video generation with progress tracking
export function useVideoGeneration() {
  const [state, setState] = useState<GenerationState>({
    isGenerating: false,
    jobId: null,
    progress: null,
    result: null,
    error: null,
  })

  const wsRef = useRef<WebSocket | null>(null)
  const pollIntervalRef = useRef<number | null>(null)

  const startGeneration = useCallback(async (request: FullGenerationRequest) => {
    setState({
      isGenerating: true,
      jobId: null,
      progress: null,
      result: null,
      error: null,
    })

    try {
      const response = await api.createVideo(request)
      const jobId = response.job_id

      setState((s) => ({ ...s, jobId }))

      // Set up WebSocket for progress updates
      wsRef.current = createProgressWebSocket(
        jobId,
        (progress) => {
          setState((s) => ({ ...s, progress }))

          if (progress.status === 'completed') {
            fetchResult(jobId)
          } else if (progress.status === 'failed') {
            setState((s) => ({
              ...s,
              isGenerating: false,
              error: progress.error || 'Generation failed',
            }))
          }
        },
        (error) => {
          // Fallback to polling if WebSocket fails
          startPolling(jobId)
        }
      )
    } catch (err) {
      setState({
        isGenerating: false,
        jobId: null,
        progress: null,
        result: null,
        error: err instanceof Error ? err.message : 'Generation failed',
      })
    }
  }, [])

  const fetchResult = useCallback(async (jobId: string) => {
    try {
      const result = await api.getJobResult(jobId)
      setState((s) => ({
        ...s,
        isGenerating: false,
        result,
      }))
    } catch (err) {
      setState((s) => ({
        ...s,
        isGenerating: false,
        error: err instanceof Error ? err.message : 'Failed to fetch result',
      }))
    }
  }, [])

  const startPolling = useCallback((jobId: string) => {
    pollIntervalRef.current = window.setInterval(async () => {
      try {
        const progress = await api.getJobStatus(jobId)
        setState((s) => ({ ...s, progress }))

        if (progress.status === 'completed') {
          stopPolling()
          fetchResult(jobId)
        } else if (progress.status === 'failed') {
          stopPolling()
          setState((s) => ({
            ...s,
            isGenerating: false,
            error: progress.error || 'Generation failed',
          }))
        }
      } catch (err) {
        console.error('Polling error:', err)
      }
    }, 2000)
  }, [fetchResult])

  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
  }, [])

  const cancelGeneration = useCallback(async () => {
    if (state.jobId) {
      try {
        await api.cancelJob(state.jobId)
      } catch (err) {
        console.error('Cancel error:', err)
      }
    }

    wsRef.current?.close()
    stopPolling()

    setState({
      isGenerating: false,
      jobId: null,
      progress: null,
      result: null,
      error: null,
    })
  }, [state.jobId, stopPolling])

  const reset = useCallback(() => {
    wsRef.current?.close()
    stopPolling()
    setState({
      isGenerating: false,
      jobId: null,
      progress: null,
      result: null,
      error: null,
    })
  }, [stopPolling])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      wsRef.current?.close()
      stopPolling()
    }
  }, [stopPolling])

  return {
    ...state,
    startGeneration,
    cancelGeneration,
    reset,
  }
}

// Hook for voice cloning
export function useVoiceClone() {
  return useMutation({
    mutationFn: async ({
      audioFile,
      name,
      description,
    }: {
      audioFile: File
      name: string
      description?: string
    }) => {
      return api.cloneVoice(audioFile, name, description)
    },
  })
}

// Hook for fetching available voices
export function useVoices() {
  return useQuery({
    queryKey: ['voices'],
    queryFn: () => api.listVoices(),
  })
}

// Hook for cost estimation
export function useCostEstimate(duration: number, resolution: string) {
  return useQuery({
    queryKey: ['cost-estimate', duration, resolution],
    queryFn: () => api.estimateCost(duration, resolution),
    enabled: duration > 0,
  })
}
