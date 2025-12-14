import axios from 'axios';
import useAuthStore from '../store/authStore';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add tenant_id to headers if present
    const tenantId = useAuthStore.getState().tenantId;
    if (tenantId) {
      config.headers['X-Tenant-ID'] = tenantId;
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

/**
 * ============================================
 * SUPER ADMIN APIs - God Mode
 * ============================================
 */

// Tenant Management
export const getAllTenants = () => apiClient.get('/admin/tenants');
export const getTenantDetails = (tenantId) => apiClient.get(`/admin/tenants/${tenantId}`);
export const suspendTenant = (tenantId) => apiClient.post(`/admin/tenants/${tenantId}/suspend`);
export const activateTenant = (tenantId) => apiClient.post(`/admin/tenants/${tenantId}/activate`);
export const updateTenantPlan = (tenantId, plan) => apiClient.put(`/admin/tenants/${tenantId}/plan`, { plan });
export const impersonateTenant = (tenantId) => apiClient.post(`/admin/tenants/${tenantId}/impersonate`);

// AI & Resource Monitoring
export const getTokenUsage = (tenantId, period = '30d') => apiClient.get(`/admin/monitoring/tokens/${tenantId}?period=${period}`);
export const getSystemErrors = (limit = 100) => apiClient.get(`/admin/monitoring/errors?limit=${limit}`);
export const getServerStatus = () => apiClient.get('/admin/monitoring/servers');

// Billing & Finance
export const getMRR = () => apiClient.get('/admin/billing/mrr');
export const getInvoices = (page = 1) => apiClient.get(`/admin/billing/invoices?page=${page}`);
export const generateLicenseKey = (tenantId, plan) => apiClient.post('/admin/billing/license', { tenant_id: tenantId, plan });

/**
 * ============================================
 * TENANT ADMIN APIs - Agency Mode
 * ============================================
 */

// CRM & Leads
export const getLeads = (status = null) => apiClient.get('/leads', { params: { status } });
export const getLeadDetails = (leadId) => apiClient.get(`/leads/${leadId}`);
export const updateLeadStatus = (leadId, status) => apiClient.put(`/leads/${leadId}/status`, { status });
export const assignLeadToAgent = (leadId, agentId) => apiClient.post(`/leads/${leadId}/assign`, { agent_id: agentId });
export const addLeadNote = (leadId, note) => apiClient.post(`/leads/${leadId}/notes`, { content: note });

// Live Chat & Takeover
export const getActiveChats = () => apiClient.get('/chats/active');
export const getChatHistory = (leadId) => apiClient.get(`/chats/${leadId}/history`);
export const takeoverChat = (leadId) => apiClient.post(`/chats/${leadId}/takeover`);
export const releaseChat = (leadId) => apiClient.post(`/chats/${leadId}/release`);
export const sendManualMessage = (leadId, message) => apiClient.post(`/chats/${leadId}/send`, { message });

// Bot Configuration
export const getBotSettings = () => apiClient.get('/settings/bot');
export const updateBotSettings = (settings) => apiClient.put('/settings/bot', settings);
export const uploadInventory = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return apiClient.post('/inventory/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
};
export const getInventory = () => apiClient.get('/inventory');
export const deleteProperty = (propertyId) => apiClient.delete(`/inventory/${propertyId}`);

// Analytics
export const getSalesFunnel = (period = '30d') => apiClient.get(`/analytics/funnel?period=${period}`);
export const getAgentPerformance = (period = '30d') => apiClient.get(`/analytics/agents?period=${period}`);
export const exportLeads = (filters) => apiClient.get('/analytics/export', { params: filters, responseType: 'blob' });

/**
 * ============================================
 * AGENT APIs - Sales Mode
 * ============================================
 */

// My Leads (filtered by agent)
export const getMyLeads = () => apiClient.get('/agent/leads');
export const getMyTasks = () => apiClient.get('/agent/tasks');
export const createTask = (leadId, task) => apiClient.post('/agent/tasks', { lead_id: leadId, ...task });
export const markTaskDone = (taskId) => apiClient.put(`/agent/tasks/${taskId}/done`);

// Quick Actions
export const sendWhatsApp = (leadId, message) => apiClient.post(`/agent/leads/${leadId}/whatsapp`, { message });
export const sendPDF = (leadId, pdfType) => apiClient.post(`/agent/leads/${leadId}/pdf`, { type: pdfType });
export const addQuickNote = (leadId, note) => apiClient.post(`/agent/leads/${leadId}/note`, { content: note });

/**
 * ============================================
 * SHARED APIs
 * ============================================
 */

// Authentication
export const login = (email, password) => apiClient.post('/auth/login', { email, password });
export const logout = () => apiClient.post('/auth/logout');
export const getProfile = () => apiClient.get('/auth/profile');

// Notifications
export const getNotifications = () => apiClient.get('/notifications');
export const markNotificationRead = (notificationId) => apiClient.put(`/notifications/${notificationId}/read`);

export default apiClient;
