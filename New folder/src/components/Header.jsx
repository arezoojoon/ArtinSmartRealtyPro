import { Search, Bell, Menu } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import LanguageSwitcher from './LanguageSwitcher'
import NotificationPanel from './NotificationPanel'

export const Header = ({ isSidebarOpen, setIsSidebarOpen }) => {
  const { user } = useAuth()

  return (
    <header className="h-20 glass-header fixed top-0 right-0 lg:left-72 left-0 z-40 px-4 md:px-6 lg:px-8">
      <div className="h-full flex items-center justify-between gap-4">
        {/* Hamburger Menu Button (Mobile) */}
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="lg:hidden p-2 rounded-xl bg-navy-800/50 text-white hover:bg-navy-700 transition-colors"
        >
          <Menu className="w-6 h-6" />
        </button>

        {/* Search Bar */}
        <div className="flex-1 max-w-lg">
          <div className="relative hidden md:block">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search leads, properties, clients..."
              className="w-full pl-12 pr-4 py-3 bg-navy-800/50 border border-white/10 rounded-xl 
                       text-gray-200 placeholder-gray-500 focus:outline-none focus:border-gold-500/50 
                       focus:bg-navy-800/70 transition-all"
            />
          </div>
          {/* Mobile Search Icon */}
          <button className="md:hidden p-2 text-gray-400 hover:text-gold-500 transition-colors">
            <Search className="w-5 h-5" />
          </button>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-3 md:gap-6">
          {/* Language Switcher */}
          <div className="hidden md:block">
            <LanguageSwitcher />
          </div>
          
          {/* Notifications Bell */}
          <NotificationPanel />

          {/* User Avatar */}
          <div className="w-9 h-9 md:w-10 md:h-10 rounded-full border-2 border-gold-500 p-0.5 cursor-pointer hover:border-gold-400 transition-colors">
            <div className="w-full h-full rounded-full flex items-center justify-center text-navy-900 font-bold text-sm" style={{background: 'linear-gradient(135deg, #E5C365 0%, #B8962E 100%)'}}>
              {user?.full_name?.[0] || user?.username?.[0] || 'A'}
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
