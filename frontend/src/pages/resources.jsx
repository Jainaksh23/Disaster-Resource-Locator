import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Loader2, Plus, Edit, Trash2, PackageX } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card"
import { Badge } from "../components/ui/badge"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Skeleton } from "../components/ui/skeleton"
import { apiFetch } from "../api/client"

function ResourceModal({ resource, onClose, mode = "add" }) {
  const queryClient = useQueryClient()
  
  const [formData, setFormData] = useState(
    resource || {
      name: "",
      resource_type: "hospital",
      capacity: 0,
      status: "available",
      location_name: "",
      latitude: "",
      longitude: "",
      contact: ""
    }
  )

  const mutation = useMutation({
    mutationFn: async (data) => {
      // Clean up empty lat/long to be null for the backend
      const payload = { ...data }
      payload.capacity = parseInt(payload.capacity, 10) || 0
      if (payload.latitude === "") delete payload.latitude
      else payload.latitude = parseFloat(payload.latitude)
      
      if (payload.longitude === "") delete payload.longitude
      else payload.longitude = parseFloat(payload.longitude)

      if (mode === "add") {
        return await apiFetch('/api/v1/resources/', {
          method: 'POST',
          body: JSON.stringify(payload)
        })
      } else {
        return await apiFetch(`/api/v1/resources/${resource.id}`, {
          method: 'PATCH',
          body: JSON.stringify(payload)
        })
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['resources'])
      queryClient.invalidateQueries(['dashboard-stats'])
      onClose()
    }
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    mutation.mutate(formData)
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  return (
    <div className="fixed inset-0 z-[999] flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
      <Card className="w-full max-w-lg shadow-2xl relative max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-xl">{mode === "add" ? "Add New Resource" : "Edit Resource"}</CardTitle>
            </div>
            <Button variant="ghost" size="icon" onClick={onClose} disabled={mutation.isPending}>
              &times;
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <form id="resource-form" onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2 md:col-span-2">
                <label className="text-sm font-medium">Name</label>
                <Input required name="name" value={formData.name} onChange={handleChange} />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Category</label>
                <select 
                  name="resource_type" 
                  value={formData.resource_type} 
                  onChange={handleChange}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background transition-shadow"
                >
                  <option value="hospital">Hospital</option>
                  <option value="shelter">Shelter</option>
                  <option value="bloodbank">Blood Bank</option>
                  <option value="ngo">NGO</option>
                  <option value="fire_station">Fire Station</option>
                  <option value="police_station">Police Station</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Status</label>
                <select 
                  name="status" 
                  value={formData.status} 
                  onChange={handleChange}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background transition-shadow"
                >
                  <option value="available">Available</option>
                  <option value="unavailable">Unavailable</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Capacity</label>
                <Input type="number" required min="0" name="capacity" value={formData.capacity} onChange={handleChange} />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Contact</label>
                <Input type="text" name="contact" value={formData.contact} onChange={handleChange} />
              </div>

              <div className="space-y-2 md:col-span-2">
                <label className="text-sm font-medium">Location Name</label>
                <Input required name="location_name" value={formData.location_name} onChange={handleChange} placeholder="e.g. Connaught Place, Delhi" />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Latitude (Optional)</label>
                <Input type="number" step="any" name="latitude" value={formData.latitude} onChange={handleChange} />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Longitude (Optional)</label>
                <Input type="number" step="any" name="longitude" value={formData.longitude} onChange={handleChange} />
              </div>
            </div>
            
            {mutation.isError && (
              <div className="text-sm text-destructive mt-2">
                {mutation.error.message || "Failed to save resource"}
              </div>
            )}
          </form>
        </CardContent>
        <div className="flex justify-end space-x-2 p-6 pt-0">
          <Button variant="outline" onClick={onClose} disabled={mutation.isPending}>
            Cancel
          </Button>
          <Button type="submit" form="resource-form" disabled={mutation.isPending}>
            {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {mode === "add" ? "Add Resource" : "Save Changes"}
          </Button>
        </div>
      </Card>
    </div>
  )
}

export default function Resources() {
  const queryClient = useQueryClient()
  const [modalState, setModalState] = useState({ isOpen: false, mode: 'add', resource: null })

  // Fetch Resources
  const { data: resourcesData, isLoading } = useQuery({
    queryKey: ['resources'],
    queryFn: async () => {
      return await apiFetch('/api/v1/resources/?page_size=100')
    }
  })

  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      return await apiFetch(`/api/v1/resources/${id}`, { method: 'DELETE' })
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['resources'])
      queryClient.invalidateQueries(['dashboard-stats'])
    }
  })

  const handleDelete = (id) => {
    if (window.confirm("Are you sure you want to delete this resource?")) {
      deleteMutation.mutate(id)
    }
  }

  const resources = resourcesData?.items || []

  return (
    <div className="flex flex-col space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight">Manage Resources</h2>
          <p className="text-muted-foreground mt-1">Add, edit, or remove emergency resources.</p>
        </div>
        <Button className="w-full md:w-auto" onClick={() => setModalState({ isOpen: true, mode: 'add', resource: null })}>
          <Plus className="mr-2 h-4 w-4" /> Add New Resource
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto w-full custom-scrollbar">
            <table className="w-full text-sm text-left whitespace-nowrap md:whitespace-normal">
              <thead className="text-xs text-muted-foreground font-semibold tracking-wider uppercase bg-muted/50 border-b">
                <tr>
                  <th className="px-6 py-4 font-semibold">Name & Location</th>
                  <th className="px-6 py-4 font-semibold">Category</th>
                  <th className="px-6 py-4 font-semibold">Capacity</th>
                  <th className="px-6 py-4 font-semibold">Status</th>
                  <th className="px-6 py-4 font-semibold">Contact</th>
                  <th className="px-6 py-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50">
                {isLoading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i}>
                      <td className="px-6 py-4"><Skeleton className="h-4 w-[200px]" /></td>
                      <td className="px-6 py-4"><Skeleton className="h-4 w-[80px]" /></td>
                      <td className="px-6 py-4"><Skeleton className="h-4 w-[60px]" /></td>
                      <td className="px-6 py-4"><Skeleton className="h-4 w-[80px]" /></td>
                      <td className="px-6 py-4"><Skeleton className="h-4 w-[100px]" /></td>
                      <td className="px-6 py-4"><Skeleton className="h-8 w-[60px] ml-auto" /></td>
                    </tr>
                  ))
                ) : resources.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-16 text-center">
                      <div className="flex flex-col items-center justify-center space-y-3">
                        <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center">
                          <PackageX className="h-6 w-6 text-muted-foreground" />
                        </div>
                        <p className="text-lg font-medium text-foreground">No resources found</p>
                        <p className="text-sm text-muted-foreground">Click the 'Add New Resource' button to add one.</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  resources.map((resource) => (
                    <tr key={resource.id} className="hover:bg-muted/40 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-semibold text-foreground text-base">{resource.name}</div>
                        <div className="text-xs text-muted-foreground mt-1 line-clamp-1">
                          {resource.location_name}
                        </div>
                      </td>
                      <td className="px-6 py-4 capitalize font-medium text-muted-foreground">
                        {resource.resource_type}
                      </td>
                      <td className="px-6 py-4 font-medium">
                        {resource.capacity}
                      </td>
                      <td className="px-6 py-4 uppercase text-[10px] font-bold tracking-wider">
                        <Badge variant={resource.status === 'available' ? 'success' : 'secondary'}>
                          {resource.status}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 text-muted-foreground">
                        {resource.contact || "N/A"}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex justify-end space-x-2">
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            onClick={() => setModalState({ isOpen: true, mode: 'edit', resource })}
                          >
                            <Edit className="h-4 w-4 text-muted-foreground hover:text-foreground" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                            onClick={() => handleDelete(resource.id)}
                            disabled={deleteMutation.isPending}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {modalState.isOpen && (
        <ResourceModal 
          mode={modalState.mode}
          resource={modalState.resource}
          onClose={() => setModalState({ isOpen: false, mode: 'add', resource: null })}
        />
      )}
    </div>
  )
}
