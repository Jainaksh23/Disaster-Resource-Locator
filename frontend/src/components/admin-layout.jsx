import { Link, Outlet, useLocation } from "react-router-dom"
import { 
  ShieldAlert, 
  Map, 
  LayoutDashboard, 
  FileText,
  Users,
  LogOut,
  Menu,
  X
} from "lucide-react"
import { useAuth } from "../context/AuthContext"
import { Button } from "./ui/button"
import { useState } from "react"

export default function AdminLayout() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen)

  const navItems = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Live Map", href: "/map", icon: Map },
    { name: "Manage Resources", href: "/resources", icon: Users },
    { name: "All Reports", href: "/reports", icon: FileText },
  ]

  return (
    <div className="min-h-screen bg-background dark flex flex-col md:flex-row">
      {/* Mobile Header */}
      <header className="md:hidden sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur flex h-14 items-center justify-between px-4">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="h-6 w-6 text-destructive" />
          <span className="font-bold">Ops Center</span>
        </div>
        <Button variant="ghost" size="icon" onClick={toggleSidebar}>
          {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
      </header>

      {/* Sidebar Navigation */}
      <aside className={`
        fixed inset-y-0 left-0 z-40 w-64 border-r bg-muted/40 backdrop-blur transform transition-transform duration-200 ease-in-out md:translate-x-0 md:static md:flex flex-col
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="h-14 flex items-center px-6 border-b hidden md:flex">
          <ShieldAlert className="h-6 w-6 text-destructive mr-2" />
          <span className="font-bold text-lg tracking-tight">Ops Center</span>
        </div>
        
        <div className="flex-1 overflow-y-auto py-4">
          <nav className="grid gap-1 px-4">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname.startsWith(item.href)
              return (
                <Link
                  key={item.href}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center space-x-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    isActive 
                      ? "bg-primary text-primary-foreground" 
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </nav>
        </div>

        <div className="p-4 border-t bg-background/50">
          <div className="flex items-center justify-between">
            <div className="flex flex-col">
              <span className="text-sm font-medium">{user?.full_name || "Admin"}</span>
              <span className="text-xs text-muted-foreground capitalize">{user?.role || "admin"}</span>
            </div>
            <Button variant="outline" size="sm" onClick={logout} className="ml-4 shrink-0">
              <LogOut className="h-4 w-4 mr-2" />
              Log out
            </Button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col p-4 md:p-8 overflow-y-auto h-[calc(100vh-3.5rem)] md:h-screen w-full">
        {/* Overlay for mobile sidebar */}
        {sidebarOpen && (
          <div 
            className="fixed inset-0 z-30 bg-background/80 backdrop-blur-sm md:hidden" 
            onClick={() => setSidebarOpen(false)}
          />
        )}
        <Outlet />
      </main>
    </div>
  )
}
