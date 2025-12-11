import { useState, useEffect } from 'react'
import { Radio, Wifi, WifiOff } from 'lucide-react'
import { useWebSocket } from '../hooks/useWebSocket'

const LiveIndicator = ({ onNewLead, onLeadUpdate, onHotLead }) => {
  const [recentActivity, setRecentActivity] = useState([])
  const [showPopup, setShowPopup] = useState(false)

  const { isConnected, lastMessage } = useWebSocket({
    onNewLead: (data) => {
      console.log('🆕 New lead detected:', data)
      addActivity('NEW_LEAD', data)
      onNewLead?.(data)
    },
    onLeadUpdate: (data) => {
      console.log('🔄 Lead updated:', data)
      addActivity('LEAD_UPDATE', data)
      onLeadUpdate?.(data)
    },
    onHotLead: (data) => {
      console.log('🔥 Hot lead alert:', data)
      addActivity('HOT_LEAD', data)
      setShowPopup(true)
      setTimeout(() => setShowPopup(false), 5000)
      onHotLead?.(data)
    }
  })

  const addActivity = (type, data) => {
    const activity = {
      id: Date.now(),
      type,
      data,
      timestamp: new Date()
    }

    setRecentActivity(prev => [activity, ...prev].slice(0, 10))
  }

  const getActivityIcon = (type) => {
    switch (type) {
      case 'NEW_LEAD':
        return '🆕'
      case 'LEAD_UPDATE':
        return '🔄'
      case 'HOT_LEAD':
        return '🔥'
      default:
        return '📌'
    }
  }

  const getActivityText = (activity) => {
    switch (activity.type) {
      case 'NEW_LEAD':
        return 'New QR scan detected'
      case 'LEAD_UPDATE':
        return `${activity.data.action_type} - Score: ${activity.data.lead_score}`
      case 'HOT_LEAD':
        return `Hot lead! Score: ${activity.data.lead_score}`
      default:
        return 'Activity'
    }
  }

  return (
    <>
      {/* Connection Status Badge */}
      <div className="fixed top-6 right-6 z-40 flex items-center gap-3">
        {/* Live Indicator */}
        <div className={`flex items-center gap-2 px-4 py-2 rounded-full backdrop-blur-md border transition-all ${
          isConnected
            ? 'bg-green-500/20 border-green-500/30 text-green-400'
            : 'bg-red-500/20 border-red-500/30 text-red-400'
        }`}>
          {isConnected ? (
            <>
              <div className="relative">
                <Radio className="w-4 h-4 animate-pulse" />
                <div className="absolute inset-0 animate-ping">
                  <Radio className="w-4 h-4 opacity-75" />
                </div>
              </div>
              <span className="text-sm font-semibold">🔴 LIVE</span>
            </>
          ) : (
            <>
              <WifiOff className="w-4 h-4" />
              <span className="text-sm font-semibold">Offline</span>
            </>
          )}
        </div>

        {/* Activity Counter */}
        {recentActivity.length > 0 && (
          <div className="bg-purple-500/20 border border-purple-500/30 text-purple-400 px-4 py-2 rounded-full backdrop-blur-md">
            <span className="text-sm font-semibold">
              ⚡ {recentActivity.length} recent
            </span>
          </div>
        )}
      </div>

      {/* Hot Lead Popup Notification */}
      {showPopup && lastMessage?.type === 'HOT_LEAD' && (
        <div className="fixed top-24 right-6 z-50 animate-slide-up">
          <div className="glass-card rounded-2xl p-6 border border-red-500/30 shadow-2xl max-w-sm bg-gradient-to-br from-red-500/20 to-orange-500/20">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center flex-shrink-0 animate-pulse">
                <span className="text-2xl">🔥</span>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-white mb-1">
                  Hot Lead Alert!
                </h3>
                <p className="text-sm text-white/80 mb-2">
                  Lead #{lastMessage.lead_id} just became hot
                </p>
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2 py-1 bg-red-500/30 rounded-full text-red-200 font-semibold">
                    Score: {lastMessage.lead_score}
                  </span>
                  <span className="text-xs px-2 py-1 bg-orange-500/30 rounded-full text-orange-200 font-semibold">
                    {lastMessage.temperature}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setShowPopup(false)}
                className="text-white/60 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Recent Activity Feed (Optional - Expandable) */}
      {recentActivity.length > 0 && (
        <div className="fixed bottom-24 right-6 z-40 w-80 glass-card rounded-xl p-4 border border-white/10 max-h-96 overflow-y-auto">
          <h4 className="font-semibold text-white mb-3 flex items-center gap-2">
            <Wifi className="w-4 h-4 text-green-400" />
            Live Activity Feed
          </h4>
          <div className="space-y-2">
            {recentActivity.map((activity) => (
              <div
                key={activity.id}
                className="flex items-start gap-3 p-2 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
              >
                <span className="text-xl">{getActivityIcon(activity.type)}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white/90 truncate">
                    {getActivityText(activity)}
                  </p>
                  <p className="text-xs text-white/50">
                    {activity.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}

export default LiveIndicator
