import React, { useState, useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import Dashboard from './components/Dashboard'
import Login from './components/Login'
import SuperAdminDashboard from './components/SuperAdminDashboard'
import './index.css'

/**
 * ArtinSmartRealty V2 - App Entry Point
 * Handles authentication state and routing
 */
function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedTenant, setSelectedTenant] = useState(null);

  useEffect(() => {
    // Check for existing auth token
    const token = localStorage.getItem('token');
    const tenantId = localStorage.getItem('tenantId');
    const userName = localStorage.getItem('userName');
    const userEmail = localStorage.getItem('userEmail');
    const isSuperAdmin = localStorage.getItem('isSuperAdmin') === 'true';
    
    if (token && tenantId) {
      setIsAuthenticated(true);
      setUser({
        token,
        tenant_id: parseInt(tenantId),
        name: userName,
        email: userEmail,
        is_super_admin: isSuperAdmin,
      });
    }
    setLoading(false);
  }, []);

  const handleLogin = (userData) => {
    localStorage.setItem('isSuperAdmin', userData.is_super_admin ? 'true' : 'false');
    setIsAuthenticated(true);
    setUser({
      token: userData.access_token,
      tenant_id: userData.tenant_id,
      name: userData.name,
      email: userData.email,
      is_super_admin: userData.is_super_admin,
    });
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('tenantId');
    localStorage.removeItem('userName');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('isSuperAdmin');
    setIsAuthenticated(false);
    setUser(null);
    setSelectedTenant(null);
  };

  const handleSelectTenant = (tenant) => {
    setSelectedTenant(tenant);
  };

  const handleBackToAdmin = () => {
    setSelectedTenant(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-navy-900 flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-navy-800 border-t-gold-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  // Super Admin view
  if (user.is_super_admin && !selectedTenant) {
    return (
      <div>
        <div className="fixed top-4 right-4 z-50">
          <button
            onClick={handleLogout}
            className="bg-red-500 hover:bg-red-400 text-white px-4 py-2 rounded-lg text-sm font-medium"
          >
            Logout
          </button>
        </div>
        <SuperAdminDashboard 
          token={user.token} 
          onSelectTenant={handleSelectTenant}
        />
      </div>
    );
  }

  // Super Admin viewing a tenant's dashboard
  if (user.is_super_admin && selectedTenant) {
    const viewAsUser = {
      ...user,
      tenant_id: selectedTenant.id,
      name: selectedTenant.name,
    };
    return (
      <div>
        <div className="fixed top-4 right-4 z-50 flex gap-2">
          <button
            onClick={handleBackToAdmin}
            className="bg-gold-500 hover:bg-gold-400 text-navy-900 px-4 py-2 rounded-lg text-sm font-medium"
          >
            ← Back to Admin
          </button>
          <button
            onClick={handleLogout}
            className="bg-red-500 hover:bg-red-400 text-white px-4 py-2 rounded-lg text-sm font-medium"
          >
            Logout
          </button>
        </div>
        <Dashboard user={viewAsUser} onLogout={handleLogout} />
      </div>
    );
  }

  // Normal tenant dashboard
  return <Dashboard user={user} onLogout={handleLogout} />;
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
