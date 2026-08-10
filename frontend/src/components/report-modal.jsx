import { Loader2, MapPin, CheckCircle } from "lucide-react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { MapContainer, TileLayer, Marker } from "react-leaflet"
import L from "leaflet"
import { Badge } from "./ui/badge"
import { Button } from "./ui/button"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "./ui/card"
import { apiFetch } from "../api/client"

export default function ReportModal({ report, onClose }) {
  const queryClient = useQueryClient()

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
      onClose()
    }
  })

  if (!report) return null

  return (
    <div className="fixed inset-0 z-[999] flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
      <Card className="w-full max-w-2xl shadow-2xl relative max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <Badge variant={report.severity_score >= 8 ? "destructive" : "default"} className="mb-2">
                Severity {report.severity_score}
              </Badge>
              <CardTitle className="text-xl">{report.title}</CardTitle>
              <CardDescription className="mt-1">{report.location_name}</CardDescription>
            </div>
            <Button variant="ghost" size="icon" onClick={onClose}>
              &times;
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          
          <div className="flex flex-col md:flex-row gap-6">
            <div className="flex-1 space-y-6">
              <div>
                <h4 className="text-sm font-semibold mb-2">Description</h4>
                <p className="text-sm text-muted-foreground bg-accent p-3 rounded-md">
                  {report.description}
                </p>
              </div>

              <div>
                <h4 className="text-sm font-semibold mb-2">Current Status</h4>
                <div className="flex items-center space-x-2">
                  <Badge variant="outline" className="uppercase px-3 py-1 bg-secondary/50">
                    {report.status}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    Last updated: {new Date(report.updated_at).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Real-time Location Map */}
            {report.latitude && report.longitude && (
              <div className="flex-1">
                <h4 className="text-sm font-semibold mb-2">Real-time Location</h4>
                <div className="h-[200px] w-full rounded-md overflow-hidden border">
                  <MapContainer 
                    center={[report.latitude, report.longitude]} 
                    zoom={15} 
                    className="h-full w-full"
                  >
                    <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
                    <Marker position={[report.latitude, report.longitude]} />
                  </MapContainer>
                </div>
              </div>
            )}
          </div>

          {/* Gemini AI Extracted Data */}
          {report.structured_data && (
            <div>
              <h4 className="text-sm font-semibold mb-2">AI Extraction (Gemini)</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 border rounded-md">
                  <span className="text-xs text-muted-foreground">Injuries</span>
                  <p className="font-bold text-lg">{report.structured_data.injury_count ?? 'N/A'}</p>
                </div>
                <div className="p-3 border rounded-md">
                  <span className="text-xs text-muted-foreground">People Trapped</span>
                  <p className="font-bold text-lg text-destructive">{report.structured_data.people_trapped ?? 'N/A'}</p>
                </div>
                <div className="p-3 border rounded-md">
                  <span className="text-xs text-muted-foreground">Structural Damage</span>
                  <p className="font-bold text-lg">{report.structured_data.structural_damage ? 'Yes' : 'No'}</p>
                </div>
                <div className="p-3 border rounded-md">
                  <span className="text-xs text-muted-foreground">AI Confidence</span>
                  <p className="font-bold text-lg">
                    {report.structured_data.confidence_score 
                      ? `${(report.structured_data.confidence_score * 100).toFixed(0)}%` 
                      : 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* RAG Suggested Actions */}
          {report.suggested_actions?.length > 0 ? (
            <div>
              <h4 className="text-sm font-semibold mb-2">SOP Recommended Actions (RAG)</h4>
              <div className="space-y-2">
                {report.suggested_actions.map((action, idx) => (
                  <div key={idx} className="p-3 border rounded-md border-primary/20 bg-primary/5">
                    <h5 className="font-bold text-sm text-primary mb-1">{action.title}</h5>
                    <p className="text-xs text-muted-foreground">{action.content}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div>
              <h4 className="text-sm font-semibold mb-2">SOP Recommended Actions (RAG)</h4>
              <p className="text-xs text-muted-foreground italic bg-accent/50 p-3 rounded-md border">
                No SOP suggestions available.
              </p>
            </div>
          )}

        </CardContent>
        <CardFooter className="flex justify-end space-x-3 border-t pt-6 bg-muted/20">
          {report.status !== 'resolved' && report.status !== 'solved' && (
            <>
              {report.status !== 'contained' && (
                <Button 
                  variant="outline"
                  onClick={() => updateStatus.mutate({ id: report.id, status: 'contained' })}
                  disabled={updateStatus.isPending}
                >
                  {updateStatus.isPending ? <Loader2 className="animate-spin w-4 h-4 mr-2" /> : null}
                  Mark as Contained
                </Button>
              )}
              
              <Button 
                className="bg-green-600 hover:bg-green-700 text-white"
                onClick={() => updateStatus.mutate({ id: report.id, status: 'resolved' })}
                disabled={updateStatus.isPending}
              >
                {updateStatus.isPending ? <Loader2 className="animate-spin w-4 h-4 mr-2" /> : <CheckCircle className="w-4 h-4 mr-2" />}
                Mark as Solved
              </Button>
            </>
          )}
        </CardFooter>
      </Card>
    </div>
  )
}
