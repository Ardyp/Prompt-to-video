import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Sparkles,
  Wand2,
  Brain,
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  Info,
  Zap,
  Shield,
  Loader2,
  Copy,
  Check,
  TrendingUp,
  Palette,
  Camera,
  Lightbulb,
  Globe2
} from 'lucide-react'
import { usePromptEnhancement } from '../hooks/usePromptEnhancement'

interface PromptEnhancerProps {
  prompt: string
  onEnhanced: (enhancedPrompt: string, negativePrompt: string) => void
}

export function PromptEnhancer({ prompt, onEnhanced }: PromptEnhancerProps) {
  const [enhancementMethod, setEnhancementMethod] = useState<'hybrid' | 'llm' | 'rule_based'>('hybrid')
  const [showDetails, setShowDetails] = useState(false)
  const [copied, setCopied] = useState(false)

  const {
    enhance,
    enhancedData,
    isEnhancing,
    error
  } = usePromptEnhancement()

  const handleEnhance = () => {
    enhance(prompt, 10, enhancementMethod)
  }

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleUseEnhanced = () => {
    if (enhancedData) {
      onEnhanced(enhancedData.enhanced_prompt, enhancedData.negative_prompt)
    }
  }

  const getMethodInfo = (method: string) => {
    const info = {
      hybrid: {
        icon: <Zap className="w-4 h-4" />,
        color: 'from-purple-500 to-pink-500',
        label: 'Hybrid',
        description: 'LLM + Validation (Best)'
      },
      llm: {
        icon: <Brain className="w-4 h-4" />,
        color: 'from-blue-500 to-cyan-500',
        label: 'LLM Only',
        description: 'Pure AI Enhancement'
      },
      rule_based: {
        icon: <Shield className="w-4 h-4" />,
        color: 'from-green-500 to-emerald-500',
        label: 'Rule-Based',
        description: 'Traditional (Fast)'
      }
    }
    return info[method as keyof typeof info]
  }

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'text-green-400'
    if (score >= 70) return 'text-yellow-400'
    return 'text-orange-400'
  }

  const getScoreLabel = (score: number) => {
    if (score >= 85) return 'Excellent'
    if (score >= 70) return 'Good'
    return 'Needs Work'
  }

  return (
    <div className="space-y-4">
      {/* Enhancement Controls */}
      <div className="glass rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Wand2 className="w-5 h-5 text-purple-400" />
            <h3 className="font-semibold">Enhance Your Prompt</h3>
          </div>

          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-1 text-sm text-zinc-400 hover:text-white transition-colors"
          >
            <Info className="w-4 h-4" />
            {showDetails ? 'Hide' : 'Show'} Details
            <ChevronDown className={`w-4 h-4 transition-transform ${showDetails ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {/* Method Selection */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          {(['hybrid', 'llm', 'rule_based'] as const).map((method) => {
            const info = getMethodInfo(method)
            return (
              <button
                key={method}
                onClick={() => setEnhancementMethod(method)}
                className={`relative p-3 rounded-xl border transition-all ${
                  enhancementMethod === method
                    ? 'border-white/30 bg-white/10'
                    : 'border-white/10 bg-white/5 hover:bg-white/10'
                }`}
              >
                <div className={`inline-flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br ${info.color} mb-2`}>
                  {info.icon}
                </div>
                <div className="text-sm font-medium mb-0.5">{info.label}</div>
                <div className="text-xs text-zinc-400">{info.description}</div>

                {enhancementMethod === method && (
                  <motion.div
                    layoutId="method-indicator"
                    className="absolute inset-0 border-2 border-purple-500 rounded-xl"
                    transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                  />
                )}
              </button>
            )
          })}
        </div>

        {/* Enhancement Info */}
        <AnimatePresence>
          {showDetails && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="pt-4 mb-4 border-t border-white/10">
                <div className="text-sm text-zinc-400 space-y-2">
                  {enhancementMethod === 'hybrid' && (
                    <>
                      <p className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                        <span>Uses AI for creative enhancement, then validates cultural accuracy</span>
                      </p>
                      <p className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                        <span>Best quality with safety checks for respectful cultural representation</span>
                      </p>
                      <p className="flex items-start gap-2">
                        <AlertCircle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                        <span>Requires API key, ~1-2s processing time</span>
                      </p>
                    </>
                  )}
                  {enhancementMethod === 'llm' && (
                    <>
                      <p className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                        <span>Pure AI enhancement with unlimited cultural coverage</span>
                      </p>
                      <p className="flex items-start gap-2">
                        <AlertCircle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                        <span>No validation - may miss some cultural details</span>
                      </p>
                    </>
                  )}
                  {enhancementMethod === 'rule_based' && (
                    <>
                      <p className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                        <span>Fast and free - no API key needed</span>
                      </p>
                      <p className="flex items-start gap-2">
                        <AlertCircle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                        <span>Limited to predefined cultural entities (Hindu, Greek, Norse mythology)</span>
                      </p>
                    </>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Enhance Button */}
        <button
          onClick={handleEnhance}
          disabled={!prompt.trim() || isEnhancing}
          className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl font-medium flex items-center justify-center gap-2 hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {isEnhancing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Enhancing...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              Enhance Prompt
            </>
          )}
        </button>
      </div>

      {/* Error Display */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-red-500/10 border border-red-500/20 rounded-2xl p-4"
          >
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-medium text-red-400 mb-1">Enhancement Failed</div>
                <div className="text-sm text-red-300/80">{error}</div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Enhanced Result */}
      <AnimatePresence>
        {enhancedData && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-4"
          >
            {/* Enhanced Prompt Display */}
            <div className="glass rounded-2xl p-5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-purple-400" />
                  <h4 className="font-semibold">Enhanced Prompt</h4>
                </div>
                <button
                  onClick={() => handleCopy(enhancedData.enhanced_prompt)}
                  className="p-2 text-zinc-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                  title="Copy to clipboard"
                >
                  {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>

              <div className="bg-white/5 rounded-xl p-4 mb-4">
                <p className="text-sm leading-relaxed text-zinc-300">
                  {enhancedData.enhanced_prompt}
                </p>
              </div>

              {enhancedData.negative_prompt && (
                <div className="mb-4">
                  <div className="text-xs font-medium text-zinc-400 mb-2">NEGATIVE PROMPT (What to avoid):</div>
                  <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                    <p className="text-xs text-red-300">{enhancedData.negative_prompt}</p>
                  </div>
                </div>
              )}

              <button
                onClick={handleUseEnhanced}
                className="w-full py-2.5 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-lg font-medium text-sm flex items-center justify-center gap-2 hover:from-indigo-600 hover:to-purple-600 transition-all"
              >
                <CheckCircle2 className="w-4 h-4" />
                Use This Enhanced Prompt
              </button>
            </div>

            {/* Aesthetic Scores */}
            {enhancedData.aesthetic_score && (
              <div className="glass rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-4">
                  <TrendingUp className="w-5 h-5 text-green-400" />
                  <h4 className="font-semibold">Quality Prediction</h4>
                  <div className={`ml-auto text-2xl font-bold ${getScoreColor(enhancedData.aesthetic_score.overall)}`}>
                    {enhancedData.aesthetic_score.overall.toFixed(0)}
                    <span className="text-sm text-zinc-400 font-normal ml-1">/ 100</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 mb-4">
                  {[
                    { label: 'Composition', value: enhancedData.aesthetic_score.composition, icon: <Camera className="w-3.5 h-3.5" /> },
                    { label: 'Clarity', value: enhancedData.aesthetic_score.clarity, icon: <Lightbulb className="w-3.5 h-3.5" /> },
                    { label: 'Creativity', value: enhancedData.aesthetic_score.creativity, icon: <Sparkles className="w-3.5 h-3.5" /> },
                    { label: 'Technical', value: enhancedData.aesthetic_score.technical, icon: <Palette className="w-3.5 h-3.5" /> },
                    { label: 'Cultural', value: enhancedData.aesthetic_score.cultural, icon: <Globe2 className="w-3.5 h-3.5" /> },
                    { label: 'Motion', value: enhancedData.aesthetic_score.motion, icon: <Zap className="w-3.5 h-3.5" /> },
                  ].map(({ label, value, icon }) => (
                    <div key={label} className="bg-white/5 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-1.5 text-xs text-zinc-400">
                          {icon}
                          <span>{label}</span>
                        </div>
                        <span className={`text-sm font-semibold ${getScoreColor(value)}`}>
                          {value.toFixed(0)}
                        </span>
                      </div>
                      <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${value}%` }}
                          transition={{ duration: 0.8, ease: 'easeOut' }}
                          className={`h-full rounded-full ${
                            value >= 85 ? 'bg-green-400' :
                            value >= 70 ? 'bg-yellow-400' :
                            'bg-orange-400'
                          }`}
                        />
                      </div>
                    </div>
                  ))}
                </div>

                <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${
                  enhancedData.aesthetic_score.overall >= 85 ? 'bg-green-500/20 text-green-400' :
                  enhancedData.aesthetic_score.overall >= 70 ? 'bg-yellow-500/20 text-yellow-400' :
                  'bg-orange-500/20 text-orange-400'
                }`}>
                  <CheckCircle2 className="w-4 h-4" />
                  {getScoreLabel(enhancedData.aesthetic_score.overall)}
                </div>
              </div>
            )}

            {/* Cultural Notes */}
            {enhancedData.cultural_notes && enhancedData.cultural_notes.length > 0 && (
              <div className="glass rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Globe2 className="w-5 h-5 text-blue-400" />
                  <h4 className="font-semibold">Cultural Context</h4>
                </div>
                <div className="space-y-2">
                  {enhancedData.cultural_notes.map((note, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-sm text-zinc-300">
                      <Info className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                      <span>{note}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Validation Warnings */}
            {enhancedData.validation && enhancedData.validation.warnings && enhancedData.validation.warnings.length > 0 && (
              <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <AlertCircle className="w-5 h-5 text-yellow-400" />
                  <h4 className="font-semibold text-yellow-400">Validation Warnings</h4>
                </div>
                <div className="space-y-2">
                  {enhancedData.validation.warnings.map((warning, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-sm text-yellow-300">
                      <span className="w-1 h-1 bg-yellow-400 rounded-full mt-2 flex-shrink-0" />
                      <span>{warning}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Detected Concepts */}
            {enhancedData.concepts_detected && enhancedData.concepts_detected.length > 0 && (
              <div className="glass rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Brain className="w-5 h-5 text-purple-400" />
                  <h4 className="font-semibold">Detected Concepts</h4>
                </div>
                <div className="flex flex-wrap gap-2">
                  {enhancedData.concepts_detected.map((concept, idx) => (
                    <div
                      key={idx}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white/10 rounded-full text-sm"
                    >
                      <span className="font-medium capitalize">{concept.type}</span>
                      <span className="text-zinc-400">•</span>
                      <span className="text-zinc-300">{concept.value}</span>
                      {concept.cultural_context && (
                        <>
                          <span className="text-zinc-400">•</span>
                          <span className="text-xs text-purple-400">{concept.cultural_context}</span>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Metadata */}
            {enhancedData.metadata && (
              <div className="glass rounded-2xl p-5">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="text-zinc-400 mb-1">Method</div>
                    <div className="font-medium capitalize">{enhancedData.method}</div>
                  </div>
                  <div>
                    <div className="text-zinc-400 mb-1">Processing Time</div>
                    <div className="font-medium">{enhancedData.metadata.processing_time_ms?.toFixed(0)}ms</div>
                  </div>
                  {enhancedData.metadata.model_used && (
                    <div>
                      <div className="text-zinc-400 mb-1">Model</div>
                      <div className="font-medium text-xs">{enhancedData.metadata.model_used.split('-')[0]}</div>
                    </div>
                  )}
                  {enhancedData.metadata.llm_confidence !== undefined && (
                    <div>
                      <div className="text-zinc-400 mb-1">Confidence</div>
                      <div className="font-medium">{(enhancedData.metadata.llm_confidence * 100).toFixed(0)}%</div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
