import { NavLink } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Users, 
  Trophy,
  BookOpen,
  QrCode,
  Send,
  BarChart3,
  Settings,
  LogOut,
  X
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import goldLogo from '../goldlogo.svg'

export const Sidebar = ({ isSidebarOpen, setIsSidebarOpen }) => {
  const { user, logout } = useAuth()

  // Define menu items with required roles
  const allMenuItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard', roles: ['viewer', 'agent', 'admin', 'superadmin'] },
    { path: '/leads', icon: Users, label: 'Leads', roles: ['viewer', 'agent', 'admin', 'superadmin'] },
    { path: '/lottery', icon: Trophy, label: 'Lottery System', roles: ['admin', 'superadmin'] },
    { path: '/catalogs', icon: BookOpen, label: 'Catalogs', roles: ['viewer', 'agent', 'admin', 'superadmin'] },
    { path: '/qr-generator', icon: QrCode, label: 'QR Generator', roles: ['agent', 'admin', 'superadmin'] },
    { path: '/broadcast', icon: Send, label: 'Broadcast', roles: ['admin', 'superadmin'] },
    { path: '/analytics', icon: BarChart3, label: 'Analytics', roles: ['admin', 'superadmin'] },
    { path: '/settings', icon: Settings, label: 'Settings', roles: ['admin'] },
    { path: '/superadmin/settings', icon: Settings, label: 'Settings', roles: ['superadmin'] },
    { path: '/superadmin', icon: Settings, label: '🔐 Superadmin Panel', roles: ['superadmin'] },
  ]

  // Filter menu items based on user role
  const menuItems = allMenuItems.filter(item => 
    item.roles.includes(user?.role || 'viewer')
  )

  const handleLinkClick = () => {
    // Close sidebar on mobile when clicking a link
    if (window.innerWidth < 1024) {
      setIsSidebarOpen(false)
    }
  }

  return (
    <aside className={`w-72 glass-sidebar fixed h-screen left-0 top-0 z-50 flex flex-col transition-transform duration-300 lg:translate-x-0 ${
      isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
    }`}>
      {/* Close button for mobile */}
      <button
        onClick={() => setIsSidebarOpen(false)}
        className="lg:hidden absolute top-4 right-4 p-2 rounded-lg bg-navy-800/50 text-white hover:bg-navy-700 transition-colors"
      >
        <X className="w-5 h-5" />
      </button>

      {/* Logo */}
      <div className="px-6 py-6 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-14 h-14 rounded-xl flex items-center justify-center">
            <img src={goldLogo} alt="Artin Expo" className="w-14 h-14" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-wide">
              Artin<span className="text-gold-500">Expo</span>
            </h1>
            <p className="text-sm text-white/40 mt-0.5">Smart Agent</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 space-y-2 overflow-y-auto">
        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            onClick={handleLinkClick}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${
                isActive
                  ? 'bg-gold-500/10 text-gold-500 border-r-2 border-gold-500 shadow-lg shadow-gold-500/10'
                  : 'text-gray-400 hover:bg-navy-800 hover:text-white'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <item.icon
                  className={`w-5 h-5 transition-colors ${
                    isActive ? 'text-gold-500' : 'group-hover:text-white'
                  }`}
                />
                <span className="font-medium">{item.label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* User Profile & Logout */}
      <div className="p-4 space-y-3">
        <button
          onClick={logout}
          className="flex items-center gap-3 px-4 py-3 rounded-xl text-gray-400 hover:bg-red-500/10 hover:text-red-500 transition-all w-full group"
        >
          <LogOut className="w-5 h-5 group-hover:text-red-500" />
          <span className="font-medium">Logout</span>
        </button>

        {/* Agent Profile Card */}
        <div className="glass-card p-4 rounded-xl">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full border-2 border-gold-500 p-0.5 relative">
              <div className="w-full h-full rounded-full flex items-center justify-center text-navy-900 font-bold text-lg" style={{background: 'linear-gradient(135deg, #E5C365 0%, #B8962E 100%)'}}>
                {user?.full_name?.[0] || user?.username?.[0] || 'A'}
              </div>
              <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-400 rounded-full border-2 border-navy-900"></span>
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="text-white font-semibold text-sm truncate">
                {user?.full_name || user?.username || 'Agent'}
              </h4>
              <p className="text-xs text-gold-400 font-medium">
                {user?.role === 'superadmin' ? '👑 Superadmin' : 
                 user?.role === 'admin' ? '⭐ Admin' :
                 user?.role === 'agent' ? '🏢 Agent' :
                 user?.role === 'viewer' ? '👁️ Viewer' : 'User'}
              </p>
              <p className="text-green-400 text-xs flex items-center gap-1 mt-0.5">
                <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse-slow"></span>
                Online
              </p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  )
}
