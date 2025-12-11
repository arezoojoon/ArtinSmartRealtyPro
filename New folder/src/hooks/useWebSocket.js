import { useEffect, useCallback, useRef, useState } from 'react'
import { useAuth } from '../context/AuthContext'

/**
 * Custom Hook for WebSocket Real-time Updates
 * 
 * Usage:
 * const { isConnected, lastMessage } = useWebSocket({
 *   onNewLead: (data) => console.log('New lead!', data),
 *   onLeadUpdate: (data) => console.log('Lead updated!', data),
 *   onHotLead: (data) => console.log('Hot lead!', data)
 * })
 */

export const useWebSocket = (callbacks = {}) => {
  const { user } = useAuth()
  const ws = useRef(null)
  const reconnectTimeout = useRef(null)
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState(null)

  const connect = useCallback(() => {
    if (!user?.tenant_id) return

    // Get JWT token from localStorage
    const token = localStorage.getItem('token')
    if (!token) {
      console.error('❌ No auth token available for WebSocket')
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/${user.tenant_id}?token=${token}`

    try {
      ws.current = new WebSocket(wsUrl)

      ws.current.onopen = () => {
        console.log('🔴 WebSocket connected')
        setIsConnected(true)

        // Send ping every 30 seconds to keep connection alive
        const pingInterval = setInterval(() => {
          if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send('ping')
          }
        }, 30000)

        ws.current.pingInterval = pingInterval
      }

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setLastMessage(data)

          // Route to specific callbacks
          switch (data.type) {
            case 'NEW_LEAD':
              callbacks.onNewLead?.(data)
              break
            case 'LEAD_UPDATE':
              callbacks.onLeadUpdate?.(data)
              break
            case 'HOT_LEAD':
              callbacks.onHotLead?.(data)
              break
            default:
              console.log('Unknown WebSocket message type:', data.type)
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error)
      }

      ws.current.onclose = () => {
        console.log('🔴 WebSocket disconnected')
        setIsConnected(false)

        // Clear ping interval
        if (ws.current?.pingInterval) {
          clearInterval(ws.current.pingInterval)
        }

        // Attempt reconnection after 5 seconds
        reconnectTimeout.current = setTimeout(() => {
          console.log('🔄 Attempting to reconnect WebSocket...')
          connect()
        }, 5000)
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
    }
  }, [user?.tenant_id, callbacks])

  useEffect(() => {
    connect()

    // Cleanup on unmount
    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current)
      }
      if (ws.current) {
        if (ws.current.pingInterval) {
          clearInterval(ws.current.pingInterval)
        }
        ws.current.close()
      }
    }
  }, [connect])

  return {
    isConnected,
    lastMessage,
    reconnect: connect
  }
}

export default useWebSocket
