import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

// Severity colors
const SEVERITY_COLORS = {
  P1: { bg: 'bg-red-500', border: 'border-red-500', text: 'text-red-400', hex: '#DC2626' },
  P2: { bg: 'bg-orange-500', border: 'border-orange-500', text: 'text-orange-400', hex: '#F97316' },
  P3: { bg: 'bg-yellow-500', border: 'border-yellow-500', text: 'text-yellow-400', hex: '#EAB308' },
  P4: { bg: 'bg-green-500', border: 'border-green-500', text: 'text-green-400', hex: '#22C55E' },
}

// Subcategory icons/emojis
const SUBCATEGORY_ICONS = {
  landslide: '⛰️',
  flood: '🌊',
  cyclone: '🌀',
  earthquake: '📳',
  storm_damage: '⛈️',
  broken_power_line: '⚡',
  pothole: '🕳️',
  road_damage: '🚧',
  water_main_break: '💧',
  collapsed_structure: '🏚️',
  fallen_tree: '🌳',
  vehicle_accident: '🚗',
  debris: '🪨',
  blocked_drain: '🚰',
  construction_hazard: '🏗️',
}

// Kerala center and bounds
const KERALA_CENTER = [10.5, 76.3]
const KERALA_BOUNDS = [[8.2, 74.8], [12.8, 77.4]]

// Handle map resize
function MapResizer() {
  const map = useMap()
  useEffect(() => {
    setTimeout(() => map.invalidateSize(), 100)
  }, [map])
  return null
}

// Fly to selected marker
function FlyToMarker({ selectedMarkerId, markers }) {
  const map = useMap()
  
  useEffect(() => {
    if (selectedMarkerId) {
      const marker = markers.find(m => m.id === selectedMarkerId)
      if (marker) {
        map.flyTo([marker.latitude, marker.longitude], 10, { duration: 0.5 })
      }
    }
  }, [selectedMarkerId, markers, map])
  
  return null
}

export default function KeralaMap({ 
  markers = [], 
  onMarkerClick,
  selectedMarkerId,
  height = '500px',
  className = ''
}) {
  const [hoveredMarker, setHoveredMarker] = useState(null)
  
  return (
    <div className={`relative ${className}`} style={{ height }}>
      {/* Map Container */}
      <div className="absolute inset-0 rounded-xl overflow-hidden border border-white/10">
        <MapContainer
          center={KERALA_CENTER}
          zoom={7}
          maxBounds={KERALA_BOUNDS}
          minZoom={6}
          maxZoom={15}
          style={{ height: '100%', width: '100%', background: '#0a1525' }}
          zoomControl={true}
        >
          <MapResizer />
          <FlyToMarker selectedMarkerId={selectedMarkerId} markers={markers} />
          
          {/* Dark map tiles */}
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          />
          
          {/* Incident Markers */}
          {markers.map((marker) => {
            const severity = SEVERITY_COLORS[marker.severity] || SEVERITY_COLORS.P3
            const isSelected = selectedMarkerId === marker.id
            const isPriority = marker.severity === 'P1' || marker.severity === 'P2'
            
            return (
              <CircleMarker
                key={marker.id}
                center={[marker.latitude, marker.longitude]}
                radius={isSelected ? 14 : (isPriority ? 10 : 8)}
                pathOptions={{
                  fillColor: severity.hex,
                  fillOpacity: 0.9,
                  color: isSelected ? '#ffffff' : severity.hex,
                  weight: isSelected ? 3 : 2,
                }}
                eventHandlers={{
                  click: () => onMarkerClick?.(marker),
                  mouseover: () => setHoveredMarker(marker.id),
                  mouseout: () => setHoveredMarker(null),
                }}
              >
                <Popup>
                  <div className="text-sm min-w-[200px]">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xl">{SUBCATEGORY_ICONS[marker.subcategory] || '⚠️'}</span>
                      <div>
                        <span className="font-bold capitalize">{marker.subcategory?.replace(/_/g, ' ')}</span>
                        <span className={`ml-2 px-2 py-0.5 text-xs rounded-full text-white`} style={{ backgroundColor: severity.hex }}>
                          {marker.severity}
                        </span>
                      </div>
                    </div>
                    <p className="text-gray-600 mb-2">{marker.description}</p>
                    {marker.district && (
                      <p className="text-xs text-gray-500">{marker.district} District</p>
                    )}
                  </div>
                </Popup>
              </CircleMarker>
            )
          })}
        </MapContainer>
        
        {/* Legend */}
        <div className="absolute bottom-4 right-4 bg-earth-panel/90 border border-white/10 rounded-lg p-3 backdrop-blur-sm z-[1000]">
          <p className="text-xs text-slate-400 font-bold mb-2">SEVERITY</p>
          <div className="space-y-1">
            {Object.entries(SEVERITY_COLORS).map(([level, colors]) => (
              <div key={level} className="flex items-center gap-2 text-xs">
                <span className={`w-3 h-3 rounded-full ${colors.bg}`} />
                <span className="text-slate-300">{level}</span>
                <span className="text-slate-500">
                  {level === 'P1' && 'Critical'}
                  {level === 'P2' && 'High'}
                  {level === 'P3' && 'Medium'}
                  {level === 'P4' && 'Low'}
                </span>
              </div>
            ))}
          </div>
        </div>
        
        {/* Marker count */}
        <div className="absolute top-4 right-4 bg-earth-panel/90 border border-white/10 rounded-lg px-3 py-2 backdrop-blur-sm z-[1000]">
          <span className="text-2xl font-bold text-white">{markers.length}</span>
          <span className="text-xs text-slate-400 ml-2">Active Incidents</span>
        </div>
      </div>
    </div>
  )
}
