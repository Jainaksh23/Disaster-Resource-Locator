import { useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { MapContainer, TileLayer, useMap } from "react-leaflet"
import L from 'leaflet'
import 'leaflet.heat'
import { AlertCircle, CheckCircle2, Clock, Users, Activity, Loader2, FileX } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card"
import { Badge } from "../components/ui/badge"
import { Button } from "../components/ui/button"
import { Skeleton } from "../components/ui/skeleton"
import { apiFetch } from "../api/client"
import ReportModal from "../components/report-modal"

// Heatmap Layer Component
function HeatmapLayer({ points }) {
  const map = useMap()
  
  useState(() => {
    if (points && points.length > 0) {
      const heatPoints = points.map(p => [p.latitude, p.longitude, p.severity_score * 10])
      const heat = L.heatLayer(heatPoints, { radius: 25, blur: 15, maxZoom: 17 })
      heat.addTo(map)
      return () => map.removeLayer(heat)
    }
  }, [map, points])
  
  return null
}

export default function Dashboard() {
  const queryClient = useQueryClient()
  const [selectedReport, setSelectedReport] = useState(null)

  // 1. Fetch Stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      return await apiFetch('/api/v1/dashboard/stats')
    }
  })

  // 2. Fetch Map Pins for Heatmap
  const { data: pins } = useQuery({
    queryKey: ['map-pins'],
    queryFn: async () => {
      return await apiFetch('/api/v1/dashboard/map-pins')
    }
  })

  // 3. Fetch Priority Queue (Reports)
  const { data: reportsData, isLoading: reportsLoading } = useQuery({
    queryKey: ['reports'],
    queryFn: async () => {
      // Sort normally handled by backend, we fetch page 1
      return await apiFetch('/api/v1/reports/')
    }
  })

  const reports = reportsData?.items || []
  
  // Sort reports by severity locally for the priority queue
  const sortedReports = [...reports].sort((a, b) => b.severity_score - a.severity_score)

  const getSeverityBadge = (score) => {
    if (score >= 8) return "destructive";
    if (score >= 4) return "warning";
    return "success";
  }

  return (
    <div className="flex flex-col space-y-6">
      
      {/* ── Stats Row ── */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="hover:border-primary/50 transition-colors">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold tracking-wide text-muted-foreground uppercase">Active Incidents</CardTitle>
            <Activity className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            {statsLoading ? <Skeleton className="h-8 w-20" /> : (
              <div className="text-3xl font-extrabold">{stats?.reports?.active || 0}</div>
            )}
          </CardContent>
        </Card>
        
        <Card className="hover:border-primary/50 transition-colors">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold tracking-wide text-muted-foreground uppercase">Total Resources</CardTitle>
            <Users className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            {statsLoading ? <Skeleton className="h-8 w-20" /> : (
              <div className="text-3xl font-extrabold">{stats?.resources?.total || 0}</div>
            )}
          </CardContent>
        </Card>
        
        <Card className="hover:border-primary/50 transition-colors">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold tracking-wide text-muted-foreground uppercase">Available Resources</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            {statsLoading ? <Skeleton className="h-8 w-20" /> : (
              <div className="text-3xl font-extrabold">{stats?.resources?.available || 0}</div>
            )}
          </CardContent>
        </Card>

        <Card className="hover:border-primary/50 transition-colors">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold tracking-wide text-muted-foreground uppercase">Resolved Incidents</CardTitle>
            <AlertCircle className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            {statsLoading ? <Skeleton className="h-8 w-20" /> : (
              <div className="text-3xl font-extrabold">{stats?.reports?.resolved || 0}</div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-7">
        
        {/* ── Priority Queue ── */}
        <Card className="md:col-span-4 flex flex-col">
          <CardHeader>
            <CardTitle className="text-xl font-bold">Live Priority Queue</CardTitle>
            <CardDescription>Sorted by AI-calculated severity score.</CardDescription>
          </CardHeader>
          <CardContent className="flex-1">
            {reportsLoading ? (
              <div className="space-y-4">
                <Skeleton className="h-16 w-full rounded-lg" />
                <Skeleton className="h-16 w-full rounded-lg" />
                <Skeleton className="h-16 w-full rounded-lg" />
              </div>
            ) : (
              <div className="space-y-3">
                {sortedReports.map(report => (
                  <div 
                    key={report.id} 
                    className="flex items-center justify-between p-4 border border-border/50 rounded-lg cursor-pointer hover:bg-muted/40 hover:shadow-sm transition-all"
                    onClick={() => setSelectedReport(report)}
                  >
                    <div className="flex flex-col space-y-1.5">
                      <div className="flex items-center space-x-3">
                        <Badge variant={getSeverityBadge(report.severity_score)}>
                          Severity {report.severity_score}
                        </Badge>
                        <span className="font-semibold text-base">{report.title}</span>
                      </div>
                      <span className="text-xs text-muted-foreground line-clamp-1">{report.description}</span>
                    </div>
                    <Badge variant="outline" className="ml-4 shrink-0 uppercase text-[10px] font-bold tracking-wider">
                      {report.status}
                    </Badge>
                  </div>
                ))}
                {sortedReports.length === 0 && (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-3">
                      <FileX className="h-6 w-6 text-muted-foreground" />
                    </div>
                    <p className="text-sm font-medium text-foreground">No reports in the queue</p>
                    <p className="text-xs text-muted-foreground mt-1">All incidents are currently resolved.</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* ── Heatmap ── */}
        <Card className="md:col-span-3">
          <CardHeader>
            <CardTitle>Incident Heatmap</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="h-[400px] w-full rounded-b-xl overflow-hidden border-t">
              <MapContainer 
                center={[0, 0]} 
                zoom={2} 
                className="h-full w-full"
                scrollWheelZoom={false}
              >
                <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
                {pins && <HeatmapLayer points={pins} />}
              </MapContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── Report Details Modal ── */}
      <ReportModal 
        report={selectedReport} 
        onClose={() => setSelectedReport(null)} 
      />

    </div>
  )
}
