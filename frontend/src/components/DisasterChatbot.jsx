import { useState, useRef, useEffect } from 'react'
import { 
  Send, Camera, MapPin, AlertTriangle, Bot, User, 
  Loader2, CheckCircle, Phone, X, Upload, RefreshCw
} from 'lucide-react'
import { disasterApi } from '../api'

// Severity colors
const SEVERITY_CONFIG = {
  P1: { label: 'Critical', bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30' },
  P2: { label: 'High', bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500/30' },
  P3: { label: 'Medium', bg: 'bg-yellow-500/20', text: 'text-yellow-400', border: 'border-yellow-500/30' },
  P4: { label: 'Low', bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/30' },
}

// Subcategory icons
const SUBCATEGORY_ICONS = {
  landslide: '⛰️', flood: '🌊', cyclone: '🌀', earthquake: '📳', storm_damage: '⛈️',
  broken_power_line: '⚡', pothole: '🕳️', road_damage: '🚧', water_main_break: '💧', collapsed_structure: '🏚️',
  fallen_tree: '🌳', vehicle_accident: '🚗', debris: '🪨', blocked_drain: '🚰', construction_hazard: '🏗️',
}

export default function DisasterChatbot({ onIncidentReported }) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: "Hello! I'm the Disaster Sentinel. Report road damage, fallen trees, floods, or any infrastructure issues. Upload a photo to get started.",
      timestamp: new Date()
    }
  ])
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [deviceLocation, setDeviceLocation] = useState(null)
  const [selectedImage, setSelectedImage] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)
  
  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])
  
  // Get device location
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setDeviceLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          })
        },
        () => {},
        { enableHighAccuracy: true, timeout: 10000 }
      )
    }
  }, [])
  
  const addMessage = (type, content, extra = {}) => {
    setMessages(prev => [...prev, {
      id: Date.now(),
      type,
      content,
      timestamp: new Date(),
      ...extra
    }])
  }
  
  const handleImageSelect = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedImage(file)
      const reader = new FileReader()
      reader.onload = (e) => setImagePreview(e.target.result)
      reader.readAsDataURL(file)
    }
  }
  
  const handleSubmitImage = async () => {
    if (!selectedImage) return
    
    // Add user message with image
    addMessage('user', 'Reporting an incident...', { image: imagePreview })
    
    setIsAnalyzing(true)
    addMessage('bot', null, { isLoading: true })
    
    try {
      const reader = new FileReader()
      reader.onload = async (e) => {
        const base64 = e.target.result.split(',')[1]
        
        try {
          const { data } = await disasterApi.analyzeIncident(
            base64,
            deviceLocation?.latitude || null,
            deviceLocation?.longitude || null
          )
          
          // Remove loading message
          setMessages(prev => prev.filter(m => !m.isLoading))
          
          if (data.success) {
            const incident = data.incident
            const severity = SEVERITY_CONFIG[incident.severity] || SEVERITY_CONFIG.P3
            const icon = SUBCATEGORY_ICONS[incident.subcategory] || '⚠️'
            
            // Add success message
            addMessage('bot', null, {
              isIncident: true,
              incident: incident,
              authorities: data.authorities,
              callScript: data.call_script
            })
            
            // Notify parent
            if (onIncidentReported) {
              onIncidentReported(incident)
            }
          } else {
            addMessage('bot', `Sorry, I couldn't analyze that image. ${data.error_message || 'Please try again.'}`)
          }
        } catch (err) {
          setMessages(prev => prev.filter(m => !m.isLoading))
          addMessage('bot', 'An error occurred while analyzing the image. Please try again.')
        }
        
        setIsAnalyzing(false)
        setSelectedImage(null)
        setImagePreview(null)
        if (fileInputRef.current) fileInputRef.current.value = ''
      }
      reader.readAsDataURL(selectedImage)
    } catch (err) {
      setMessages(prev => prev.filter(m => !m.isLoading))
      addMessage('bot', 'Failed to process image. Please try again.')
      setIsAnalyzing(false)
    }
  }
  
  const handleQuickAction = (action) => {
    if (action === 'photo') {
      fileInputRef.current?.click()
    }
  }
  
  const cancelImage = () => {
    setSelectedImage(null)
    setImagePreview(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }
  
  return (
    <div className="bg-black/60 backdrop-blur-2xl border border-white/10 rounded-2xl flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-white/10 bg-black/20 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center">
          <AlertTriangle className="text-amber-400" size={20} />
        </div>
        <div className="flex-1">
          <h3 className="font-bold text-white text-sm">Disaster Sentinel</h3>
          <p className="text-xs text-slate-400">Report infrastructure issues</p>
        </div>
        {deviceLocation && (
          <div className="flex items-center gap-1 text-xs text-green-400 bg-green-500/10 px-2 py-1 rounded-lg">
            <MapPin size={12} />
            GPS
          </div>
        )}
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        {messages.map((message) => (
          <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
            {message.type === 'bot' && (
              <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center mr-2 shrink-0">
                <Bot className="text-amber-400" size={16} />
              </div>
            )}
            
            <div className={`max-w-[85%] ${message.type === 'user' ? 'order-1' : ''}`}>
              {message.isLoading ? (
                <div className="bg-white/5 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2">
                  <Loader2 className="animate-spin text-amber-400" size={16} />
                  <span className="text-slate-400 text-sm">Analyzing incident...</span>
                </div>
              ) : message.isIncident ? (
                <IncidentCard 
                  incident={message.incident} 
                  authorities={message.authorities}
                  callScript={message.callScript}
                />
              ) : (
                <div className={`rounded-2xl px-4 py-3 ${
                  message.type === 'user' 
                    ? 'bg-amber-500/20 rounded-tr-sm text-white' 
                    : 'bg-white/5 rounded-tl-sm text-slate-300'
                }`}>
                  {message.image && (
                    <img src={message.image} alt="Report" className="max-h-32 rounded-lg mb-2" />
                  )}
                  <p className="text-sm">{message.content}</p>
                </div>
              )}
              <p className="text-[10px] text-slate-500 mt-1 px-1">
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
            
            {message.type === 'user' && (
              <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center ml-2 shrink-0">
                <User className="text-blue-400" size={16} />
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Image Preview */}
      {imagePreview && (
        <div className="px-4 py-2 border-t border-white/10 bg-black/20">
          <div className="relative inline-block">
            <img src={imagePreview} alt="Preview" className="h-20 rounded-lg" />
            <button
              onClick={cancelImage}
              className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white"
            >
              <X size={14} />
            </button>
          </div>
        </div>
      )}
      
      {/* Input Area */}
      <div className="p-4 border-t border-white/10 bg-black/20">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          onChange={handleImageSelect}
          className="hidden"
        />
        
        {selectedImage ? (
          <button
            onClick={handleSubmitImage}
            disabled={isAnalyzing}
            className="w-full py-3 bg-amber-500 hover:bg-amber-600 disabled:bg-slate-700 text-black font-bold rounded-xl flex items-center justify-center gap-2 transition-all"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="animate-spin" size={18} />
                Analyzing...
              </>
            ) : (
              <>
                <Send size={18} />
                Submit Report
              </>
            )}
          </button>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={() => handleQuickAction('photo')}
              className="flex-1 py-3 bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 font-bold rounded-xl flex items-center justify-center gap-2 transition-all"
            >
              <Camera size={18} />
              Take Photo
            </button>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex-1 py-3 bg-white/5 hover:bg-white/10 text-slate-300 font-bold rounded-xl flex items-center justify-center gap-2 transition-all"
            >
              <Upload size={18} />
              Upload
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// Incident Card Component
function IncidentCard({ incident, authorities, callScript }) {
  const [showAuthorities, setShowAuthorities] = useState(false)
  const severity = SEVERITY_CONFIG[incident.severity] || SEVERITY_CONFIG.P3
  const icon = SUBCATEGORY_ICONS[incident.subcategory] || '⚠️'
  
  return (
    <div className="bg-white/5 rounded-2xl rounded-tl-sm overflow-hidden">
      {/* Severity Header */}
      <div className={`px-4 py-2 ${severity.bg} border-b ${severity.border}`}>
        <div className="flex items-center gap-2">
          <span className="text-xl">{icon}</span>
          <span className={`font-bold ${severity.text}`}>
            {incident.severity} - {severity.label}
          </span>
        </div>
      </div>
      
      {/* Content */}
      <div className="p-4 space-y-3">
        <div>
          <p className="text-xs text-slate-500 uppercase">Incident Type</p>
          <p className="text-white font-medium capitalize">
            {incident.subcategory?.replace(/_/g, ' ')}
          </p>
        </div>
        
        <div>
          <p className="text-xs text-slate-500 uppercase">Description</p>
          <p className="text-slate-300 text-sm">{incident.description}</p>
        </div>
        
        {incident.district && (
          <div>
            <p className="text-xs text-slate-500 uppercase">Location</p>
            <p className="text-slate-300 text-sm flex items-center gap-1">
              <MapPin size={12} />
              {incident.district} District
            </p>
          </div>
        )}
        
        {/* Status */}
        <div className="flex items-center gap-2 text-green-400 text-sm">
          <CheckCircle size={16} />
          Incident logged successfully
        </div>
        
        {/* Authorities */}
        {authorities && authorities.length > 0 && (
          <div className="pt-2 border-t border-white/10">
            <button
              onClick={() => setShowAuthorities(!showAuthorities)}
              className="text-xs text-amber-400 font-medium hover:underline"
            >
              {showAuthorities ? 'Hide' : 'Show'} emergency contacts ({authorities.length})
            </button>
            
            {showAuthorities && (
              <div className="mt-2 space-y-2">
                {authorities.slice(0, 3).map((auth, i) => (
                  <a
                    key={i}
                    href={`tel:${auth.phone}`}
                    className="flex items-center justify-between bg-black/20 rounded-lg p-2 hover:bg-black/30"
                  >
                    <div>
                      <p className="text-white text-xs font-medium">{auth.name}</p>
                      <p className="text-slate-500 text-[10px]">{auth.department}</p>
                    </div>
                    <div className="flex items-center gap-1 text-green-400 text-xs">
                      <Phone size={12} />
                      {auth.phone}
                    </div>
                  </a>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
