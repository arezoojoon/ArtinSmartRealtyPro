/**
 * Authentication Context با Zustand
 * مدیریت state کاربر و JWT token
 */
import React, { createContext, useContext, useEffect } from 'react'
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import axios from 'axios'

// ============================================
// AXIOS INSTANCE
// ============================================
const API_URL = import.meta.env.VITE_API_URL || '/api';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Add response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ============================================
// ZUSTAND STORE
// ============================================
export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Login
      login: async (username, password) => {
        set({ isLoading: true, error: null })
        try {
          const response = await api.post('/api/auth/login', {
            username,
            password,
          })

          const { access_token, user } = response.data

          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })

          return { success: true }
        } catch (error) {
          let errorMessage = 'Login failed. Please try again.'
          
          if (error.response?.data?.detail) {
            const detail = error.response.data.detail
            // If detail is array (validation errors), extract messages
            if (Array.isArray(detail)) {
              errorMessage = detail.map(err => err.msg || err).join(', ')
            } else if (typeof detail === 'string') {
              errorMessage = detail
            } else if (typeof detail === 'object') {
              errorMessage = JSON.stringify(detail)
            }
          }

          set({
            error: errorMessage,
            isLoading: false,
          })

          return { success: false, error: errorMessage }
        }
      },

      // Logout
      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        })
      },

      // Get current user
      getCurrentUser: async () => {
        if (!get().token) return

        try {
          const response = await api.get('/api/auth/me')
          set({ user: response.data })
        } catch (error) {
          console.error('Failed to get current user:', error)
          get().logout()
        }
      },

      // Clear error
      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

// ============================================
// CONTEXT
// ============================================
const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const authStore = useAuthStore()

  useEffect(() => {
    // Verify token on mount
    if (authStore.isAuthenticated && authStore.token) {
      authStore.getCurrentUser()
    }
  }, [])

  return (
    <AuthContext.Provider value={authStore}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
