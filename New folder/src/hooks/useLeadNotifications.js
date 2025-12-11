import { useEffect } from 'react'
import { useNotifications } from '../context/NotificationContext'
import { useWebSocket } from './useWebSocket'
import { useAuth } from '../context/AuthContext'

export const useLeadNotifications = () => {
  const { addNotification } = useNotifications()
  const { user } = useAuth()
  const { lastMessage } = useWebSocket()

  useEffect(() => {
    if (!lastMessage) return

    try {
      const data = JSON.parse(lastMessage)

      // Handle different event types
      switch (data.type) {
        case 'new_lead':
          addNotification({
            type: 'new_lead',
            title: 'New Visitor!',
            message: `${data.lead_name || 'Someone'} just scanned QR code`,
            onClick: () => {
              window.location.href = '/leads'
            }
          })
          break

        case 'hot_lead':
          addNotification({
            type: 'hot_lead',
            title: '🔥 Hot Lead Alert!',
            message: `${data.lead_name} has score ${data.score}/100 - Follow up NOW!`,
            onClick: () => {
              window.location.href = '/leads'
            }
          })
          break

        case 'telegram_message':
          addNotification({
            type: 'message',
            title: '💬 New Message',
            message: `${data.lead_name}: ${data.message_preview || 'Sent a message'}`,
            onClick: () => {
              window.location.href = '/leads'
            }
          })
          break

        case 'qr_scan':
          addNotification({
            type: 'qr_scan',
            title: 'QR Code Scanned',
            message: `${data.lead_name || 'Visitor'} scanned ${data.catalog_name || 'catalog'}`,
            onClick: () => {
              window.location.href = '/analytics'
            }
          })
          break

        case 'catalog_view':
          addNotification({
            type: 'catalog_view',
            title: 'Catalog Viewed',
            message: `${data.lead_name} is viewing ${data.catalog_name}`,
            onClick: () => {
              window.location.href = '/catalogs'
            }
          })
          break

        case 'follow_up_reminder':
          addNotification({
            type: 'follow_up',
            title: '📞 Follow-up Reminder',
            message: `Time to follow up with ${data.lead_name}`,
            onClick: () => {
              window.location.href = '/leads'
            }
          })
          break

        case 'conversion':
          addNotification({
            type: 'conversion',
            title: '🎉 Conversion!',
            message: `${data.lead_name} marked as converted! Great job!`,
            onClick: () => {
              window.location.href = '/analytics'
            }
          })
          break

        default:
          // Generic notification
          if (data.notification) {
            addNotification({
              type: 'system',
              title: data.notification.title || 'Notification',
              message: data.notification.message || 'New activity',
              onClick: data.notification.url ? () => {
                window.location.href = data.notification.url
              } : undefined
            })
          }
          break
      }
    } catch (error) {
      console.error('Failed to parse WebSocket notification:', error)
    }
  }, [lastMessage, addNotification])

  return null
}
