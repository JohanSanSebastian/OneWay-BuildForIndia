import { useState, useEffect, useRef, useCallback } from 'react'
import { 
  AlertTriangle, Camera, Upload, MapPin, Clock, Phone,
  CheckCircle, XCircle, Shield, Zap, TreeDeciduous, Droplets,
  ChevronRight, Copy, PhoneCall, Building2, Users, FileText,
  RefreshCw, Filter, Search, X, Eye, Send, Edit2, Save
} from 'lucide-react'
import { disasterApi } from '../api'
import KeralaMap from '../components/KeralaMap'

// Severity configuration
const SEVERITY_CONFIG = {
  P1: { label: 'Critical', color: 'red', bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20', response: 'Immediate' },
  P2: { label: 'High', color: 'orange', bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/20', response: 'Within 1 hour' },
  P3: { label: 'Medium', color: 'yellow', bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/20', response: 'Within 4 hours' },
  P4: { label: 'Low', color: 'green', bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/20', response: 'Within 24 hours' },
}

// Category configuration
const CATEGORY_CONFIG = {
  natural_disaster: { label: 'Natural Disaster', icon: Droplets, color: 'blue' },
  infrastructure: { label: 'Infrastructure', icon: Zap, color: 'yellow' },
  obstruction: { label: 'Obstruction', icon: TreeDeciduous, color: 'green' },
}

// Subcategory icons
const SUBCATEGORY_ICONS = {
  landslide: '⛰️', flood: '🌊', cyclone: '🌀', earthquake: '📳', storm_damage: '⛈️',
  broken_power_line: '⚡', pothole: '🕳️', road_damage: '🚧', water_main_break: '💧', collapsed_structure: '🏚️',
  fallen_tree: '🌳', vehicle_accident: '🚗', debris: '🪨', blocked_drain: '🚰', construction_hazard: '🏗️',
}

// Status configuration
const STATUS_CONFIG = {
  reported: { label: 'Reported', bg: 'bg-slate-500/10', text: 'text-slate-400' },
  verified: { label: 'Verified', bg: 'bg-blue-500/10', text: 'text-blue-400' },
  authority_notified: { label: 'Authority Notified', bg: 'bg-purple-500/10', text: 'text-purple-400' },
  in_progress: { label: 'In Progress', bg: 'bg-amber-500/10', text: 'text-amber-400' },
  resolved: { label: 'Resolved', bg: 'bg-green-500/10', text: 'text-green-400' },
  rejected: { label: 'Rejected', bg: 'bg-red-500/10', text: 'text-red-400' },
}

export default function DisasterSentinel() {
  const [activeTab, setActiveTab] = useState('report')
  const [incidents, setIncidents] = useState([])
  const [mapMarkers, setMapMarkers] = useState([])
  const [stats, setStats] = useState(null)
  const [authorities, setAuthorities] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  
  // Report form state
  const [selectedImage, setSelectedImage] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [deviceLocation, setDeviceLocation] = useState(null)
  const [locationError, setLocationError] = useState(null)
  
  // Map state
  const [selectedIncident, setSelectedIncident] = useState(null)
  const [showCallScript, setShowCallScript] = useState(false)
  const [callScript, setCallScript] = useState(null)
  
  // Edit state
  const [isEditing, setIsEditing] = useState(false)
  const [editedIncident, setEditedIncident] = useState(null)
  
  const fileInputRef = useRef(null)
  
  // Get device location on mount
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setDeviceLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy
          })
          setLocationError(null)
        },
        (error) => {
          console.warn('Geolocation error:', error.message)
          setLocationError(error.message)
        },
        { enableHighAccuracy: true, timeout: 10000 }
      )
    }
  }, [])
  
  // Load data on mount
  useEffect(() => {
    loadIncidents()
    loadMapData()
    loadStats()
    loadAuthorities()
  }, [])
  
  const loadIncidents = async () => {
    try {
      const { data } = await disasterApi.getIncidents(false)
      setIncidents(data)
    } catch (err) {
      console.error('Failed to load incidents:', err)
    }
  }
  
  const loadMapData = async () => {
    try {
      const { data } = await disasterApi.getMapData()
      setMapMarkers(data.markers || [])
    } catch (err) {
      console.error('Failed to load map data:', err)
    }
  }
  
  const loadStats = async () => {
    try {
      const { data } = await disasterApi.getStats()
      setStats(data)
    } catch (err) {
      console.error('Failed to load stats:', err)
    }
  }
  
  const loadAuthorities = async () => {
    try {
      const { data } = await disasterApi.getAllAuthorities()
      setAuthorities(data)
    } catch (err) {
      console.error('Failed to load authorities:', err)
    }
  }
  
  const handleImageSelect = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedImage(file)
      setAnalysisResult(null)
      const reader = new FileReader()
      reader.onload = (e) => setImagePreview(e.target.result)
      reader.readAsDataURL(file)
    }
  }
  
  const handleAnalyze = async () => {
    if (!selectedImage) return
    
    setIsAnalyzing(true)
    try {
      const reader = new FileReader()
      reader.onload = async (e) => {
        const base64 = e.target.result.split(',')[1]
        const { data } = await disasterApi.analyzeIncident(
          base64,
          deviceLocation?.latitude || null,
          deviceLocation?.longitude || null
        )
        setAnalysisResult(data)
        if (data.success) {
          loadIncidents()
          loadMapData()
          loadStats()
        }
        setIsAnalyzing(false)
      }
      reader.readAsDataURL(selectedImage)
    } catch (err) {
      console.error('Analysis failed:', err)
      setAnalysisResult({ success: false, error_message: 'Analysis failed. Please try again.' })
      setIsAnalyzing(false)
    }
  }
  
  const handleNotifyAuthorities = async (incidentId) => {
    try {
      await disasterApi.notifyAuthorities(incidentId)
      loadIncidents()
    } catch (err) {
      console.error('Failed to notify authorities:', err)
    }
  }
  
  const handleShowCallScript = async (incident) => {
    try {
      const { data } = await disasterApi.getCallScript(incident.id)
      setCallScript(data)
      setShowCallScript(true)
    } catch (err) {
      console.error('Failed to get call script:', err)
    }
  }
  
  const handleMarkerClick = (marker) => {
    const incident = incidents.find(i => i.id === marker.id)
    setSelectedIncident(incident || marker)
  }
  
  const clearForm = () => {
    setSelectedImage(null)
    setImagePreview(null)
    setAnalysisResult(null)
    setIsEditing(false)
    setEditedIncident(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleStartEdit = () => {
    if (analysisResult?.incident) {
      setEditedIncident({
        category: analysisResult.incident.category || 'obstruction',
        subcategory: analysisResult.incident.subcategory || 'debris',
        severity: analysisResult.incident.severity || 'P3',
        description: analysisResult.incident.description || ''
      })
      setIsEditing(true)
    }
  }

  const handleSaveEdit = () => {
    if (analysisResult && editedIncident) {
      setAnalysisResult(prev => ({
        ...prev,
        incident: {
          ...prev.incident,
          ...editedIncident
        }
      }))
      setIsEditing(false)
    }
  }
  
  return (
    <div className="max-w-[1400px] mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Shield className="text-amber-500" size={32} />
            Disaster & Infrastructure Sentinel
          </h1>
          <p className="text-slate-400 mt-1">
            Report road damage, fallen trees, floods, and infrastructure issues across Kerala
          </p>
        </div>
        
        {/* Stats badges */}
        {stats && (
          <div className="flex gap-4">
            <div className="bg-earth-panel border border-white/10 rounded-lg px-4 py-2">
              <span className="text-2xl font-bold text-white">{stats.total || 0}</span>
              <span className="text-xs text-slate-400 ml-2">Total</span>
            </div>
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-2">
              <span className="text-2xl font-bold text-red-400">{stats.by_severity?.P1 || 0}</span>
              <span className="text-xs text-red-400 ml-2">Critical</span>
            </div>
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg px-4 py-2">
              <span className="text-2xl font-bold text-blue-400">{stats.last_24h || 0}</span>
              <span className="text-xs text-blue-400 ml-2">Last 24h</span>
            </div>
          </div>
        )}
      </div>
      
      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {[
          { id: 'report', label: 'Report Incident', icon: Camera },
          { id: 'map', label: 'Live Map', icon: MapPin },
          { id: 'incidents', label: 'All Incidents', icon: FileText },
          { id: 'contacts', label: 'Emergency Contacts', icon: Phone },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
              activeTab === tab.id
                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                : 'bg-earth-panel text-slate-400 hover:text-white hover:bg-white/5 border border-white/5'
            }`}
          >
            <tab.icon size={18} />
            {tab.label}
          </button>
        ))}
      </div>
      
      {/* Report Tab */}
      {activeTab === 'report' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Upload Section */}
          <div className="bg-earth-panel border border-white/10 rounded-xl p-6">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Camera className="text-amber-400" size={20} />
              Upload Evidence
            </h2>
            
            {/* Location status */}
            <div className={`mb-4 p-3 rounded-lg ${deviceLocation ? 'bg-green-500/10 border border-green-500/20' : 'bg-yellow-500/10 border border-yellow-500/20'}`}>
              <div className="flex items-center gap-2 text-sm">
                <MapPin size={16} className={deviceLocation ? 'text-green-400' : 'text-yellow-400'} />
                {deviceLocation ? (
                  <span className="text-green-400">
                    Location acquired: {deviceLocation.latitude.toFixed(4)}, {deviceLocation.longitude.toFixed(4)}
                  </span>
                ) : (
                  <span className="text-yellow-400">
                    {locationError || 'Acquiring location...'}
                  </span>
                )}
              </div>
            </div>
            
            {/* Image upload area */}
            <div
              onClick={() => fileInputRef.current?.click()}
              className={`relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                imagePreview 
                  ? 'border-amber-500/50 bg-amber-500/5' 
                  : 'border-white/20 hover:border-amber-500/50 hover:bg-white/5'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                onChange={handleImageSelect}
                className="hidden"
              />
              
              {imagePreview ? (
                <div className="relative">
                  <img 
                    src={imagePreview} 
                    alt="Preview" 
                    className="max-h-64 mx-auto rounded-lg"
                  />
                  <button
                    onClick={(e) => { e.stopPropagation(); clearForm() }}
                    className="absolute top-2 right-2 p-1 bg-red-500 rounded-full text-white hover:bg-red-600"
                  >
                    <X size={16} />
                  </button>
                </div>
              ) : (
                <>
                  <Upload className="mx-auto text-slate-500 mb-3" size={48} />
                  <p className="text-slate-300 font-medium">Click to upload or take photo</p>
                  <p className="text-slate-500 text-sm mt-1">JPG, PNG up to 10MB</p>
                </>
              )}
            </div>
            
            {/* Analyze button */}
            <button
              onClick={handleAnalyze}
              disabled={!selectedImage || isAnalyzing}
              className="w-full mt-4 py-3 bg-amber-500 hover:bg-amber-600 disabled:bg-slate-700 disabled:text-slate-500 text-black font-bold rounded-lg transition-all flex items-center justify-center gap-2"
            >
              {isAnalyzing ? (
                <>
                  <RefreshCw className="animate-spin" size={20} />
                  Analyzing Incident...
                </>
              ) : (
                <>
                  <AlertTriangle size={20} />
                  Analyze & Report
                </>
              )}
            </button>
          </div>
          
          {/* Analysis Result */}
          <div className="bg-earth-panel border border-white/10 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <FileText className="text-amber-400" size={20} />
                Analysis Result
              </h2>
              {analysisResult?.success && !isEditing && (
                <button
                  onClick={handleStartEdit}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-white/10 transition-all"
                >
                  <Edit2 size={14} />
                  Edit
                </button>
              )}
              {isEditing && (
                <button
                  onClick={handleSaveEdit}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/20 border border-emerald-500/30 rounded-lg text-sm text-emerald-400 hover:bg-emerald-500 hover:text-white transition-all"
                >
                  <Save size={14} />
                  Save
                </button>
              )}
            </div>
            
            {analysisResult ? (
              analysisResult.success ? (
                <div className="space-y-4">
                  {/* Severity Badge - Editable */}
                  <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg ${SEVERITY_CONFIG[isEditing ? editedIncident?.severity : analysisResult.incident?.severity]?.bg} ${SEVERITY_CONFIG[isEditing ? editedIncident?.severity : analysisResult.incident?.severity]?.border} border`}>
                    <span className="text-2xl">{SUBCATEGORY_ICONS[isEditing ? editedIncident?.subcategory : analysisResult.incident?.subcategory] || '⚠️'}</span>
                    {isEditing ? (
                      <select
                        value={editedIncident?.severity || 'P3'}
                        onChange={(e) => setEditedIncident(prev => ({ ...prev, severity: e.target.value }))}
                        className="px-3 py-1 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-amber-500/50"
                      >
                        <option value="P1">P1 - Critical</option>
                        <option value="P2">P2 - High</option>
                        <option value="P3">P3 - Medium</option>
                        <option value="P4">P4 - Low</option>
                      </select>
                    ) : (
                      <div>
                        <span className={`font-bold ${SEVERITY_CONFIG[analysisResult.incident?.severity]?.text}`}>
                          {analysisResult.incident?.severity} - {SEVERITY_CONFIG[analysisResult.incident?.severity]?.label}
                        </span>
                        <p className="text-xs text-slate-400">
                          Response: {SEVERITY_CONFIG[analysisResult.incident?.severity]?.response}
                        </p>
                      </div>
                    )}
                  </div>
                  
                  {/* Incident Details - Editable */}
                  <div className="space-y-3">
                    <div>
                      <span className="text-xs text-slate-500 uppercase">Category</span>
                      {isEditing ? (
                        <select
                          value={editedIncident?.category || 'obstruction'}
                          onChange={(e) => setEditedIncident(prev => ({ ...prev, category: e.target.value }))}
                          className="w-full mt-1 px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-amber-500/50"
                        >
                          <option value="natural_disaster">Natural Disaster</option>
                          <option value="infrastructure">Infrastructure</option>
                          <option value="obstruction">Obstruction</option>
                        </select>
                      ) : (
                        <p className="text-white capitalize">
                          {analysisResult.incident?.category?.replace(/_/g, ' ')}
                        </p>
                      )}
                    </div>
                    <div>
                      <span className="text-xs text-slate-500 uppercase">Type</span>
                      {isEditing ? (
                        <select
                          value={editedIncident?.subcategory || 'debris'}
                          onChange={(e) => setEditedIncident(prev => ({ ...prev, subcategory: e.target.value }))}
                          className="w-full mt-1 px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-amber-500/50"
                        >
                          <option value="landslide">Landslide</option>
                          <option value="flood">Flood</option>
                          <option value="cyclone">Cyclone</option>
                          <option value="earthquake">Earthquake</option>
                          <option value="storm_damage">Storm Damage</option>
                          <option value="broken_power_line">Broken Power Line</option>
                          <option value="pothole">Pothole</option>
                          <option value="road_damage">Road Damage</option>
                          <option value="water_main_break">Water Main Break</option>
                          <option value="collapsed_structure">Collapsed Structure</option>
                          <option value="fallen_tree">Fallen Tree</option>
                          <option value="vehicle_accident">Vehicle Accident</option>
                          <option value="debris">Debris</option>
                          <option value="blocked_drain">Blocked Drain</option>
                          <option value="construction_hazard">Construction Hazard</option>
                        </select>
                      ) : (
                        <p className="text-white capitalize">
                          {analysisResult.incident?.subcategory?.replace(/_/g, ' ')}
                        </p>
                      )}
                    </div>
                    <div>
                      <span className="text-xs text-slate-500 uppercase">Description</span>
                      {isEditing ? (
                        <textarea
                          value={editedIncident?.description || ''}
                          onChange={(e) => setEditedIncident(prev => ({ ...prev, description: e.target.value }))}
                          className="w-full mt-1 px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-slate-300 text-sm focus:outline-none focus:border-amber-500/50 resize-none"
                          rows={3}
                          placeholder="Describe the incident..."
                        />
                      ) : (
                        <p className="text-slate-300">{analysisResult.incident?.description}</p>
                      )}
                    </div>
                    {analysisResult.incident?.district && (
                      <div>
                        <span className="text-xs text-slate-500 uppercase">District</span>
                        <p className="text-white">{analysisResult.incident.district}</p>
                      </div>
                    )}
                  </div>
                  
                  {/* Authorities */}
                  {analysisResult.authorities?.length > 0 && (
                    <div>
                      <span className="text-xs text-slate-500 uppercase mb-2 block">Recommended Authorities</span>
                      <div className="space-y-2">
                        {analysisResult.authorities.slice(0, 3).map((auth, i) => (
                          <div key={i} className="flex items-center justify-between bg-white/5 rounded-lg p-3">
                            <div>
                              <p className="text-white font-medium text-sm">{auth.name}</p>
                              <p className="text-slate-400 text-xs">{auth.department}</p>
                            </div>
                            <a
                              href={`tel:${auth.phone}`}
                              className="flex items-center gap-1 px-3 py-1 bg-green-500/20 text-green-400 rounded-lg text-sm hover:bg-green-500/30"
                            >
                              <Phone size={14} />
                              {auth.phone}
                            </a>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Action Buttons */}
                  <div className="flex gap-2 pt-2">
                    <button
                      onClick={() => handleShowCallScript(analysisResult.incident)}
                      className="flex-1 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 flex items-center justify-center gap-2"
                    >
                      <PhoneCall size={18} />
                      Get Call Script
                    </button>
                    <button
                      onClick={() => handleNotifyAuthorities(analysisResult.incident?.id)}
                      className="flex-1 py-2 bg-purple-500/20 text-purple-400 rounded-lg hover:bg-purple-500/30 flex items-center justify-center gap-2"
                    >
                      <Send size={18} />
                      Notify Authorities
                    </button>
                  </div>
                </div>
              ) : (
                <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-red-400">
                    <XCircle size={20} />
                    <span className="font-medium">Analysis Failed</span>
                  </div>
                  <p className="text-slate-400 text-sm mt-2">{analysisResult.error_message}</p>
                </div>
              )
            ) : (
              <div className="text-center py-12 text-slate-500">
                <AlertTriangle className="mx-auto mb-3 opacity-50" size={48} />
                <p>Upload an image to analyze the incident</p>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Map Tab */}
      {activeTab === 'map' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <KeralaMap
              markers={mapMarkers}
              onMarkerClick={handleMarkerClick}
              selectedMarkerId={selectedIncident?.id}
              showDistrictLabels={true}
              height="600px"
            />
          </div>
          
          {/* Incident Details Panel */}
          <div className="bg-earth-panel border border-white/10 rounded-xl p-6">
            <h2 className="text-lg font-bold text-white mb-4">Incident Details</h2>
            
            {selectedIncident ? (
              <div className="space-y-4">
                {/* Severity */}
                <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-lg ${SEVERITY_CONFIG[selectedIncident.severity]?.bg}`}>
                  <span className="text-xl">{SUBCATEGORY_ICONS[selectedIncident.subcategory] || '⚠️'}</span>
                  <span className={`font-bold ${SEVERITY_CONFIG[selectedIncident.severity]?.text}`}>
                    {selectedIncident.severity}
                  </span>
                </div>
                
                {/* Details */}
                <div className="space-y-3">
                  <div>
                    <span className="text-xs text-slate-500 uppercase">Type</span>
                    <p className="text-white capitalize">{selectedIncident.subcategory?.replace(/_/g, ' ')}</p>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500 uppercase">Status</span>
                    <span className={`ml-2 px-2 py-0.5 rounded text-xs ${STATUS_CONFIG[selectedIncident.status]?.bg} ${STATUS_CONFIG[selectedIncident.status]?.text}`}>
                      {STATUS_CONFIG[selectedIncident.status]?.label}
                    </span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500 uppercase">Description</span>
                    <p className="text-slate-300 text-sm">{selectedIncident.description}</p>
                  </div>
                  {selectedIncident.district && (
                    <div>
                      <span className="text-xs text-slate-500 uppercase">District</span>
                      <p className="text-white">{selectedIncident.district}</p>
                    </div>
                  )}
                  <div>
                    <span className="text-xs text-slate-500 uppercase">Coordinates</span>
                    <p className="text-slate-400 text-sm font-mono">
                      {selectedIncident.latitude?.toFixed(6)}, {selectedIncident.longitude?.toFixed(6)}
                    </p>
                  </div>
                </div>
                
                {/* Actions */}
                <div className="pt-4 space-y-2">
                  <button
                    onClick={() => handleShowCallScript(selectedIncident)}
                    className="w-full py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 flex items-center justify-center gap-2"
                  >
                    <PhoneCall size={18} />
                    Get Call Script
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-slate-500">
                <MapPin className="mx-auto mb-3 opacity-50" size={48} />
                <p>Click on a marker to view details</p>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Incidents List Tab */}
      {activeTab === 'incidents' && (
        <div className="bg-earth-panel border border-white/10 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-white/10 flex items-center justify-between">
            <h2 className="text-lg font-bold text-white">All Reported Incidents</h2>
            <button
              onClick={loadIncidents}
              className="p-2 hover:bg-white/5 rounded-lg text-slate-400 hover:text-white"
            >
              <RefreshCw size={18} />
            </button>
          </div>
          
          <div className="divide-y divide-white/5">
            {incidents.length > 0 ? incidents.map(incident => {
              const severity = SEVERITY_CONFIG[incident.severity] || SEVERITY_CONFIG.P3
              const status = STATUS_CONFIG[incident.status] || STATUS_CONFIG.reported
              
              return (
                <div key={incident.id} className="p-4 hover:bg-white/5">
                  <div className="flex items-start gap-4">
                    {/* Icon */}
                    <div className={`w-12 h-12 rounded-lg ${severity.bg} flex items-center justify-center text-2xl`}>
                      {SUBCATEGORY_ICONS[incident.subcategory] || '⚠️'}
                    </div>
                    
                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${severity.bg} ${severity.text}`}>
                          {incident.severity}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-xs ${status.bg} ${status.text}`}>
                          {status.label}
                        </span>
                        <span className="text-slate-500 text-xs capitalize">
                          {incident.subcategory?.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <p className="text-white mt-1">{incident.description}</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                        {incident.district && (
                          <span className="flex items-center gap-1">
                            <MapPin size={12} /> {incident.district}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <Clock size={12} /> {new Date(incident.created_at).toLocaleString()}
                        </span>
                      </div>
                    </div>
                    
                    {/* Actions */}
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleShowCallScript(incident)}
                        className="p-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30"
                        title="Get call script"
                      >
                        <PhoneCall size={16} />
                      </button>
                      {incident.status !== 'authority_notified' && incident.status !== 'resolved' && (
                        <button
                          onClick={() => handleNotifyAuthorities(incident.id)}
                          className="p-2 bg-purple-500/20 text-purple-400 rounded-lg hover:bg-purple-500/30"
                          title="Notify authorities"
                        >
                          <Send size={16} />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )
            }) : (
              <div className="p-12 text-center text-slate-500">
                <AlertTriangle className="mx-auto mb-3 opacity-50" size={48} />
                <p>No incidents reported yet</p>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Emergency Contacts Tab */}
      {activeTab === 'contacts' && authorities && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Emergency Services */}
          <div className="bg-earth-panel border border-red-500/20 rounded-xl p-6">
            <h3 className="text-lg font-bold text-red-400 mb-4 flex items-center gap-2">
              <AlertTriangle size={20} />
              Emergency Services
            </h3>
            <div className="space-y-3">
              {authorities.emergency?.map((auth, i) => (
                <div key={i} className="bg-white/5 rounded-lg p-3">
                  <p className="text-white font-medium">{auth.name}</p>
                  <p className="text-slate-400 text-sm">{auth.department}</p>
                  <div className="flex gap-2 mt-2">
                    <a
                      href={`tel:${auth.phone}`}
                      className="flex-1 py-2 bg-red-500/20 text-red-400 rounded-lg text-center text-sm font-bold hover:bg-red-500/30"
                    >
                      {auth.phone}
                    </a>
                    {auth.alt_phone && (
                      <a
                        href={`tel:${auth.alt_phone}`}
                        className="px-3 py-2 bg-white/5 text-slate-400 rounded-lg text-sm hover:bg-white/10"
                      >
                        Alt
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Utilities */}
          <div className="bg-earth-panel border border-yellow-500/20 rounded-xl p-6">
            <h3 className="text-lg font-bold text-yellow-400 mb-4 flex items-center gap-2">
              <Zap size={20} />
              Utility Services
            </h3>
            <div className="space-y-3">
              {authorities.utility?.map((auth, i) => (
                <div key={i} className="bg-white/5 rounded-lg p-3">
                  <p className="text-white font-medium">{auth.name}</p>
                  <p className="text-slate-400 text-sm">{auth.department}</p>
                  <div className="flex gap-2 mt-2">
                    <a
                      href={`tel:${auth.phone}`}
                      className="flex-1 py-2 bg-yellow-500/20 text-yellow-400 rounded-lg text-center text-sm font-bold hover:bg-yellow-500/30"
                    >
                      {auth.phone}
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Government */}
          <div className="bg-earth-panel border border-blue-500/20 rounded-xl p-6">
            <h3 className="text-lg font-bold text-blue-400 mb-4 flex items-center gap-2">
              <Building2 size={20} />
              Government Departments
            </h3>
            <div className="space-y-3">
              {authorities.government?.map((auth, i) => (
                <div key={i} className="bg-white/5 rounded-lg p-3">
                  <p className="text-white font-medium">{auth.name}</p>
                  <p className="text-slate-400 text-sm">{auth.department}</p>
                  <div className="flex gap-2 mt-2">
                    <a
                      href={`tel:${auth.phone}`}
                      className="flex-1 py-2 bg-blue-500/20 text-blue-400 rounded-lg text-center text-sm font-bold hover:bg-blue-500/30"
                    >
                      {auth.phone}
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* Call Script Modal */}
      {showCallScript && callScript && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-earth-panel border border-white/10 rounded-xl max-w-lg w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <PhoneCall className="text-blue-400" />
                  Call Script
                </h3>
                <button
                  onClick={() => setShowCallScript(false)}
                  className="p-2 hover:bg-white/10 rounded-lg text-slate-400"
                >
                  <X size={20} />
                </button>
              </div>
              
              <div className={`mb-4 p-3 rounded-lg ${SEVERITY_CONFIG[callScript.severity]?.bg} ${SEVERITY_CONFIG[callScript.severity]?.border} border`}>
                <span className={`font-bold ${SEVERITY_CONFIG[callScript.severity]?.text}`}>
                  {callScript.severity} - {callScript.severity_label}
                </span>
                <p className="text-sm text-slate-400">
                  Expected response: {callScript.response_time}
                </p>
              </div>
              
              <div className="bg-slate-900 rounded-lg p-4 font-mono text-sm text-slate-300 whitespace-pre-wrap">
                {callScript.script}
              </div>
              
              <button
                onClick={() => {
                  navigator.clipboard.writeText(callScript.script)
                }}
                className="w-full mt-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 flex items-center justify-center gap-2"
              >
                <Copy size={18} />
                Copy to Clipboard
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
