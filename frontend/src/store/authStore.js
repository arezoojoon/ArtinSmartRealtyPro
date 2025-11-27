import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * Authentication Store
 * Manages user session, role, and tenant context
 */
const useAuthStore = create(
  persist(
    (set, get) => ({
      // User data
      user: null,
      token: null,
      role: null, // 'super_admin' | 'tenant_admin' | 'agent'
      tenantId: null,
      tenantName: null,
      
      // Login action
      login: (userData) => {
        set({
          user: userData.user,
          token: userData.token,
          role: userData.role,
          tenantId: userData.tenant_id,
          tenantName: userData.tenant_name
        });
      },
      
      // Logout action
      logout: () => {
        set({
          user: null,
          token: null,
          role: null,
          tenantId: null,
          tenantName: null
        });
      },
      
      // Impersonate tenant (Super Admin only)
      impersonate: (tenantId, tenantName) => {
        set({
          role: 'tenant_admin',
          tenantId,
          tenantName
        });
      },
      
      // Stop impersonation
      stopImpersonate: () => {
        set({
          role: 'super_admin',
          tenantId: null,
          tenantName: null
        });
      },
      
      // Check if user is authenticated
      isAuthenticated: () => !!get().token,
      
      // Check if user is super admin
      isSuperAdmin: () => get().role === 'super_admin',
      
      // Check if user is tenant admin
      isTenantAdmin: () => get().role === 'tenant_admin',
      
      // Check if user is agent
      isAgent: () => get().role === 'agent'
    }),
    {
      name: 'artin-auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        role: state.role,
        tenantId: state.tenantId,
        tenantName: state.tenantName
      })
    }
  )
);

export default useAuthStore;
