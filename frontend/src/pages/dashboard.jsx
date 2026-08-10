import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { MapContainer, TileLayer, useMap } from "react-leaflet"
import L from 'leaflet'
import 'leaflet.heat'
import { AlertCircle, CheckCircle2, Clock, Users, Activity, Loader2 } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card"
import { Badge } from "../components/ui/badge"
import { Button } from "../components/ui/button"
import { Skeleton } from "../components/ui/skeleton"
import { apiFetch } from "../api/client"

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

  // Status Update Mutation
  const updateStatus = useMutation({
    mutationFn: async ({ id, status }) => {
      return await apiFetch(`/api/v1/reports/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status })
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['reports'])
      queryClient.invalidateQueries(['dashboard-stats'])
      setSelectedReport(null)
    }
  })

  const reports = reportsData?.items || []
  
  // Sort reports by severity locally for the priority queue
  const sortedReports = [...reports].sort((a, b) => b.severity_score - a.severity_score)

  return (
    <div className="flex flex-col space-y-6">
      
      {/* ── Stats Row ── */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Incidents</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {statsLoading ? <Skeleton className="h-8 w-20" /> : (
              <div className="text-2xl font-bold">{stats?.reports?.active || 0}</div>
            )}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Resources</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {statsLoading ? <Skeleton className="h-8 w-20" /> : (
              <div className="text-2xl font-bold">{stats?.resources?.total || 0}</div>
            )}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Available Resources</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            {statsLoading ? <Skeleton className="h-8 w-20" /> : (
              <div className="text-2xl font-bold">{stats?.resources?.available || 0}</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resolved Incidents</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {statsLoading ? <Skeleton className="h-8 w-20" /> : (
              <div className="text-2xl font-bold">{stats?.reports?.resolved || 0}</div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-7">
        
        {/* ── Priority Queue ── */}
        <Card className="md:col-span-4">
          <CardHeader>
            <CardTitle>Live Priority Queue</CardTitle>
            <CardDescription>Sorted by AI-calculated severity score.</CardDescription>
          </CardHeader>
          <CardContent>
            {reportsLoading ? (
              <div className="space-y-4">
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
              </div>
            ) : (
              <div className="space-y-4">
                {sortedReports.map(report => (
                  <div 
                    key={report.id} 
                    className="flex items-center justify-between p-4 border rounded-lg cursor-pointer hover:bg-accent transition-colors"
                    onClick={() => setSelectedReport(report)}
                  >
                    <div className="flex flex-col space-y-1">
                      <div className="flex items-center space-x-2">
                        <Badge variant={report.severity_score >= 8 ? "destructive" : "default"}>
                          Severity {report.severity_score}
                        </Badge>
                        <span className="font-semibold text-sm">{report.title}</span>
                      </div>
                      <span className="text-xs text-muted-foreground line-clamp-1">{report.description}</span>
                    </div>
                    <Badge variant="outline" className="ml-4 shrink-0 uppercase text-[10px]">
                      {report.status}
                    </Badge>
                  </div>
                ))}
                {sortedReports.length === 0 && (
                  <div className="text-center text-muted-foreground py-8 text-sm">No reports in the queue.</div>
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
      {selectedReport && (
        <div className="fixed inset-0 z-[999] flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
          <Card className="w-full max-w-2xl shadow-2xl relative max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <Badge variant="destructive" className="mb-2">Severity {selectedReport.severity_score}</Badge>
                  <CardTitle className="text-xl">{selectedReport.title}</CardTitle>
                  <CardDescription className="mt-1">{selectedReport.location_name}</CardDescription>
                </div>
                <Button variant="ghost" size="icon" onClick={() => setSelectedReport(null)}>
                  &times;
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              
              <div>
                <h4 className="text-sm font-semibold mb-2">Description</h4>
                <p className="text-sm text-muted-foreground bg-accent p-3 rounded-md">
                  {selectedReport.description}
                </p>
              </div>

              {/* Gemini AI Extracted Data */}
              {selectedReport.structured_data && (
                <div>
                  <h4 className="text-sm font-semibold mb-2">AI Extraction (Gemini)</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 border rounded-md">
                      <span className="text-xs text-muted-foreground">Injuries</span>
                      <p className="font-bold text-lg">{selectedReport.structured_data.injury_count ?? 'N/A'}</p>
                    </div>
                    <div className="p-3 border rounded-md">
                      <span className="text-xs text-muted-foreground">People Trapped</span>
                      <p className="font-bold text-lg text-destructive">{selectedReport.structured_data.people_trapped ?? 'N/A'}</p>
                    </div>
                    <div className="p-3 border rounded-md">
                      <span className="text-xs text-muted-foreground">Structural Damage</span>
                      <p className="font-bold text-lg">{selectedReport.structured_data.structural_damage ? 'Yes' : 'No'}</p>
                    </div>
                    <div className="p-3 border rounded-md">
                      <span className="text-xs text-muted-foreground">AI Confidence</span>
                      <p className="font-bold text-lg">
                        {selectedReport.structured_data.confidence_score 
                          ? `${(selectedReport.structured_data.confidence_score * 100).toFixed(0)}%` 
                          : 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* RAG Suggested Actions */}
              {selectedReport.suggested_actions !== undefined && (
                <div>
                  <h4 className="text-sm font-semibold mb-2">SOP Recommended Actions (RAG)</h4>
                  {selectedReport.suggested_actions.length > 0 ? (
                    <div className="space-y-2">
                      {selectedReport.suggested_actions.map((action, idx) => (
                        <div key={idx} className="p-3 border rounded-md border-primary/20 bg-primary/5">
                          <h5 className="font-bold text-sm text-primary mb-1">{action.title}</h5>
                          <p className="text-xs text-muted-foreground">{action.content}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground italic bg-accent/50 p-3 rounded-md border">
                      No SOP suggestions available (RAG disabled).
                    </p>
                  )}
                </div>
              )}

            </CardContent>
            <CardFooter className="flex justify-end space-x-2 border-t pt-6">
              {selectedReport.status === 'active' && (
                <Button 
                  onClick={() => updateStatus.mutate({ id: selectedReport.id, status: 'contained' })}
                  disabled={updateStatus.isPending}
                >
                  {updateStatus.isPending ? <Loader2 className="animate-spin w-4 h-4" /> : 'Mark as Contained'}
                </Button>
              )}
              {selectedReport.status !== 'resolved' && (
                <Button 
                  variant="secondary"
                  onClick={() => updateStatus.mutate({ id: selectedReport.id, status: 'resolved' })}
                  disabled={updateStatus.isPending}
                >
                  Mark as Resolved
                </Button>
              )}
            </CardFooter>
          </Card>
        </div>
      )}

    </div>
  )
}
