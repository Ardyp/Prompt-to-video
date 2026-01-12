import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Sparkles,
  Mic,
  Video,
  Settings,
  Play,
  Download,
  RefreshCw,
  ChevronDown,
  Globe,
  Loader2,
  Check,
  X,
  Volume2,
  Wand2,
} from 'lucide-react'
import {
  useVideoGeneration,
  useLanguageDetection,
  useAudioRecorder,
  useCostEstimate,
} from './hooks'
import { PromptEnhancer } from './components/PromptEnhancer'
import type { FullGenerationRequest } from './types'

// Language flag mapping
const languageFlags: Record<string, string> = {
  en: '🇺🇸', es: '🇪🇸', fr: '🇫🇷', de: '🇩🇪', it: '🇮🇹',
  pt: '🇵🇹', zh: '🇨🇳', ja: '🇯🇵', ko: '🇰🇷', ar: '🇸🇦',
  hi: '🇮🇳', ru: '🇷🇺', nl: '🇳🇱', tr: '🇹🇷', pl: '🇵🇱',
}

function App() {
  const [prompt, setPrompt] = useState('')
  const [duration, setDuration] = useState(8)
  const [aspectRatio, setAspectRatio] = useState('16:9')
  const [resolution, setResolution] = useState('720p')
  const [style, setStyle] = useState('')
  const [showSettings, setShowSettings] = useState(false)
  const [showEnhancer, setShowEnhancer] = useState(false)

  const { detectedLanguage, isDetecting } = useLanguageDetection(prompt)
  const { data: costEstimate } = useCostEstimate(duration, resolution)
  const recorder = useAudioRecorder()
  const generation = useVideoGeneration()

  const handleGenerate = () => {
    const request: FullGenerationRequest = {
      prompt,
      video_duration: duration,
      aspect_ratio: aspectRatio,
      resolution,
      video_style: style || undefined,
      detect_language: true,
    }
    generation.startGeneration(request)
  }

  const handleEnhancedPromptSelected = (enhancedPrompt: string, negativePrompt: string) => {
    setPrompt(enhancedPrompt)
    setShowEnhancer(false)
    // Optionally scroll to the prompt input
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const getStatusMessage = () => {
    if (!generation.progress) return ''
    
    const statusMessages: Record<string, string> = {
      pending: 'Starting up...',
      detecting_language: 'Analyzing language...',
      cloning_voice: 'Cloning voice...',
      generating_speech: 'Creating narration...',
      generating_video: 'Generating video... (2-5 min)',
      merging: 'Merging audio & video...',
      completed: 'Done!',
      failed: 'Failed',
    }
    return statusMessages[generation.progress.status] || generation.progress.current_step
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      {/* Background gradient */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-50%] left-[-50%] w-[200%] h-[200%] bg-[radial-gradient(ellipse_at_center,_rgba(99,102,241,0.08)_0%,_transparent_50%)]" />
      </div>

      <div className="relative max-w-4xl mx-auto px-4 py-12">
        {/* Header */}
        <motion.header 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-6">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <span className="text-sm text-zinc-400">AI-Powered Video Generation</span>
          </div>
          
          <h1 className="font-display text-5xl md:text-6xl lg:text-7xl mb-4">
            <span className="gradient-text">Prompt to Video</span>
          </h1>
          
          <p className="text-zinc-400 text-lg max-w-xl mx-auto">
            Transform your ideas into stunning videos with AI narration.
            Just type your prompt and let the magic happen.
          </p>
        </motion.header>

        {/* Main Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass rounded-3xl p-6 md:p-8 mb-8"
        >
          {/* Prompt Input */}
          <div className="relative mb-4">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe your video... e.g., 'A serene mountain landscape at sunrise with mist rolling through the valleys'"
              className="w-full h-32 bg-white/5 border border-white/10 rounded-2xl px-5 py-4 text-white placeholder:text-zinc-500 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-transparent transition-all"
              disabled={generation.isGenerating}
            />

            {/* Language Badge */}
            <AnimatePresence>
              {detectedLanguage && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="absolute top-3 right-3 flex items-center gap-2 px-3 py-1.5 bg-white/10 rounded-full"
                >
                  <Globe className="w-3.5 h-3.5 text-zinc-400" />
                  <span className="text-sm">
                    {languageFlags[detectedLanguage.code] || '🌐'} {detectedLanguage.name}
                  </span>
                  {isDetecting && <Loader2 className="w-3 h-3 animate-spin" />}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* AI Enhance Button */}
          <div className="mb-6">
            <button
              onClick={() => setShowEnhancer(!showEnhancer)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border transition-all ${
                showEnhancer
                  ? 'border-purple-500/50 bg-purple-500/10 text-purple-400'
                  : 'border-white/10 bg-white/5 text-zinc-400 hover:bg-white/10 hover:text-white'
              }`}
              disabled={generation.isGenerating}
            >
              <Wand2 className="w-4 h-4" />
              <span className="text-sm font-medium">
                {showEnhancer ? 'Hide' : 'Show'} AI Prompt Enhancer
              </span>
              <ChevronDown className={`w-4 h-4 transition-transform ml-auto ${showEnhancer ? 'rotate-180' : ''}`} />
            </button>
          </div>

          {/* Prompt Enhancer Component */}
          <AnimatePresence>
            {showEnhancer && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden mb-6"
              >
                <PromptEnhancer
                  prompt={prompt}
                  onEnhanced={handleEnhancedPromptSelected}
                />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Quick Settings */}
          <div className="flex flex-wrap gap-3 mb-6">
            <select
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
              disabled={generation.isGenerating}
            >
              <option value={8}>8 seconds</option>
              <option value={10}>10 seconds</option>
              <option value={15}>15 seconds</option>
              <option value={20}>20 seconds</option>
              <option value={30}>30 seconds</option>
            </select>

            <select
              value={aspectRatio}
              onChange={(e) => setAspectRatio(e.target.value)}
              className="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
              disabled={generation.isGenerating}
            >
              <option value="16:9">16:9 Landscape</option>
              <option value="9:16">9:16 Portrait</option>
              <option value="1:1">1:1 Square</option>
            </select>

            <select
              value={resolution}
              onChange={(e) => setResolution(e.target.value)}
              className="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
              disabled={generation.isGenerating}
            >
              <option value="720p">720p HD</option>
              <option value="1080p">1080p Full HD</option>
            </select>

            <button
              onClick={() => setShowSettings(!showSettings)}
              className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm hover:bg-white/10 transition-colors"
            >
              <Settings className="w-4 h-4" />
              More
              <ChevronDown className={`w-4 h-4 transition-transform ${showSettings ? 'rotate-180' : ''}`} />
            </button>
          </div>

          {/* Advanced Settings */}
          <AnimatePresence>
            {showSettings && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden mb-6"
              >
                <div className="pt-4 border-t border-white/10">
                  <label className="block text-sm text-zinc-400 mb-2">Visual Style</label>
                  <input
                    type="text"
                    value={style}
                    onChange={(e) => setStyle(e.target.value)}
                    placeholder="e.g., cinematic, anime, documentary, sci-fi"
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                    disabled={generation.isGenerating}
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Voice Recording Section */}
          <div className="flex items-center gap-4 mb-6 p-4 bg-white/5 rounded-xl">
            <div className="flex items-center gap-3">
              <button
                onClick={recorder.isRecording ? recorder.stopRecording : recorder.startRecording}
                className={`p-3 rounded-full transition-all ${
                  recorder.isRecording 
                    ? 'bg-red-500 recording-pulse' 
                    : 'bg-white/10 hover:bg-white/20'
                }`}
                disabled={generation.isGenerating}
              >
                <Mic className="w-5 h-5" />
              </button>
              
              <div className="text-sm">
                {recorder.isRecording ? (
                  <span className="text-red-400">Recording... {recorder.duration}s</span>
                ) : recorder.audioBlob ? (
                  <span className="text-green-400 flex items-center gap-1">
                    <Check className="w-4 h-4" /> Voice recorded ({recorder.duration}s)
                  </span>
                ) : (
                  <span className="text-zinc-400">Record your voice (optional)</span>
                )}
              </div>
            </div>

            {recorder.audioBlob && (
              <button
                onClick={recorder.clearRecording}
                className="ml-auto p-2 text-zinc-400 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Cost Estimate */}
          {costEstimate && (
            <div className="text-sm text-zinc-400 mb-6">
              Estimated cost: <span className="text-white">${costEstimate.total_cost.toFixed(2)}</span>
            </div>
          )}

          {/* Generate Button */}
          <button
            onClick={handleGenerate}
            disabled={!prompt.trim() || generation.isGenerating}
            className="w-full py-4 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-2xl font-semibold text-lg flex items-center justify-center gap-3 hover:from-indigo-600 hover:to-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all glow"
          >
            {generation.isGenerating ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Video className="w-5 h-5" />
                Generate Video
              </>
            )}
          </button>
        </motion.div>

        {/* Progress Section */}
        <AnimatePresence>
          {generation.isGenerating && generation.progress && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="glass rounded-3xl p-6 md:p-8 mb-8"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold">Generation Progress</h3>
                <button
                  onClick={generation.cancelGeneration}
                  className="text-sm text-zinc-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
              </div>

              <div className="relative h-3 bg-white/10 rounded-full overflow-hidden mb-3">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${generation.progress.progress}%` }}
                  className="absolute inset-y-0 left-0 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full progress-shine"
                />
              </div>

              <div className="flex items-center justify-between text-sm">
                <span className="text-zinc-400">{getStatusMessage()}</span>
                <span className="text-white">{Math.round(generation.progress.progress)}%</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Result Section */}
        <AnimatePresence>
          {generation.result && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass rounded-3xl p-6 md:p-8"
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="font-semibold text-xl">Your Video is Ready!</h3>
                <button
                  onClick={generation.reset}
                  className="flex items-center gap-2 text-sm text-zinc-400 hover:text-white transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  Create Another
                </button>
              </div>

              {/* Video Player */}
              <div className="relative rounded-2xl overflow-hidden bg-black mb-6">
                <video
                  src={generation.result.video_url}
                  poster={generation.result.thumbnail_url}
                  controls
                  className="w-full aspect-video"
                />
              </div>

              {/* Video Info */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-white/5 rounded-xl p-4">
                  <div className="text-sm text-zinc-400 mb-1">Duration</div>
                  <div className="font-semibold">{generation.result.duration_seconds}s</div>
                </div>
                
                {generation.result.detected_language && (
                  <div className="bg-white/5 rounded-xl p-4">
                    <div className="text-sm text-zinc-400 mb-1">Language</div>
                    <div className="font-semibold">
                      {languageFlags[generation.result.detected_language.code]} {generation.result.detected_language.name}
                    </div>
                  </div>
                )}
                
                <div className="bg-white/5 rounded-xl p-4">
                  <div className="text-sm text-zinc-400 mb-1">Processing Time</div>
                  <div className="font-semibold">{generation.result.processing_time_seconds.toFixed(1)}s</div>
                </div>
                
                {generation.result.cost_estimate && (
                  <div className="bg-white/5 rounded-xl p-4">
                    <div className="text-sm text-zinc-400 mb-1">Cost</div>
                    <div className="font-semibold">${generation.result.cost_estimate.toFixed(2)}</div>
                  </div>
                )}
              </div>

              {/* Download Buttons */}
              <div className="flex flex-wrap gap-3">
                <a
                  href={generation.result.video_url}
                  download
                  className="flex items-center gap-2 px-6 py-3 bg-indigo-500 rounded-xl font-medium hover:bg-indigo-600 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Download Video
                </a>
                
                {generation.result.audio_url && (
                  <a
                    href={generation.result.audio_url}
                    download
                    className="flex items-center gap-2 px-6 py-3 bg-white/10 rounded-xl font-medium hover:bg-white/20 transition-colors"
                  >
                    <Volume2 className="w-4 h-4" />
                    Download Audio
                  </a>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error Display */}
        <AnimatePresence>
          {generation.error && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-red-500/10 border border-red-500/20 rounded-2xl p-6 text-center"
            >
              <p className="text-red-400 mb-4">{generation.error}</p>
              <button
                onClick={generation.reset}
                className="px-6 py-2 bg-red-500/20 rounded-xl text-red-400 hover:bg-red-500/30 transition-colors"
              >
                Try Again
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

export default App
