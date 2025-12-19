import { useState, useEffect, useRef } from 'react'
import { Bell, X, Check, Volume2, VolumeX, Trash2 } from 'lucide-react'
import { useNotifications } from '../context/NotificationContext'
import { useLanguage } from '../context/LanguageContext'
import { formatDistanceToNow } from 'date-fns'

const NotificationPanel = () => {
  const { notifications, unreadCount, soundEnabled, setSoundEnabled, markAsRead, markAllAsRead, clearNotification, clearAll } = useNotifications()
  const { t } = useLanguage()
  const [isOpen, setIsOpen] = useState(false)
  const panelRef = useRef(null)

  // Close panel when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (panelRef.current && !panelRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  const getNotificationIcon = (type) => {
    const icons = {
      'new_lead': '🆕',
      'hot_lead': '🔥',
      'message': '💬',
      'qr_scan': '📱',
      'catalog_view': '📄',
      'follow_up': '📞',
      'conversion': '🎉',
      'system': 'ℹ️'
    }
    return icons[type] || '📢'
  }

  const getNotificationColor = (type) => {
    const colors = {
      'new_lead': 'border-blue-500/30 bg-blue-500/5',
      'hot_lead': 'border-red-500/30 bg-red-500/5',
      'message': 'border-purple-500/30 bg-purple-500/5',
      'qr_scan': 'border-green-500/30 bg-green-500/5',
      'catalog_view': 'border-yellow-500/30 bg-yellow-500/5',
      'follow_up': 'border-orange-500/30 bg-orange-500/5',
      'conversion': 'border-gold-500/30 bg-gold-500/5',
      'system': 'border-white/10 bg-white/5'
    }
    return colors[type] || 'border-white/10 bg-white/5'
  }

  return (
    <div className="relative" ref={panelRef}>
      {/* Notification Bell Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative text-gray-400 hover:text-gold-500 transition-colors p-2 hover:bg-white/5 rounded-xl"
      >
        <Bell className="w-5 h-5 md:w-6 md:h-6" />
        {unreadCount > 0 && (
          <>
            <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-gold-500 rounded-full animate-pulse-slow"></span>
            <span className="absolute -top-1 -right-1 min-w-[20px] h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center px-1">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          </>
        )}
      </button>

      {/* Notification Panel */}
      {isOpen && (
        <div className="absolute top-full right-0 mt-2 w-96 max-w-[calc(100vw-2rem)] bg-navy-800 border border-white/10 rounded-xl shadow-2xl z-50 max-h-[600px] flex flex-col">
          {/* Header */}
          <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bell className="w-5 h-5 text-gold-500" />
              <h3 className="font-semibold text-white">Notifications</h3>
              {unreadCount > 0 && (
                <span className="px-2 py-0.5 bg-gold-500/20 text-gold-400 text-xs font-bold rounded-full">
                  {unreadCount}
                </span>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              {/* Sound Toggle */}
              <button
                onClick={() => setSoundEnabled(!soundEnabled)}
                className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
                title={soundEnabled ? 'Mute notifications' : 'Unmute notifications'}
              >
                {soundEnabled ? (
                  <Volume2 className="w-4 h-4 text-white/70" />
                ) : (
                  <VolumeX className="w-4 h-4 text-white/40" />
                )}
              </button>

              {/* Mark All Read */}
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
                  title="Mark all as read"
                >
                  <Check className="w-4 h-4 text-white/70" />
                </button>
              )}

              {/* Clear All */}
              {notifications.length > 0 && (
                <button
                  onClick={clearAll}
                  className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
                  title="Clear all"
                >
                  <Trash2 className="w-4 h-4 text-white/70" />
                </button>
              )}

              {/* Close */}
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
              >
                <X className="w-4 h-4 text-white/70" />
              </button>
            </div>
          </div>

          {/* Notifications List */}
          <div className="overflow-y-auto flex-1">
            {notifications.length === 0 ? (
              <div className="py-12 px-4 text-center">
                <Bell className="w-12 h-12 text-white/20 mx-auto mb-3" />
                <p className="text-white/40">No notifications yet</p>
                <p className="text-white/30 text-sm mt-1">
                  You'll be notified when leads interact
                </p>
              </div>
            ) : (
              <div className="divide-y divide-white/5">
                {notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={`px-4 py-3 hover:bg-white/5 transition-colors cursor-pointer ${
                      !notification.read ? 'bg-white/5 border-l-2 border-gold-500' : ''
                    }`}
                    onClick={() => {
                      if (!notification.read) markAsRead(notification.id)
                      if (notification.onClick) notification.onClick()
                    }}
                  >
                    <div className="flex gap-3">
                      {/* Icon */}
                      <div className={`flex-shrink-0 w-10 h-10 rounded-lg ${getNotificationColor(notification.type)} border flex items-center justify-center text-xl`}>
                        {getNotificationIcon(notification.type)}
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <h4 className="font-medium text-white text-sm">
                            {notification.title}
                          </h4>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              clearNotification(notification.id)
                            }}
                            className="flex-shrink-0 p-1 hover:bg-white/10 rounded transition-colors"
                          >
                            <X className="w-3 h-3 text-white/40" />
                          </button>
                        </div>
                        
                        <p className="text-white/70 text-sm mt-0.5 line-clamp-2">
                          {notification.message}
                        </p>

                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-white/40 text-xs">
                            {formatDistanceToNow(new Date(notification.timestamp), { addSuffix: true })}
                          </span>
                          {!notification.read && (
                            <span className="w-2 h-2 bg-gold-500 rounded-full"></span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default NotificationPanel
