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

// Role-based Route Guard
function RoleRoute({ children, allowedRoles, fallbackPath }) {
  const { user } = useAuth()
  
  // If user role is not in the allowed list, redirect to fallback
  if (user && !allowedRoles.includes(user.role)) {
    return <Navigate to={fallbackPath} replace />
  }
  
  return children
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            {/* Admin & Responder Routes */}
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <RoleRoute allowedRoles={['admin', 'responder']} fallbackPath="/report">
                    <AdminLayout />
                  </RoleRoute>
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="map" element={<MapPage />} />
              <Route path="report" element={<Report />} />
              <Route path="resources" element={<Resources />} />
              <Route path="reports" element={<Reports />} />
            </Route>

            {/* Citizen Routes */}
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <RoleRoute allowedRoles={['citizen']} fallbackPath="/dashboard">
                    <CitizenLayout />
                  </RoleRoute>
                </ProtectedRoute>
              }
            >
              <Route path="report" element={<Report />} />
              <Route path="map" element={<MapPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)
