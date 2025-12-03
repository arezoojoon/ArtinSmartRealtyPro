import { LayoutDashboard, Users, CalendarDays, Building2, BarChart3, Settings, LogOut, QrCode, Send, BookOpen, Gift } from 'lucide-react';

export const Sidebar = ({ activeTab, setActiveTab, onLogout, isOpen, onClose }) => {
  const menuItems = [
    { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { id: 'leads', icon: Users, label: 'Lead Pipeline' },
    { id: 'calendar', icon: CalendarDays, label: 'Calendar' },
    { id: 'properties', icon: Building2, label: 'Properties' },
    { id: 'analytics', icon: BarChart3, label: 'Analytics' },
    { id: 'qr', icon: QrCode, label: 'QR Generator' },
    { id: 'broadcast', icon: Send, label: 'Broadcast' },
    { id: 'catalogs', icon: BookOpen, label: 'Catalogs' },
    { id: 'lottery', icon: Gift, label: 'Lottery' },
    { id: 'settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <aside className={`w-72 glass-sidebar fixed h-screen left-0 top-0 z-50 flex flex-col animate-slide-in-left transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
      <div className="px-6 py-6 mb-4 flex items-center gap-3">
        <div className="w-10 h-10 bg-gold-500 rounded-lg flex items-center justify-center font-bold text-navy-900">AS</div>
        <div>
          <h1 className="text-xl font-bold text-white">Artin<span className="text-gold-500">Realty</span></h1>
          <p className="text-xs text-gray-400">Smart Agent</p>
        </div>
      </div>
      <nav className="flex-1 px-4 space-y-2 overflow-y-auto no-scrollbar">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
              activeTab === item.id 
                ? 'bg-gold-500/10 text-gold-500 border-r-2 border-gold-500' 
                : 'text-gray-400 hover:bg-navy-800 hover:text-white'
            }`}
          >
            <item.icon size={20} />
            <span className="font-medium">{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="p-4 mt-auto">
        <button onClick={onLogout} className="flex items-center gap-3 px-4 py-3 rounded-xl text-gray-400 hover:text-red-500 w-full transition-colors">
          <LogOut size={20} />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
};
