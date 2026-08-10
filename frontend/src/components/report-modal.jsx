import { Loader2 } from "lucide-react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
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
          
          <div>
            <h4 className="text-sm font-semibold mb-2">Description</h4>
            <p className="text-sm text-muted-foreground bg-accent p-3 rounded-md">
              {report.description}
            </p>
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
          {report.suggested_actions !== undefined && (
            <div>
              <h4 className="text-sm font-semibold mb-2">SOP Recommended Actions (RAG)</h4>
              {report.suggested_actions.length > 0 ? (
                <div className="space-y-2">
                  {report.suggested_actions.map((action, idx) => (
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
          {report.status === 'active' && (
            <Button 
              onClick={() => updateStatus.mutate({ id: report.id, status: 'contained' })}
              disabled={updateStatus.isPending}
            >
              {updateStatus.isPending ? <Loader2 className="animate-spin w-4 h-4" /> : 'Mark as Contained'}
            </Button>
          )}
          {report.status !== 'resolved' && (
            <Button 
              variant="secondary"
              onClick={() => updateStatus.mutate({ id: report.id, status: 'resolved' })}
              disabled={updateStatus.isPending}
            >
              Mark as Resolved
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  )
}
