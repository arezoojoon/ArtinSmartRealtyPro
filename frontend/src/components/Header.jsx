/**
 * Artin Smart Realty - Premium Header Component
 * Search bar, notifications, and user quick actions
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Search,
  Bell,
  Settings,
  ChevronDown,
  User,
  LogOut,
  DollarSign,
  Users,
  Building2,
  X,
} from 'lucide-react';

const Header = ({ user, onLogout, notificationCount = 0 }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [notifications, setNotifications] = useState([]);

  const notificationRef = useRef(null);
  const userMenuRef = useRef(null);

  // Sample notifications - replace with real data
  useEffect(() => {
    setNotifications([
      {
        id: 1,
        type: 'new_lead',
        title: 'New Lead!',
        message: 'Sarah Jenkins interested in Palm Jumeirah Villa',
        time: '2 min ago',
        unread: true,
      },
      {
        id: 2,
        type: 'deal_closed',
        title: 'Deal Closed! 🎉',
        message: 'Michael Chen purchased Downtown Penthouse',
        time: '1 hour ago',
        unread: true,
      },
      {
        id: 3,
        type: 'appointment',
        title: 'Upcoming Viewing',
        message: 'Emma Davis - Villa viewing at 4:00 PM',
        time: '3 hours ago',
        unread: false,
      },
    ]);
  }, []);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (notificationRef.current && !notificationRef.current.contains(e.target)) {
        setShowNotifications(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
        setShowUserMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'new_lead': return <Users className="w-4 h-4 text-gold-400" />;
      case 'deal_closed': return <DollarSign className="w-4 h-4 text-green-400" />;
      case 'appointment': return <Building2 className="w-4 h-4 text-blue-400" />;
      default: return <Bell className="w-4 h-4 text-gray-400" />;
    }
  };

  const unreadCount = notifications.filter(n => n.unread).length;

  return (
    <header className="glass-header px-6 py-4 flex items-center justify-between sticky top-0 z-40">
      {/* Search Bar */}
      <div className="flex-1 max-w-2xl">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search leads, properties..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input w-full pl-12 pr-4"
          />
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-4 ml-6">
        {/* Notifications */}
        <div className="relative" ref={notificationRef}>
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="btn-icon notification-bell"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="notification-badge">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>

          {showNotifications && (
            <div className="notification-dropdown">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-semibold text-white">Notifications</h4>
                <button
                  onClick={() => setShowNotifications(false)}
                  className="text-gray-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-2 max-h-80 overflow-y-auto">
                {notifications.map((notif) => (
                  <div
                    key={notif.id}
                    className={`notification-item ${notif.unread ? 'notification-item-unread' : ''}`}
                  >
                    <div className="w-8 h-8 rounded-full bg-navy-700 flex items-center justify-center flex-shrink-0">
                      {getNotificationIcon(notif.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white">{notif.title}</p>
                      <p className="text-xs text-gray-400 truncate">{notif.message}</p>
                      <p className="text-xs text-gray-500 mt-1">{notif.time}</p>
                    </div>
                  </div>
                ))}
              </div>

              <button className="w-full mt-4 text-sm text-gold-400 hover:text-gold-300 transition-colors">
                View all notifications
              </button>
            </div>
          )}
        </div>

        {/* User Menu */}
        <div className="relative" ref={userMenuRef}>
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-3 p-2 rounded-xl hover:bg-navy-800/50 transition-all"
          >
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center text-navy-900 font-bold">
              {user?.name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${showUserMenu ? 'rotate-180' : ''}`} />
          </button>

          {showUserMenu && (
            <div className="absolute right-0 top-full mt-2 w-56 glass-card p-2 z-50 animate-slide-up">
              <div className="px-3 py-2 border-b border-white/5 mb-2">
                <p className="text-sm font-medium text-white">{user?.name || 'User'}</p>
                <p className="text-xs text-gray-400">{user?.email}</p>
              </div>

              <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-gray-300 hover:bg-navy-700 hover:text-white transition-all">
                <User className="w-4 h-4" />
                <span className="text-sm">Profile</span>
              </button>

              <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-gray-300 hover:bg-navy-700 hover:text-white transition-all">
                <Settings className="w-4 h-4" />
                <span className="text-sm">Settings</span>
              </button>

              <hr className="my-2 border-white/5" />

              <button
                onClick={onLogout}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-red-400 hover:bg-red-500/10 transition-all"
              >
                <LogOut className="w-4 h-4" />
                <span className="text-sm">Logout</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
