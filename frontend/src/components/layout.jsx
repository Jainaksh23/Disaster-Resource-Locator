import { Link, Outlet } from "react-router-dom"
import { ShieldAlert, Map, LayoutDashboard, Menu } from "lucide-react"
import { useAuth } from "../context/AuthContext"
import { Button } from "./ui/button"

export default function CitizenLayout() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-background dark flex flex-col">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center px-4 md:px-8">
          <div className="mr-4 flex">
            <Link to="/report" className="mr-6 flex items-center space-x-2">
              <ShieldAlert className="h-6 w-6 text-destructive" />
              <span className="font-bold sm:inline-block">Emergency Portal</span>
            </Link>
            <nav className="flex items-center space-x-6 text-sm font-medium">
              <Link
                to="/map"
                className="transition-colors hover:text-foreground/80 text-foreground/60"
              >
                Map
              </Link>
              <Link
                to="/report"
                className="transition-colors hover:text-foreground/80 text-foreground/60"
              >
                Report Incident
              </Link>
            </nav>
          </div>
          <div className="ml-auto flex items-center space-x-4">
            <span className="text-sm text-muted-foreground hidden md:inline-block">
              {user?.full_name || user?.email}
            </span>
            <Button variant="outline" size="sm" onClick={logout}>
              Log out
            </Button>
          </div>
        </div>
      </header>
      <main className="flex-1 flex flex-col p-4 md:p-8">
        <Outlet />
      </main>
    </div>
  )
}
