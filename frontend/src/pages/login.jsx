import { useState } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { ShieldAlert, Loader2 } from "lucide-react"
import { useAuth } from "../context/AuthContext"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Input } from "../components/ui/input"
import { Button } from "../components/ui/button"

export default function Login() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  
  const from = location.state?.from?.pathname || "/dashboard"

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError("")
    setIsLoading(true)
    
    try {
      const loggedInUser = await login(email, password)
      
      // Determine destination based on role, unless they were trying to access a specific page
      let destination = loggedInUser.role === "citizen" ? "/report" : "/dashboard"
      
      if (location.state?.from?.pathname && location.state.from.pathname !== "/") {
         destination = location.state.from.pathname
      }
      
      navigate(destination, { replace: true })
    } catch (err) {
      setError(err.message || "Failed to login")
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background dark p-4">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <ShieldAlert className="h-12 w-12 text-destructive mb-4" />
          <h1 className="text-2xl font-bold tracking-tight">DisasterLocator</h1>
          <p className="text-sm text-muted-foreground mt-2">Emergency Operations Center</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Sign In</CardTitle>
            <CardDescription>Enter your credentials to access the dashboard.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Email address</label>
                <Input 
                  type="email" 
                  required 
                  placeholder="admin@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Password</label>
                <Input 
                  type="password" 
                  required 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>

              {error && (
                <div className="p-3 text-sm rounded-md bg-destructive/15 text-destructive border border-destructive/30">
                  {error}
                </div>
              )}

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                {isLoading ? "Signing in..." : "Sign In"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
