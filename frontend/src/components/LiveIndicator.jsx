/**
 * Live Connection Indicator
 * Shows real-time connection status with backend/WebSocket
 */

import React, { useState, useEffect } from 'react';
import { Wifi, WifiOff } from 'lucide-react';

const LiveIndicator = ({ wsConnected = false }) => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [lastPing, setLastPing] = useState(Date.now());

  useEffect(() => {
    // Monitor browser online/offline status
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Ping check every 10 seconds
    const pingInterval = setInterval(() => {
      setLastPing(Date.now());
    }, 10000);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(pingInterval);
    };
  }, []);

  const isConnected = isOnline && wsConnected;

  return (
    <div className="fixed top-4 right-4 z-50 glass-card rounded-full px-4 py-2 flex items-center gap-2 border border-white/10">
      {/* Status Indicator */}
      <div className="relative">
        <div className={`w-3 h-3 rounded-full ${
          isConnected ? 'bg-green-500' : 'bg-red-500'
        }`}>
          {isConnected && (
            <div className="absolute inset-0 w-3 h-3 rounded-full bg-green-500 animate-ping"></div>
          )}
        </div>
      </div>

      {/* Status Text */}
      <span className={`text-xs font-semibold ${
        isConnected ? 'text-green-400' : 'text-red-400'
      }`}>
        {isConnected ? '● LIVE' : '● OFFLINE'}
      </span>

      {/* Icon */}
      {isConnected ? (
        <Wifi size={16} className="text-green-400" />
      ) : (
        <WifiOff size={16} className="text-red-400" />
      )}
    </div>
  );
};

export default LiveIndicator;
