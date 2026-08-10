import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet"
import { Card } from "../components/ui/card"
import { Badge } from "../components/ui/badge"
import { Input } from "../components/ui/input"
import { apiFetch } from "../api/client"
import 'leaflet/dist/leaflet.css'

export default function MapPage() {
  const [filterType, setFilterType] = useState("all")

  // Fetch resources
  const { data: resourcesData, isLoading } = useQuery({
    queryKey: ['resources'],
    queryFn: async () => {
      return await apiFetch('/api/v1/resources/')
    }
  })

  // Fetch active reports for pins
  const { data: pinsData } = useQuery({
    queryKey: ['map-pins'],
    queryFn: async () => {
      return await apiFetch('/api/v1/dashboard/map-pins')
    }
  })

  const resources = resourcesData?.items || []
  const pins = pinsData || []

  const filteredResources = filterType === "all" 
    ? resources 
    : resources.filter(r => r.resource_type === filterType)

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] w-full relative rounded-xl overflow-hidden border">
      {/* Map Overlay Controls */}
      <div className="absolute top-4 left-4 z-[400] flex flex-col space-y-2 bg-background/90 backdrop-blur p-4 rounded-lg border shadow-lg w-64">
        <h3 className="font-semibold text-sm mb-2">Resource Filters</h3>
        
        <div className="flex flex-wrap gap-2">
          {["all", "hospitals", "shelters", "bloodbanks", "NGOs"].map(type => (
            <Badge 
              key={type}
              variant={filterType === type ? "default" : "secondary"}
              className="cursor-pointer"
              onClick={() => setFilterType(type)}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </Badge>
          ))}
        </div>
      </div>

      <MapContainer 
        center={[0, 0]} 
        zoom={2} 
        className="h-full w-full"
      >
        <TileLayer 
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {/* Resource Markers */}
        {filteredResources.map(res => (
          <Marker key={res.id} position={[res.latitude, res.longitude]}>
            <Popup>
              <div className="font-sans text-foreground">
                <h4 className="font-bold text-sm">{res.name}</h4>
                <p className="text-xs text-muted-foreground capitalize">{res.resource_type}</p>
                <div className="mt-2 text-xs space-y-1">
                  <p><strong>Capacity:</strong> {res.capacity || 'Unknown'}</p>
                  <p><strong>Contact:</strong> {res.contact || 'N/A'}</p>
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Incident Pins */}
        {pins.map(pin => (
          <Marker key={pin.id} position={[pin.latitude, pin.longitude]}>
             <Popup>
              <div className="font-sans text-foreground">
                <Badge variant="destructive" className="mb-2 uppercase text-[10px]">{pin.category}</Badge>
                <h4 className="font-bold text-sm">{pin.title}</h4>
                <p className="text-xs mt-1">Severity: {pin.severity_score}/10</p>
                <p className="text-xs text-muted-foreground">{pin.location_name}</p>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  )
}
