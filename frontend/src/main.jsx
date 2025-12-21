import React, { useState, useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import Dashboard from './components/Dashboard'
import AgentDashboard from './components/AgentDashboard'
import Login from './components/Login'
import SuperAdminDashboard from './components/SuperAdminDashboard'
import ImpersonationBar from './components/ImpersonationBar'
import RealTimeNotifications from './components/RealTimeNotifications'
import './index.css'

/**
 * ArtinSmartRealty V2 - App Entry Point
 * Handles authentication state, RBAC, and routing
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
    const userRole = localStorage.getItem('userRole') || 'admin'; // 'super_admin', 'admin', 'agent'

    if (token && tenantId) {
      setIsAuthenticated(true);
      setUser({
        token,
        tenant_id: parseInt(tenantId),
        name: userName,
        email: userEmail,
        is_super_admin: isSuperAdmin,
        role: isSuperAdmin ? 'super_admin' : userRole,
      });
    }
    setLoading(false);
  }, []);

  const handleLogin = (userData) => {
    // Determine user role
    let role = 'admin';
    if (userData.is_super_admin) {
      role = 'super_admin';
    } else if (userData.role) {
      role = userData.role; // 'admin' or 'agent'
    }

    localStorage.setItem('isSuperAdmin', userData.is_super_admin ? 'true' : 'false');
    localStorage.setItem('userRole', role);

    setIsAuthenticated(true);
    setUser({
      token: userData.access_token,
      tenant_id: userData.tenant_id,
      name: userData.name,
      email: userData.email,
      is_super_admin: userData.is_super_admin,
      role: role,
    });
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('tenantId');
    localStorage.removeItem('userName');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('isSuperAdmin');
    localStorage.removeItem('userRole');
    setIsAuthenticated(false);
    setUser(null);
    setSelectedTenant(null);
  };

  const handleSelectTenant = (tenant) => {
    setSelectedTenant(tenant);
  };

  const handleImpersonate = async (tenant) => {
    // Impersonation logic already handled in SuperAdminDashboard
    // Just redirect to main dashboard
    setSelectedTenant(tenant);
  };

  const handleExitImpersonation = () => {
    // Restore admin token from sessionStorage
    const adminToken = sessionStorage.getItem('admin_fallback_token');
    if (adminToken) {
      localStorage.setItem('token', adminToken);
    }

    // Clear impersonation data
    sessionStorage.removeItem('admin_fallback_token');
    sessionStorage.removeItem('impersonating_tenant');

    // Return to Super Admin dashboard
    setSelectedTenant(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-navy-950 via-navy-900 to-navy-800 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-navy-700 border-t-gold-500 rounded-full animate-spin"></div>
          <p className="text-gray-400 text-sm">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  // Super Admin view (not impersonating)
  if (user.is_super_admin && !selectedTenant) {
    return (
      <SuperAdminDashboard
        user={user}
        onLogout={handleLogout}
        onImpersonate={handleImpersonate}
      />
    );
  }

  // Super Admin impersonating a tenant's dashboard
  if (user.is_super_admin && selectedTenant) {
    const viewAsUser = {
      ...user,
      tenant_id: selectedTenant.id,
      name: selectedTenant.name,
      token: user.token,  // Pass Super Admin token for API calls
      role: 'admin', // View as admin when impersonating
    };
    return (
      <RealTimeNotifications>
        <div>
          <ImpersonationBar
            tenantName={selectedTenant.name || selectedTenant.email}
            onExit={handleExitImpersonation}
          />
          <div className="pt-16">
            <Dashboard user={viewAsUser} onLogout={handleLogout} />
          </div>
        </div>
      </RealTimeNotifications>
    );
  }

  // Agent Dashboard - Restricted view for sales agents
  if (user.role === 'agent') {
    return (
      <RealTimeNotifications>
        <AgentDashboard user={user} onLogout={handleLogout} />
      </RealTimeNotifications>
    );
  }

  // Tenant Admin Dashboard - Full access
  return (
    <RealTimeNotifications>
      <Dashboard user={user} onLogout={handleLogout} />
    </RealTimeNotifications>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
