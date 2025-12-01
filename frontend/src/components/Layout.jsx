import { Sidebar } from './Sidebar';
import { Header } from './Header';

export const Layout = ({ children, activeTab, setActiveTab, user, onLogout }) => {
  return (
    <div className="min-h-screen bg-navy-900 relative">
      <div className="fixed inset-0 pointer-events-none bg-gradient-radial from-gold-500/5 via-transparent to-transparent"></div>
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} onLogout={onLogout} />
      <Header user={user} />
      <main className="ml-72 mt-20 p-8 relative z-10">
        <div className="max-w-[1920px] mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
};
