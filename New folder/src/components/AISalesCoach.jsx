import { useState } from 'react'
import { Sparkles, TrendingUp, MessageSquare, Target, Lightbulb, Loader } from 'lucide-react'
import { api } from '../context/AuthContext'

const AISalesCoach = ({ leadId, leadData }) => {
  const [advice, setAdvice] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchAdvice = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get(`/api/leads/${leadId}/advice`)
      setAdvice(response.data.advice)
    } catch (err) {
      console.error('Failed to fetch AI advice:', err)
      
      // Handle rate limiting
      if (err.response?.status === 429) {
        setError('🕐 Rate limit reached. You can request AI advice 5 times per minute and 30 times per hour. Please wait a moment and try again.')
      } else {
        setError('Failed to load AI suggestions. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  if (!advice && !loading && !error) {
    return (
      <button
        onClick={fetchAdvice}
        className="w-full mt-4 bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 text-white px-6 py-3 rounded-lg font-medium flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-xl"
      >
        <Sparkles className="w-5 h-5" />
        🤖 Get AI Sales Advice
      </button>
    )
  }

  if (loading) {
    return (
      <div className="mt-4 bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 rounded-xl p-6 border border-purple-200 dark:border-purple-800">
        <div className="flex items-center justify-center gap-3 text-purple-600 dark:text-purple-400">
          <Loader className="w-5 h-5 animate-spin" />
          <span className="font-medium">AI analyzing lead behavior...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="mt-4 bg-red-50 dark:bg-red-900/20 rounded-xl p-4 border border-red-200 dark:border-red-800">
        <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
        <button
          onClick={fetchAdvice}
          className="mt-2 text-red-600 dark:text-red-400 text-sm font-medium hover:underline"
        >
          Try again
        </button>
      </div>
    )
  }

  return (
    <div className="mt-4 bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 rounded-xl p-6 border border-purple-200 dark:border-purple-800 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-500 flex items-center justify-center">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="font-bold text-gray-900 dark:text-white flex items-center gap-2">
            🤖 AI Sales Coach
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Personalized strategy for this lead
          </p>
        </div>
      </div>

      {/* Approach Strategy */}
      <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Target className="w-5 h-5 text-purple-600 dark:text-purple-400 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="font-semibold text-gray-900 dark:text-white text-sm mb-1">
              📋 Approach Strategy
            </h4>
            <p className="text-gray-700 dark:text-gray-300 text-sm">
              {advice.approach}
            </p>
          </div>
        </div>
      </div>

      {/* Talking Points */}
      <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <MessageSquare className="w-5 h-5 text-indigo-600 dark:text-indigo-400 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <h4 className="font-semibold text-gray-900 dark:text-white text-sm mb-2">
              💬 Key Talking Points
            </h4>
            <div className="text-gray-700 dark:text-gray-300 text-sm whitespace-pre-line">
              {advice.talking_points}
            </div>
          </div>
        </div>
      </div>

      {/* Next Action */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
        <div className="flex items-start gap-3">
          <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="font-semibold text-gray-900 dark:text-white text-sm mb-1">
              ⚡ Recommended Next Action
            </h4>
            <p className="text-gray-700 dark:text-gray-300 text-sm font-medium">
              {advice.next_action}
            </p>
          </div>
        </div>
      </div>

      {/* Psychology Tip */}
      <div className="bg-gradient-to-r from-amber-50 to-yellow-50 dark:from-amber-900/20 dark:to-yellow-900/20 rounded-lg p-4 border border-amber-200 dark:border-amber-800">
        <div className="flex items-start gap-3">
          <Lightbulb className="w-5 h-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="font-semibold text-gray-900 dark:text-white text-sm mb-1">
              💡 Sales Psychology Insight
            </h4>
            <p className="text-gray-700 dark:text-gray-300 text-sm">
              {advice.psychology_tip}
            </p>
          </div>
        </div>
      </div>

      {/* Refresh Button */}
      <button
        onClick={fetchAdvice}
        className="w-full mt-2 text-purple-600 dark:text-purple-400 text-sm font-medium hover:underline flex items-center justify-center gap-2"
      >
        <Sparkles className="w-4 h-4" />
        Refresh AI Advice
      </button>
    </div>
  )
}

export default AISalesCoach
