import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import CitizenLayout from './components/layout'
import AdminLayout from './components/admin-layout'
import Dashboard from './pages/dashboard'
import MapPage from './pages/map'
import Report from './pages/report'
import Reports from './pages/reports'
import Resources from './pages/resources'
import Login from './pages/login'
import Register from './pages/register'
import './index.css'

const queryClient = new QueryClient()

// Protected Route Wrapper
function ProtectedRoute({ children }) {
  const { token, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return <div className="min-h-screen bg-background dark flex items-center justify-center">Loading...</div>
  }

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return children
}

// Role-based Route Guard for specific pages
function RoleRoute({ children, allowedRoles, fallbackPath }) {
  const { user } = useAuth()
  
  // If user role is not in the allowed list, redirect to fallback
  if (user && !allowedRoles.includes(user.role)) {
    return <Navigate to={fallbackPath} replace />
  }
  
  return children
}

// Conditional Layout Wrapper
function RootLayout() {
  const { user, loading } = useAuth()
  
  if (loading) return null
  
  if (user && ['admin', 'responder'].includes(user.role)) {
    return <AdminLayout />
  }
  
  return <CitizenLayout />
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            {/* Main Application Routes */}
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <RootLayout />
                </ProtectedRoute>
              }
            >
              {/* Default Redirect */}
              <Route index element={<Navigate to="/dashboard" replace />} />
              
              {/* Admin & Responder Only Routes */}
              <Route path="dashboard" element={
                <RoleRoute allowedRoles={['admin', 'responder']} fallbackPath="/report">
                  <Dashboard />
                </RoleRoute>
              } />
              <Route path="resources" element={
                <RoleRoute allowedRoles={['admin', 'responder']} fallbackPath="/report">
                  <Resources />
                </RoleRoute>
              } />
              <Route path="reports" element={
                <RoleRoute allowedRoles={['admin', 'responder']} fallbackPath="/report">
                  <Reports />
                </RoleRoute>
              } />

              {/* Shared Routes (Accessible by all roles) */}
              <Route path="report" element={<Report />} />
              <Route path="map" element={<MapPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)
