import Sidebar from './Sidebar';
import Header from './Header';
import { useState } from 'react';

export const Layout = ({ children, activeTab, setActiveTab, user, onLogout }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-navy-900 relative">
      <div className="fixed inset-0 pointer-events-none bg-gradient-radial from-gold-500/5 via-transparent to-transparent"></div>

      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onLogout={onLogout}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
      <Header
        user={user}
        onMenuClick={() => setSidebarOpen(!sidebarOpen)}
      />

      {/* Responsive main content */}
      <main className="lg:ml-72 mt-16 lg:mt-20 p-4 sm:p-6 lg:p-8 relative z-10">
        <div className="max-w-[1920px] mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
};
