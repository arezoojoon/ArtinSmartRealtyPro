import { useState, useEffect } from 'react'
import { Trophy, TrendingUp, Users, DollarSign, Target, Award, Medal } from 'lucide-react'
import { api } from '../context/AuthContext'

const AgentLeaderboard = () => {
  const [leaderboard, setLeaderboard] = useState([])
  const [loading, setLoading] = useState(true)
  const [timeframe, setTimeframe] = useState('today') // today, week, month

  useEffect(() => {
    fetchLeaderboard()
    
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchLeaderboard, 300000)
    return () => clearInterval(interval)
  }, [timeframe])

  const fetchLeaderboard = async () => {
    try {
      setLoading(true)
      const response = await api.get(`/api/analytics/leaderboard?timeframe=${timeframe}`)
      setLeaderboard(response.data.agents || [])
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error)
    } finally {
      setLoading(false)
    }
  }

  const getMedalIcon = (rank) => {
    if (rank === 1) return <Trophy className="w-6 h-6 text-yellow-500" />
    if (rank === 2) return <Medal className="w-6 h-6 text-gray-400" />
    if (rank === 3) return <Medal className="w-6 h-6 text-amber-600" />
    return <Award className="w-5 h-5 text-gray-500" />
  }

  const getRankClass = (rank) => {
    if (rank === 1) return 'bg-gradient-to-r from-yellow-500/20 to-amber-500/20 border-yellow-500/30'
    if (rank === 2) return 'bg-gradient-to-r from-gray-400/20 to-gray-500/20 border-gray-400/30'
    if (rank === 3) return 'bg-gradient-to-r from-amber-600/20 to-orange-600/20 border-amber-600/30'
    return 'bg-white/5 border-white/10'
  }

  return (
    <div className="glass-card rounded-2xl p-6 border border-white/10">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-yellow-500 to-amber-600 flex items-center justify-center">
            <Trophy className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">🏆 Top Performers</h2>
            <p className="text-sm text-white/60">Team leaderboard - {timeframe}</p>
          </div>
        </div>

        {/* Timeframe Selector */}
        <div className="flex gap-2 bg-white/5 rounded-lg p-1">
          {['today', 'week', 'month'].map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                timeframe === tf
                  ? 'bg-gold-500 text-white shadow-lg'
                  : 'text-white/60 hover:text-white hover:bg-white/10'
              }`}
            >
              {tf.charAt(0).toUpperCase() + tf.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="w-8 h-8 border-4 border-gold-500/30 border-t-gold-500 rounded-full animate-spin"></div>
        </div>
      ) : leaderboard.length === 0 ? (
        <div className="text-center py-12">
          <Users className="w-16 h-16 mx-auto text-white/20 mb-3" />
          <p className="text-white/40">No data available yet</p>
        </div>
      ) : (
        <div className="space-y-3">
          {leaderboard.map((agent, index) => (
            <div
              key={agent.id}
              className={`flex items-center gap-4 p-4 rounded-xl border transition-all hover:scale-[1.02] ${getRankClass(index + 1)}`}
            >
              {/* Rank & Medal */}
              <div className="flex items-center gap-3 w-16">
                <span className="text-2xl font-bold text-white/40">#{index + 1}</span>
                {getMedalIcon(index + 1)}
              </div>

              {/* Agent Info */}
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <img
                    src={agent.avatar_url || `https://ui-avatars.com/api/?name=${agent.full_name}&background=random`}
                    alt={agent.full_name}
                    className="w-10 h-10 rounded-full border-2 border-white/20"
                  />
                  <div>
                    <h3 className="font-semibold text-white">{agent.full_name}</h3>
                    <p className="text-xs text-white/50">{agent.role}</p>
                  </div>
                </div>
              </div>

              {/* Stats */}
              <div className="flex items-center gap-6">
                {/* Leads */}
                <div className="text-center">
                  <div className="flex items-center gap-1 text-white mb-1">
                    <Users className="w-4 h-4" />
                    <span className="text-lg font-bold">{agent.leads_count || 0}</span>
                  </div>
                  <p className="text-xs text-white/50">Leads</p>
                </div>

                {/* Conversions */}
                <div className="text-center">
                  <div className="flex items-center gap-1 text-green-400 mb-1">
                    <Target className="w-4 h-4" />
                    <span className="text-lg font-bold">{agent.conversions || 0}</span>
                  </div>
                  <p className="text-xs text-white/50">Converted</p>
                </div>

                {/* Revenue */}
                <div className="text-center">
                  <div className="flex items-center gap-1 text-gold-500 mb-1">
                    <DollarSign className="w-4 h-4" />
                    <span className="text-lg font-bold">
                      ${(agent.revenue || 0).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-xs text-white/50">Revenue</p>
                </div>

                {/* Conversion Rate */}
                <div className="text-center">
                  <div className="flex items-center gap-1 text-purple-400 mb-1">
                    <TrendingUp className="w-4 h-4" />
                    <span className="text-lg font-bold">
                      {agent.conversion_rate || 0}%
                    </span>
                  </div>
                  <p className="text-xs text-white/50">Rate</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="mt-6 pt-4 border-t border-white/10 text-center">
        <p className="text-xs text-white/40">
          🔄 Auto-updates every 5 minutes
        </p>
      </div>
    </div>
  )
}

export default AgentLeaderboard
