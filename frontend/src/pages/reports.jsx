import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Loader2, Search } from "lucide-react"

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

  return (
    <div className="flex flex-col space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">All Reports</h2>
          <p className="text-muted-foreground">Manage and track emergency incident reports.</p>
        </div>
        <div className="flex items-center space-x-2">
          <select 
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
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
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-muted-foreground uppercase bg-muted/50 border-b">
                <tr>
                  <th className="px-6 py-4 font-medium">Title & Location</th>
                  <th className="px-6 py-4 font-medium">Category</th>
                  <th className="px-6 py-4 font-medium">Severity</th>
                  <th className="px-6 py-4 font-medium">Status</th>
                  <th className="px-6 py-4 font-medium text-right">Date Reported</th>
                </tr>
              </thead>
              <tbody className="divide-y">
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
                    <td colSpan={5} className="px-6 py-12 text-center text-muted-foreground">
                      No reports found.
                    </td>
                  </tr>
                ) : (
                  reports.map((report) => (
                    <tr 
                      key={report.id} 
                      className="hover:bg-accent/50 cursor-pointer transition-colors"
                      onClick={() => setSelectedReport(report)}
                    >
                      <td className="px-6 py-4">
                        <div className="font-medium text-foreground">{report.title}</div>
                        <div className="text-xs text-muted-foreground mt-1 line-clamp-1">
                          {report.location_name}
                        </div>
                      </td>
                      <td className="px-6 py-4 capitalize">
                        {report.category}
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant={report.severity_score >= 8 ? "destructive" : "default"}>
                          {report.severity_score}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 uppercase text-[10px]">
                        <Badge variant="outline">{report.status}</Badge>
                      </td>
                      <td className="px-6 py-4 text-right text-muted-foreground">
                        {new Date(report.created_at).toLocaleDateString()}
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
