import { useEffect, useState, useRef } from 'react'
import { MapPin, RefreshCw, ExternalLink } from 'lucide-react'
import { disasterApi } from '../api'
import { Link } from 'react-router-dom'
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

// Severity colors
const SEVERITY_COLORS = {
  P1: { bg: 'bg-red-500', hex: '#DC2626', text: 'text-red-400' },
  P2: { bg: 'bg-orange-500', hex: '#F97316', text: 'text-orange-400' },
  P3: { bg: 'bg-yellow-500', hex: '#EAB308', text: 'text-yellow-400' },
  P4: { bg: 'bg-green-500', hex: '#22C55E', text: 'text-green-400' },
}

// Subcategory icons
const SUBCATEGORY_ICONS = {
  landslide: '⛰️', flood: '🌊', cyclone: '🌀', earthquake: '📳', storm_damage: '⛈️',
  broken_power_line: '⚡', pothole: '🕳️', road_damage: '🚧', water_main_break: '💧', collapsed_structure: '🏚️',
  fallen_tree: '🌳', vehicle_accident: '🚗', debris: '🪨', blocked_drain: '🚰', construction_hazard: '🏗️',
}

// Kerala center and bounds
const KERALA_CENTER = [10.5, 76.3]
const KERALA_BOUNDS = [[8.2, 74.8], [12.8, 77.4]]

// Component to handle map invalidation on resize
function MapResizer() {
  const map = useMap()
  useEffect(() => {
    setTimeout(() => map.invalidateSize(), 100)
  }, [map])
  return null
}

export default function DashboardMap({ newIncident }) {
  const [markers, setMarkers] = useState([])
  const [loading, setLoading] = useState(true)
  const mapRef = useRef(null)
  
  const loadMarkers = async () => {
    try {
      const { data } = await disasterApi.getMapData()
      setMarkers(data.markers || [])
    } catch (err) {
      console.error('Failed to load map data:', err)
    } finally {
      setLoading(false)
    }
  }
  
  useEffect(() => {
    loadMarkers()
  }, [])
  
  // Reload when new incident is reported
  useEffect(() => {
    if (newIncident) {
      loadMarkers()
    }
  }, [newIncident])
  
  // Count by severity
  const severityCounts = markers.reduce((acc, m) => {
    acc[m.severity] = (acc[m.severity] || 0) + 1
    return acc
  }, {})
  
  return (
    <div className="bg-black/60 backdrop-blur-2xl border border-white/10 rounded-2xl flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-white/10 bg-black/20 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
            <MapPin className="text-blue-400" size={20} />
          </div>
          <div>
            <h3 className="font-bold text-white text-sm">Live Incidents</h3>
            <p className="text-xs text-slate-400">Kerala Infrastructure Map</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xl font-bold text-white">{markers.length}</span>
          <button
            onClick={loadMarkers}
            className="p-2 hover:bg-white/5 rounded-lg text-slate-400 hover:text-white transition-colors"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>
      
      {/* Leaflet Map */}
      <div className="flex-1 relative min-h-0">
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-900/50">
            <RefreshCw className="animate-spin text-slate-500" size={24} />
          </div>
        ) : (
          <MapContainer
            ref={mapRef}
            center={KERALA_CENTER}
            zoom={7}
            maxBounds={KERALA_BOUNDS}
            minZoom={6}
            maxZoom={12}
            style={{ height: '100%', width: '100%', background: '#0a1525' }}
            zoomControl={false}
            attributionControl={false}
          >
            <MapResizer />
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />
            
            {markers.map((marker) => {
              const severity = SEVERITY_COLORS[marker.severity] || SEVERITY_COLORS.P3
              const isPriority = marker.severity === 'P1' || marker.severity === 'P2'
              
              return (
                <CircleMarker
                  key={marker.id}
                  center={[marker.latitude, marker.longitude]}
                  radius={isPriority ? 8 : 6}
                  pathOptions={{
                    fillColor: severity.hex,
                    fillOpacity: 0.8,
                    color: 'white',
                    weight: 1,
                  }}
                >
                  <Popup className="incident-popup">
                    <div className="text-xs">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-lg">{SUBCATEGORY_ICONS[marker.subcategory] || '⚠️'}</span>
                        <span className="font-bold capitalize">{marker.subcategory?.replace(/_/g, ' ')}</span>
                      </div>
                      <div className="text-slate-400">
                        {marker.district} • {marker.severity}
                      </div>
                    </div>
                  </Popup>
                </CircleMarker>
              )
            })}
          </MapContainer>
        )}
      </div>
      
      {/* Footer Stats */}
      <div className="p-3 border-t border-white/10 bg-black/20">
        <div className="flex items-center justify-between mb-2">
          <div className="flex gap-2">
            {['P1', 'P2', 'P3', 'P4'].map(level => (
              <div key={level} className="flex items-center gap-1">
                <span className={`w-2 h-2 rounded-full ${SEVERITY_COLORS[level].bg}`} />
                <span className="text-[10px] text-slate-400">
                  {severityCounts[level] || 0}
                </span>
              </div>
            ))}
          </div>
        </div>
        
        <Link
          to="/disaster"
          className="flex items-center justify-center gap-2 w-full py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg text-xs font-medium transition-colors"
        >
          <ExternalLink size={12} />
          View Full Map
        </Link>
      </div>
    </div>
  )
}
