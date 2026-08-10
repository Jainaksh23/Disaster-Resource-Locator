import { createContext, useContext, useState, useEffect } from "react"
import { apiFetch } from "../api/client"

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("token"))
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // If we have a token, fetch the user profile to verify it's still valid
    const fetchUser = async () => {
      if (!token) {
        setLoading(false)
        return
      }
      try {
        const data = await apiFetch("/api/v1/auth/me")
        setUser(data)
      } catch (err) {
        console.error("Failed to authenticate token", err)
        logout()
      } finally {
        setLoading(false)
      }
    }
    
    fetchUser()
  }, [token])

  const login = async (email, password) => {
    // The backend uses a custom POST /api/v1/auth/login-json endpoint
    const data = await apiFetch("/api/v1/auth/login-json", {
      method: "POST",
      body: JSON.stringify({ email, password })
    })
    
    setToken(data.access_token)
    setUser(data.user)
    localStorage.setItem("token", data.access_token)
    return data.user
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem("token")
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
