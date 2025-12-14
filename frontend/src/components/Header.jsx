import { Search, Bell } from 'lucide-react';

import { Menu } from 'lucide-react';

export const Header = ({ user, onMenuClick }) => {
  return (
    <header className="h-16 lg:h-20 glass-header fixed top-0 right-0 left-0 lg:left-72 z-40 px-4 lg:px-8">
      <div className="h-full flex items-center justify-between gap-4">
        {/* Hamburger Menu - Mobile Only */}
        <button 
          onClick={onMenuClick}
          className="lg:hidden text-gray-400 hover:text-gold-500 transition-colors p-2 hover:bg-white/5 rounded-xl"
        >
          <Menu className="w-6 h-6" />
        </button>

        <div className="flex-1 max-w-lg hidden sm:block">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input 
              type="text" 
              placeholder="Search leads, properties..." 
              className="w-full pl-12 pr-4 py-2 lg:py-3 bg-navy-800/50 border border-white/10 rounded-xl text-gray-200 focus:outline-none focus:border-gold-500/50 transition-all text-sm" 
            />
          </div>
        </div>
        <div className="flex items-center gap-6">
          <button className="relative text-gray-400 hover:text-gold-500 transition-colors p-2 hover:bg-white/5 rounded-xl">
            <Bell className="w-6 h-6" />
            <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-gold-500 rounded-full"></span>
          </button>
          <div className="w-10 h-10 rounded-full border-2 border-gold-500 p-0.5">
            <div className="w-full h-full rounded-full flex items-center justify-center text-navy-900 font-bold bg-gold-500">
              {user?.name?.charAt(0) || 'A'}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
