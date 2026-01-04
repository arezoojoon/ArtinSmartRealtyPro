/**
 * Mobile Bottom Navigation Component
 * Displays a sticky bottom navigation bar for mobile devices (< 1024px)
 * Includes safe area handling for iOS notch/home indicator
 */

import React from 'react';
import { LayoutDashboard, Users, Megaphone, Settings } from 'lucide-react';

const MobileNav = ({ activeView, onViewChange, notificationCount = 0 }) => {
    const navItems = [
        {
            id: 'dashboard',
            icon: LayoutDashboard,
            label: 'Dashboard',
            badge: null
        },
        {
            id: 'pipeline',
            icon: Users,
            label: 'Leads',
            badge: notificationCount > 0 ? notificationCount : null
        },
        {
            id: 'broadcast',
            icon: Megaphone,
            label: 'Broadcast',
            badge: null
        },
        {
            id: 'settings',
            icon: Settings,
            label: 'Settings',
            badge: null
        },
    ];

    return (
        <nav
            className="mobile-nav-container lg:hidden fixed bottom-0 left-0 right-0 z-50"
            style={{
                paddingBottom: 'env(safe-area-inset-bottom)',
            }}
        >
            <div className="mobile-nav-glass">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = activeView === item.id;

                    return (
                        <button
                            key={item.id}
                            onClick={() => onViewChange(item.id)}
                            className={`mobile-nav-item ${isActive ? 'mobile-nav-item-active' : ''}`}
                            aria-label={item.label}
                            aria-current={isActive ? 'page' : undefined}
                        >
                            <div className="relative">
                                <Icon
                                    className={`w-6 h-6 transition-colors ${isActive ? 'text-gold-400' : 'text-gray-400'
                                        }`}
                                />
                                {item.badge && (
                                    <span className="mobile-nav-badge">
                                        {item.badge > 99 ? '99+' : item.badge}
                                    </span>
                                )}
                            </div>
                            <span
                                className={`text-xs font-medium mt-1 transition-colors ${isActive ? 'text-gold-400' : 'text-gray-400'
                                    }`}
                            >
                                {item.label}
                            </span>
                            {isActive && (
                                <div className="mobile-nav-indicator" />
                            )}
                        </button>
                    );
                })}
            </div>
        </nav>
    );
};

export default MobileNav;
