import { useState, useRef, useEffect } from "react"
import { useMutation } from "@tanstack/react-query"
import { MapContainer, TileLayer, Marker, useMapEvents } from "react-leaflet"
import { Mic, MicOff, MapPin, Send, Loader2 } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "../components/ui/card"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { apiFetch } from "../api/client"
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

// Fix default marker icon in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

function LocationMarker({ position, setPosition }) {
  useMapEvents({
    click(e) {
      setPosition(e.latlng)
    },
  })
  return position === null ? null : <Marker position={position} />
}

export default function Report() {
  const [title, setTitle] = useState("")
  const [category, setCategory] = useState("")
  const [description, setDescription] = useState("")
  const [locationName, setLocationName] = useState("")
  const [position, setPosition] = useState(null)
  
  const [isListening, setIsListening] = useState(false)
  const recognitionRef = useRef(null)

  useEffect(() => {
    // Initialize Web Speech API
    if ('webkitSpeechRecognition' in window) {
      const SpeechRecognition = window.webkitSpeechRecognition
      const recognition = new SpeechRecognition()
      recognition.continuous = true
      recognition.interimResults = true
      
      recognition.onresult = (event) => {
        let finalTranscript = ""
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript + " "
          }
        }
        if (finalTranscript) {
          setDescription(prev => (prev + " " + finalTranscript).trim())
        }
      }
      
      recognition.onend = () => {
        setIsListening(false)
      }
      
      recognitionRef.current = recognition
    }
  }, [])

  const toggleListen = () => {
    if (isListening) {
      recognitionRef.current?.stop()
      setIsListening(false)
    } else {
      recognitionRef.current?.start()
      setIsListening(true)
    }
  }

  const handleGetLocation = () => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition((pos) => {
        setPosition({ lat: pos.coords.latitude, lng: pos.coords.longitude })
      })
    }
  }

  const submitMutation = useMutation({
    mutationFn: async (data) => {
      return await apiFetch('/api/v1/reports/', {
        method: 'POST',
        body: JSON.stringify(data)
      })
    }
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    submitMutation.mutate({
      title,
      category,
      description,
      location_name: locationName || "Unknown Location",
      latitude: position?.lat,
      longitude: position?.lng
    })
  }

  return (
    <div className="max-w-3xl mx-auto w-full">
      <Card>
        <CardHeader>
          <CardTitle>File Emergency Report</CardTitle>
          <CardDescription>
            Report an ongoing disaster or emergency. AI will automatically prioritize the report and dispatch resources.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            
            {/* Title */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Incident Title</label>
              <Input 
                required 
                placeholder="e.g., Major flood on Main Street" 
                value={title} 
                onChange={e => setTitle(e.target.value)} 
              />
            </div>

            {/* Category */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Category</label>
              <select
                required
                value={category}
                onChange={e => setCategory(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                <option value="" disabled>Select a category</option>
                <option value="fire">Fire</option>
                <option value="flood">Flood</option>
                <option value="medical">Medical</option>
                <option value="collapse">Collapse</option>
                <option value="other">Other</option>
              </select>
            </div>

            {/* Description & Voice */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="text-sm font-medium">Description</label>
                <Button 
                  type="button" 
                  variant={isListening ? "destructive" : "secondary"} 
                  size="sm" 
                  onClick={toggleListen}
                >
                  {isListening ? <MicOff className="w-4 h-4 mr-2" /> : <Mic className="w-4 h-4 mr-2" />}
                  {isListening ? "Stop Dictation" : "Dictate"}
                </Button>
              </div>
              <textarea 
                required
                className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 min-h-[120px]"
                placeholder="Describe what is happening, who is injured, and any structural damage..."
                value={description}
                onChange={e => setDescription(e.target.value)}
              />
            </div>

            {/* Location */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Location</label>
              <div className="flex space-x-2">
                <Input 
                  placeholder="Address or landmark" 
                  value={locationName} 
                  onChange={e => setLocationName(e.target.value)} 
                />
                <Button type="button" variant="outline" onClick={handleGetLocation}>
                  <MapPin className="w-4 h-4 mr-2" /> Locate Me
                </Button>
              </div>
            </div>

            {/* Map Pin */}
            <div className="h-[300px] rounded-md overflow-hidden border">
              <MapContainer 
                center={position || [0, 0]} 
                zoom={position ? 15 : 2} 
                scrollWheelZoom={false} 
                className="h-full w-full"
              >
                <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                <LocationMarker position={position} setPosition={setPosition} />
              </MapContainer>
            </div>

            {/* Status Feedback */}
            {submitMutation.isSuccess && (
              <div className="p-4 bg-green-500/15 text-green-500 rounded-md text-sm border border-green-500/30">
                Report submitted successfully! Emergency responders have been notified.
              </div>
            )}
            {submitMutation.isError && (
              <div className="p-4 bg-destructive/15 text-destructive rounded-md text-sm border border-destructive/30">
                Failed to submit report. Please try again.
              </div>
            )}

            <Button 
              type="submit" 
              className="w-full" 
              disabled={submitMutation.isPending}
            >
              {submitMutation.isPending ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Submitting...</>
              ) : (
                <><Send className="w-4 h-4 mr-2" /> Submit Emergency Report</>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
