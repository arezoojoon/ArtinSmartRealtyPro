import { useState, useEffect } from 'react'
import { X, Flame, Minimize2, Maximize2, Phone, Mail, MessageCircle } from 'lucide-react'
import { api } from '../context/AuthContext'

const FloatingHotLeads = () => {
  const [isOpen, setIsOpen] = useState(true)
  const [isMinimized, setIsMinimized] = useState(false)
  const [hotLeads, setHotLeads] = useState([])
  const [loading, setLoading] = useState(false)
  const [lastCount, setLastCount] = useState(0)
  const [notificationPermission, setNotificationPermission] = useState('default')

  // Request notification permission on mount
  useEffect(() => {
    if ('Notification' in window) {
      setNotificationPermission(Notification.permission)
      
      if (Notification.permission === 'default') {
        // Auto-request permission after 3 seconds
        setTimeout(() => {
          Notification.requestPermission().then(permission => {
            setNotificationPermission(permission)
            if (permission === 'granted') {
              new Notification('✅ Notifications Enabled!', {
                icon: '/logo.png',
                body: 'You\'ll be notified when hot leads arrive'
              })
            }
          })
        }, 3000)
      }
    }
  }, [])

  useEffect(() => {
    fetchHotLeads()
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchHotLeads, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchHotLeads = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/leads/hot?min_score=50&limit=10')
      const leads = response.data.hot_leads || []
      
      // Show notification if new hot lead
      if (leads.length > lastCount && lastCount > 0) {
        const newLead = leads[0]
        showNotification(
          '🔥 New Hot Lead!',
          `${newLead.full_name} - Score: ${newLead.lead_score}`
        )
      }
      
      setHotLeads(leads)
      setLastCount(leads.length)
    } catch (error) {
      console.error('Failed to fetch hot leads:', error)
    } finally {
      setLoading(false)
    }
  }

  const showNotification = (title, body) => {
    if ('Notification' in window && Notification.permission === 'granted') {
      const notification = new Notification(title, {
        icon: '/logo.png',
        body: body,
        badge: '/logo.png',
        tag: 'hot-lead',
        requireInteraction: true,
        vibrate: [200, 100, 200]
      })

      // Auto-close after 10 seconds
      setTimeout(() => notification.close(), 10000)

      // Click to focus window
      notification.onclick = () => {
        window.focus()
        notification.close()
      }
    }
  }

  const requestNotificationPermission = async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission()
      setNotificationPermission(permission)
      
      if (permission === 'granted') {
        showNotification('✅ Notifications Enabled!', 'You\'ll be alerted about hot leads')
      }
    }
  }

  const getTemperatureColor = (temperature) => {
    const colors = {
      burning: 'from-red-500 to-orange-500',
      hot: 'from-orange-500 to-yellow-500',
      warm: 'from-yellow-500 to-green-500',
    }
    return colors[temperature] || 'from-blue-500 to-cyan-500'
  }

  const getTemperatureEmoji = (temperature) => {
    const emojis = {
      burning: '🔥',
      hot: '🌶️',
      warm: '☀️',
    }
    return emojis[temperature] || '❄️'
  }

  if (!isOpen) return null

  if (isMinimized) {
    return (
      <div className="fixed bottom-4 right-4 left-4 sm:left-auto sm:right-6 sm:bottom-6 z-50 animate-slide-up">
        <button
          onClick={() => setIsMinimized(false)}
          className="group relative bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white px-4 py-3 sm:px-6 sm:py-4 rounded-xl sm:rounded-2xl shadow-2xl transition-all hover:scale-105 flex items-center gap-2 sm:gap-3 w-full sm:w-auto justify-center touch-manipulation"
        >
          <Flame className="w-6 h-6 animate-pulse" />
          <div className="text-left">
            <div className="text-sm font-bold">Hot Leads</div>
            <div className="text-xs opacity-90">{hotLeads.length} burning now!</div>
          </div>
          {hotLeads.length > 0 && (
            <div className="absolute -top-2 -right-2 bg-white text-red-500 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shadow-lg animate-bounce">
              {hotLeads.length}
            </div>
          )}
        </button>
      </div>
    )
  }

  return (
    <div className="fixed bottom-16 right-4 left-4 sm:left-auto sm:right-6 sm:bottom-6 z-50 w-auto sm:w-96 max-h-[60vh] sm:max-h-none animate-slide-up">
      <div className="glass-card rounded-xl sm:rounded-2xl shadow-2xl overflow-hidden border border-white/10">
        {/* Header */}
        <div className="bg-gradient-to-r from-red-500/20 to-orange-500/20 border-b border-white/10 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center">
                <Flame className="w-5 h-5 text-white animate-pulse" />
              </div>
              <div>
                <h3 className="font-bold text-white flex items-center gap-2">
                  🔥 Hot Leads
                  {loading && (
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  )}
                </h3>
                <p className="text-xs text-white/60">
                  {hotLeads.length} leads need attention now
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              {/* Notification Permission Button */}
              {notificationPermission !== 'granted' && (
                <button
                  onClick={requestNotificationPermission}
                  className="p-2 hover:bg-white/10 rounded-lg transition-colors group"
                  title="Enable notifications"
                >
                  <span className="text-lg group-hover:animate-pulse">🔔</span>
                </button>
              )}
              <button
                onClick={() => setIsMinimized(true)}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                title="Minimize"
              >
                <Minimize2 className="w-4 h-4 text-white/60" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                title="Close"
              >
                <X className="w-4 h-4 text-white/60" />
              </button>
            </div>
          </div>
        </div>

        {/* Hot Leads List */}
        <div className="max-h-[500px] overflow-y-auto p-4 space-y-3">
          {hotLeads.length === 0 ? (
            <div className="text-center py-8">
              <div className="w-16 h-16 mx-auto mb-3 rounded-full bg-white/5 flex items-center justify-center">
                <Flame className="w-8 h-8 text-white/30" />
              </div>
              <p className="text-white/40 text-sm">No hot leads right now</p>
              <p className="text-white/30 text-xs mt-1">Keep scanning QR codes!</p>
            </div>
          ) : (
            hotLeads.map((lead) => (
              <div
                key={lead.id}
                className="group relative bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl p-4 transition-all hover:scale-[1.02] cursor-pointer"
              >
                {/* Temperature Badge */}
                <div className={`absolute -top-2 -right-2 px-3 py-1 rounded-full bg-gradient-to-r ${getTemperatureColor(lead.temperature)} text-white text-xs font-bold shadow-lg flex items-center gap-1`}>
                  <span>{getTemperatureEmoji(lead.temperature)}</span>
                  <span>{lead.lead_score}</span>
                </div>

                {/* Lead Info */}
                <div className="mb-3">
                  <h4 className="font-semibold text-white mb-1 pr-16">
                    {lead.full_name}
                  </h4>
                  {lead.company_name && (
                    <p className="text-xs text-white/50">🏢 {lead.company_name}</p>
                  )}
                  {lead.product_interest && (
                    <p className="text-xs text-white/50">🎯 {lead.product_interest}</p>
                  )}
                </div>

                {/* Contact Info */}
                <div className="space-y-1.5 mb-3">
                  {lead.phone && (
                    <div className="flex items-center gap-2 text-xs">
                      <Phone className="w-3 h-3 text-gold-500" />
                      <a href={`tel:${lead.phone}`} className="text-white/70 hover:text-gold-500 transition-colors">
                        {lead.phone}
                      </a>
                    </div>
                  )}
                  {lead.email && (
                    <div className="flex items-center gap-2 text-xs">
                      <Mail className="w-3 h-3 text-gold-500" />
                      <a href={`mailto:${lead.email}`} className="text-white/70 hover:text-gold-500 transition-colors">
                        {lead.email}
                      </a>
                    </div>
                  )}
                </div>

                {/* Activity Stats */}
                {lead.total_interactions > 0 && (
                  <div className="flex items-center gap-3 pt-3 border-t border-white/5 text-xs text-white/50">
                    {lead.qr_scan_count > 0 && (
                      <span>📱 {lead.qr_scan_count}</span>
                    )}
                    {lead.catalog_views > 0 && (
                      <span>📄 {lead.catalog_views}</span>
                    )}
                    {lead.messages_count > 0 && (
                      <span>💬 {lead.messages_count}</span>
                    )}
                  </div>
                )}

                {/* Last Action */}
                {lead.last_action_at && (
                  <div className="mt-2 text-xs text-white/40">
                    ⏱️ {getTimeAgo(lead.last_action_at)}
                  </div>
                )}

                {/* Quick Actions */}
                <div className="mt-3 pt-3 border-t border-white/5 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  {lead.phone && (
                    <a
                      href={`tel:${lead.phone}`}
                      className="flex-1 px-3 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-1"
                    >
                      <Phone className="w-3 h-3" />
                      Call
                    </a>
                  )}
                  {lead.phone && (
                    <a
                      href={`https://wa.me/${lead.phone.replace(/\D/g, '')}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 px-3 py-2 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-1"
                    >
                      <MessageCircle className="w-3 h-3" />
                      WhatsApp
                    </a>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-white/10 p-3 bg-white/5">
          <div className="flex items-center justify-between text-xs">
            <button
              onClick={fetchHotLeads}
              disabled={loading}
              className="text-gold-500 hover:text-gold-400 transition-colors disabled:opacity-50"
            >
              🔄 Refresh
            </button>
            <span className="text-white/40">
              Auto-updates every 30s
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

// Helper function for time ago
const getTimeAgo = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffInSeconds = Math.floor((now - date) / 1000)

  if (diffInSeconds < 60) return 'Just now'
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
  return `${Math.floor(diffInSeconds / 86400)}d ago`
}

export default FloatingHotLeads
