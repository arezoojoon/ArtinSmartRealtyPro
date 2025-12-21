/**
 * Artin Smart Realty - Real-Time Notification System
 * Toast notifications with money sound for new leads
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
    X,
    DollarSign,
    Users,
    Building2,
    Calendar,
    CheckCircle,
    AlertTriangle,
} from 'lucide-react';

// Audio context for notification sounds
let audioContext = null;

const playMoneySound = () => {
    try {
        // Try to play the cha-ching sound
        const audio = new Audio('/sounds/cha-ching.mp3');
        audio.volume = 0.5;
        audio.play().catch(() => {
            // Fallback: Create a simple beep sound if file not found
            if (!audioContext) {
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);

            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        });
    } catch (e) {
        console.log('Audio not available');
    }
};

const NotificationToast = ({ notification, onDismiss }) => {
    const [isExiting, setIsExiting] = useState(false);

    const getIcon = () => {
        switch (notification.type) {
            case 'new_lead':
                return <Users className="w-6 h-6 text-gold-400" />;
            case 'deal_closed':
                return <DollarSign className="w-6 h-6 text-green-400" />;
            case 'appointment':
                return <Calendar className="w-6 h-6 text-blue-400" />;
            case 'property':
                return <Building2 className="w-6 h-6 text-purple-400" />;
            case 'success':
                return <CheckCircle className="w-6 h-6 text-green-400" />;
            case 'warning':
                return <AlertTriangle className="w-6 h-6 text-yellow-400" />;
            default:
                return <Users className="w-6 h-6 text-gold-400" />;
        }
    };

    const handleDismiss = () => {
        setIsExiting(true);
        setTimeout(() => onDismiss(notification.id), 300);
    };

    useEffect(() => {
        // Auto dismiss after 5 seconds
        const timer = setTimeout(handleDismiss, 5000);
        return () => clearTimeout(timer);
    }, []);

    return (
        <div
            className={`new-lead-toast ${isExiting ? 'animate-fade-out' : 'animate-bounce-in'}`}
            style={{
                animation: isExiting ? 'fadeOut 0.3s ease-out forwards' : undefined,
            }}
        >
            <div className="w-12 h-12 rounded-xl bg-navy-700 flex items-center justify-center flex-shrink-0">
                {getIcon()}
            </div>
            <div className="flex-1 min-w-0">
                <p className="font-semibold text-white">{notification.title}</p>
                <p className="text-sm text-gray-400 truncate">{notification.message}</p>
            </div>
            <button
                onClick={handleDismiss}
                className="p-2 text-gray-400 hover:text-white transition-colors"
            >
                <X className="w-4 h-4" />
            </button>
        </div>
    );
};

// Notification Provider Component
const RealTimeNotifications = ({ children }) => {
    const [notifications, setNotifications] = useState([]);

    // Function to add a notification
    const addNotification = useCallback((notification) => {
        const id = Date.now();
        const newNotification = { ...notification, id };

        setNotifications(prev => [...prev, newNotification]);

        // Play sound for new leads and deals
        if (notification.type === 'new_lead' || notification.type === 'deal_closed') {
            playMoneySound();
        }
    }, []);

    // Function to remove a notification
    const removeNotification = useCallback((id) => {
        setNotifications(prev => prev.filter(n => n.id !== id));
    }, []);

    // Expose the addNotification function globally for WebSocket events
    useEffect(() => {
        window.showNotification = addNotification;
        return () => {
            delete window.showNotification;
        };
    }, [addNotification]);

    return (
        <>
            {children}

            {/* Notification Container */}
            <div className="fixed bottom-6 right-6 z-50 space-y-3">
                {notifications.map((notification) => (
                    <NotificationToast
                        key={notification.id}
                        notification={notification}
                        onDismiss={removeNotification}
                    />
                ))}
            </div>
        </>
    );
};

// Hook to use notifications
export const useNotification = () => {
    const showNotification = useCallback((notification) => {
        if (window.showNotification) {
            window.showNotification(notification);
        }
    }, []);

    return { showNotification };
};

// Utility functions for common notifications
export const showNewLeadNotification = (leadName, interest) => {
    if (window.showNotification) {
        window.showNotification({
            type: 'new_lead',
            title: '🔥 New Lead!',
            message: `${leadName} interested in ${interest}`,
        });
    }
};

export const showDealClosedNotification = (clientName, property) => {
    if (window.showNotification) {
        window.showNotification({
            type: 'deal_closed',
            title: '💰 Deal Closed!',
            message: `${clientName} purchased ${property}`,
        });
    }
};

export default RealTimeNotifications;
