import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Loader2, Search, FileX } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card"
import { Badge } from "../components/ui/badge"
import { Input } from "../components/ui/input"
import { Skeleton } from "../components/ui/skeleton"
import { apiFetch } from "../api/client"
import ReportModal from "../components/report-modal"

export default function Reports() {
  const [selectedReport, setSelectedReport] = useState(null)
  const [statusFilter, setStatusFilter] = useState("all")

  // Fetch Reports
  const { data: reportsData, isLoading } = useQuery({
    queryKey: ['reports', statusFilter],
    queryFn: async () => {
      const url = statusFilter === "all" 
        ? '/api/v1/reports/' 
        : `/api/v1/reports/?status=${statusFilter}`
      return await apiFetch(url)
    }
  })

  const reports = reportsData?.items || []

  const getSeverityBadge = (score) => {
    if (score >= 8) return "destructive";
    if (score >= 4) return "warning";
    return "success";
  }

  return (
    <div className="flex flex-col space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight">All Reports</h2>
          <p className="text-muted-foreground mt-1">Manage and track emergency incident reports.</p>
        </div>
        <div className="flex items-center space-x-2 w-full md:w-auto">
          <select 
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="flex h-10 w-full md:w-[200px] items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-shadow"
          >
            <option value="all">All Statuses</option>
            <option value="active">Active</option>
            <option value="contained">Contained</option>
            <option value="resolved">Resolved</option>
            <option value="false_alarm">False Alarm</option>
          </select>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto w-full custom-scrollbar">
            <table className="w-full text-sm text-left whitespace-nowrap md:whitespace-normal">
              <thead className="text-xs text-muted-foreground font-semibold tracking-wider uppercase bg-muted/50 border-b">
                <tr>
                  <th className="px-6 py-4 font-semibold">Title & Location</th>
                  <th className="px-6 py-4 font-semibold">Category</th>
                  <th className="px-6 py-4 font-semibold">Severity</th>
                  <th className="px-6 py-4 font-semibold">Status</th>
                  <th className="px-6 py-4 font-semibold text-right">Date Reported</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50">
                {isLoading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i}>
                      <td className="px-6 py-4"><Skeleton className="h-4 w-[250px]" /></td>
                      <td className="px-6 py-4"><Skeleton className="h-4 w-[80px]" /></td>
                      <td className="px-6 py-4"><Skeleton className="h-4 w-[60px]" /></td>
                      <td className="px-6 py-4"><Skeleton className="h-4 w-[80px]" /></td>
                      <td className="px-6 py-4"><Skeleton className="h-4 w-[100px] ml-auto" /></td>
                    </tr>
                  ))
                ) : reports.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-16 text-center">
                      <div className="flex flex-col items-center justify-center space-y-3">
                        <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center">
                          <FileX className="h-6 w-6 text-muted-foreground" />
                        </div>
                        <p className="text-lg font-medium text-foreground">No reports found</p>
                        <p className="text-sm text-muted-foreground">Try adjusting your filters or check back later.</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  reports.map((report) => (
                    <tr 
                      key={report.id} 
                      className="hover:bg-muted/40 cursor-pointer transition-colors"
                      onClick={() => setSelectedReport(report)}
                    >
                      <td className="px-6 py-4">
                        <div className="font-semibold text-foreground text-base">{report.title}</div>
                        <div className="text-xs text-muted-foreground mt-1 line-clamp-1">
                          {report.location_name}
                        </div>
                      </td>
                      <td className="px-6 py-4 capitalize font-medium text-muted-foreground">
                        {report.category}
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant={getSeverityBadge(report.severity_score)}>
                          Severity {report.severity_score}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 uppercase text-[10px] font-bold tracking-wider">
                        <Badge variant="outline">{report.status}</Badge>
                      </td>
                      <td className="px-6 py-4 text-right text-muted-foreground text-xs font-medium">
                        {new Date(report.created_at).toLocaleDateString(undefined, {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric'
                        })}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <ReportModal 
        report={selectedReport} 
        onClose={() => setSelectedReport(null)} 
      />
    </div>
  )
}
