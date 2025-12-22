/**
 * Artin Smart Realty - Premium Sidebar Navigation
 * Luxury dark glass design with gold accents
 */

import React from 'react';
import {
  LayoutDashboard,
  Users,
  CalendarDays,
  Building2,
  BarChart3,
  Settings,
  Crown,
  MessageSquare,
  Megaphone,
  Gift,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Zap,
  Target,
  RefreshCw,
  Newspaper,
  Brain,
} from 'lucide-react';

const Sidebar = ({
  activeView,
  onViewChange,
  user,
  onLogout,
  isCollapsed = false,
  onToggleCollapse,
  userRole = 'admin' // 'super_admin', 'admin', 'agent'
}) => {
  // Navigation items based on role
  const getNavItems = () => {
    const baseItems = [
      { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard', roles: ['super_admin', 'admin', 'agent'] },
      { id: 'pipeline', icon: Users, label: 'Lead Pipeline', roles: ['super_admin', 'admin', 'agent'] },
      { id: 'lead-gen', icon: Target, label: 'Lead Generation', roles: ['super_admin', 'admin'] },
      { id: 'followup', icon: RefreshCw, label: 'Follow-up', roles: ['super_admin', 'admin', 'agent'] },
      { id: 'calendar', icon: CalendarDays, label: 'Calendar/Scheduling', roles: ['super_admin', 'admin', 'agent'] },
      { id: 'properties', icon: Building2, label: 'Properties', roles: ['super_admin', 'admin'] },
      { id: 'knowledge-base', icon: Brain, label: 'Knowledge Base', roles: ['super_admin', 'admin'] },
      { id: 'news', icon: Newspaper, label: 'Market Insider', roles: ['super_admin', 'admin', 'agent'] },
      { id: 'analytics', icon: BarChart3, label: 'Analytics', roles: ['super_admin', 'admin'] },
      { id: 'live-chat', icon: MessageSquare, label: 'Live Chat', roles: ['super_admin', 'admin'] },
      { id: 'broadcast', icon: Megaphone, label: 'Broadcast', roles: ['super_admin', 'admin'] },
      { id: 'lottery', icon: Gift, label: 'Lottery', roles: ['super_admin', 'admin'] },
      { id: 'settings', icon: Settings, label: 'Settings', roles: ['super_admin', 'admin'] },
    ];

    return baseItems.filter(item => item.roles.includes(userRole));
  };

  const navItems = getNavItems();

  return (
    <aside
      className={`glass-sidebar h-screen flex flex-col transition-all duration-300 ${isCollapsed ? 'w-20' : 'w-64'
        }`}
    >
      {/* Logo Section */}
      <div className="p-5 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center">
            <Crown className="w-6 h-6 text-navy-900" />
          </div>
          {!isCollapsed && (
            <div className="animate-fade-in">
              <h1 className="text-lg font-bold text-white">ARTIN REALTY</h1>
              <p className="text-xs text-gold-400">Smart CRM</p>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${isActive
                ? 'sidebar-item-active'
                : 'sidebar-item'
                }`}
              title={isCollapsed ? item.label : undefined}
            >
              <Icon
                className={`w-5 h-5 flex-shrink-0 transition-colors ${isActive ? 'text-gold-400' : 'text-gray-400 group-hover:text-white'
                  }`}
              />
              {!isCollapsed && (
                <span className={`text-sm font-medium transition-colors ${isActive ? 'text-gold-400' : 'text-gray-400 group-hover:text-white'
                  }`}>
                  {item.label}
                </span>
              )}
              {isActive && !isCollapsed && (
                <div className="ml-auto w-1.5 h-6 rounded-full bg-gold-400" />
              )}
            </button>
          );
        })}
      </nav>

      {/* Collapse Toggle */}
      {onToggleCollapse && (
        <button
          onClick={onToggleCollapse}
          className="mx-4 mb-2 p-2 rounded-xl bg-navy-800/50 border border-white/5 text-gray-400 hover:text-white hover:bg-navy-700 transition-all"
        >
          {isCollapsed ? (
            <ChevronRight className="w-5 h-5 mx-auto" />
          ) : (
            <div className="flex items-center justify-center gap-2">
              <ChevronLeft className="w-5 h-5" />
              <span className="text-sm">Collapse</span>
            </div>
          )}
        </button>
      )}

      {/* User Profile Section */}
      <div className="p-4 border-t border-white/5">
        <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'}`}>
          <div className="relative">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-navy-600 to-navy-700 flex items-center justify-center text-white font-bold border-2 border-gold-500/30">
              {user?.name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div className="online-indicator status-online" />
          </div>

          {!isCollapsed && (
            <div className="flex-1 min-w-0 animate-fade-in">
              <p className="text-sm font-medium text-white truncate">
                {user?.name || 'User'}
              </p>
              <p className="text-xs text-green-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
                Online
              </p>
            </div>
          )}

          {!isCollapsed && (
            <button
              onClick={onLogout}
              className="p-2 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-all"
              title="Logout"
            >
              <LogOut className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
