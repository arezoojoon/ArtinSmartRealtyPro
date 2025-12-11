import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import { AuthProvider } from './context/AuthContext'
import { LanguageProvider } from './context/LanguageContext'
import { NotificationProvider } from './context/NotificationContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import ErrorBoundary from './components/ErrorBoundary'
import ImpersonationBanner from './components/ImpersonationBanner'

// Pages
import Login from './pages/Login'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import Dashboard from './pages/Dashboard'
import Leads from './pages/Leads'
import Lottery from './pages/Lottery'
import Catalogs from './pages/Catalogs'
import QRGenerator from './pages/QRGenerator'
import Broadcast from './pages/Broadcast'
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'
import SuperadminPanel from './pages/SuperadminPanel'
import SuperAdminDashboard from './pages/SuperAdminDashboard'
import SuperAdminSettings from './pages/SuperAdminSettings'

function App() {
  return (
    <ErrorBoundary>
      <LanguageProvider>
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AuthProvider>
          <NotificationProvider>
            {/* Impersonation Banner - Shows only when impersonating */}
            <ImpersonationBanner />
        
        <ToastContainer 
          position="top-right"
          autoClose={3000}
          hideProgressBar={false}
          newestOnTop={true}
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
          theme="dark"
        />
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />

          {/* Protected Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/leads"
            element={
              <ProtectedRoute>
                <Leads />
              </ProtectedRoute>
            }
          />
          <Route
            path="/lottery"
            element={
              <ProtectedRoute>
                <Lottery />
              </ProtectedRoute>
            }
          />
          <Route
            path="/catalogs"
            element={
              <ProtectedRoute>
                <Catalogs />
              </ProtectedRoute>
            }
          />
          <Route
            path="/qr-generator"
            element={
              <ProtectedRoute>
                <QRGenerator />
              </ProtectedRoute>
            }
          />
          <Route
            path="/broadcast"
            element={
              <ProtectedRoute>
                <Broadcast />
              </ProtectedRoute>
            }
          />
          <Route
            path="/analytics"
            element={
              <ProtectedRoute>
                <Analytics />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <Settings />
              </ProtectedRoute>
            }
          />
          <Route
            path="/superadmin"
            element={
              <ProtectedRoute requiredRole="superadmin">
                <SuperadminPanel />
              </ProtectedRoute>
            }
          />
          <Route
            path="/superadmin/dashboard"
            element={
              <ProtectedRoute requiredRole="superadmin">
                <SuperAdminDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/superadmin/settings"
            element={
              <ProtectedRoute requiredRole="superadmin">
                <SuperAdminSettings />
              </ProtectedRoute>
            }
          />

          {/* Catch all - redirect to dashboard */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </NotificationProvider>
      </AuthProvider>
    </BrowserRouter>
    </LanguageProvider>
    </ErrorBoundary>
  )
}

export default App
