import { useState, useEffect, useRef, useCallback } from 'react'
import { 
  Shield, Camera, Upload, Car, Phone, User, MapPin, Clock, 
  CheckCircle, AlertTriangle, Mail, Trash2, Plus, Search, X,
  ChevronRight, FileWarning, Eye, Edit2, Save
} from 'lucide-react'
import { sentinelApi } from '../api'

const STATUS_COLORS = {
  pending: { bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/20' },
  verified: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20' },
  emailed_to_mvd: { bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/20' },
  call_dispatched: { bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/20' },
  resolved: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20' },
  rejected: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20' },
}

const STATUS_LABELS = {
  pending: 'Pending',
  verified: 'Verified',
  emailed_to_mvd: 'Emailed to MVD',
  call_dispatched: 'Call Dispatched',
  resolved: 'Resolved',
  rejected: 'Rejected',
}

const VIOLATION_ICONS = {
  no_helmet: '🪖',
  triple_riding: '🏍️',
  wrong_side: '🔄',
  no_parking: '🅿️',
  signal_jump: '🚦',
  obstruction: '🚧',
  other: '⚠️',
}

export default function Sentinel() {
  const [activeTab, setActiveTab] = useState('report')
  const [reports, setReports] = useState([])
  const [registry, setRegistry] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [selectedImage, setSelectedImage] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [deviceLocation, setDeviceLocation] = useState(null)
  const [locationError, setLocationError] = useState(null)
  const [parkingPlate, setParkingPlate] = useState('')
  const [parkingResult, setParkingResult] = useState(null)
  const [showAddRegistry, setShowAddRegistry] = useState(false)
  const [newRegistry, setNewRegistry] = useState({ plate: '', name: '', phone: '' })
  const [isEditing, setIsEditing] = useState(false)
  const [editedReport, setEditedReport] = useState(null)
  const [emailNotification, setEmailNotification] = useState(null)
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
    loadReports()
    loadRegistry()
  }, [])

  const loadReports = async () => {
    try {
      const { data } = await sentinelApi.getReports()
      setReports(data)
    } catch (err) {
      console.error('Failed to load reports:', err)
    }
  }

  const loadRegistry = async () => {
    try {
      const { data } = await sentinelApi.getRegistry()
      setRegistry(data)
    } catch (err) {
      console.error('Failed to load registry:', err)
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
        const { data } = await sentinelApi.analyzeViolation(
          base64,
          deviceLocation?.latitude || null,
          deviceLocation?.longitude || null
        )
        setAnalysisResult(data)
        if (data.success) {
          loadReports()
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

  const handleSendToMVD = async (reportId) => {
    try {
      await sentinelApi.sendToMVD(reportId)
      loadReports()
      // Show email sent notification
      setEmailNotification({ success: true, message: 'Report successfully emailed to MVD!' })
      setTimeout(() => setEmailNotification(null), 5000)
    } catch (err) {
      console.error('Failed to send to MVD:', err)
      setEmailNotification({ success: false, message: 'Failed to send email. Please try again.' })
      setTimeout(() => setEmailNotification(null), 5000)
    }
  }

  const handleParkingAssist = async () => {
    if (!parkingPlate.trim()) return
    
    setIsLoading(true)
    try {
      const { data } = await sentinelApi.parkingAssist(parkingPlate)
      setParkingResult(data)
    } catch (err) {
      setParkingResult({ success: false, message: 'Failed to process request' })
    }
    setIsLoading(false)
  }

  const handleAddToRegistry = async () => {
    if (!newRegistry.plate || !newRegistry.phone) return
    
    try {
      await sentinelApi.addToRegistry(
        newRegistry.plate,
        newRegistry.name || null,
        newRegistry.phone
      )
      setNewRegistry({ plate: '', name: '', phone: '' })
      setShowAddRegistry(false)
      loadRegistry()
    } catch (err) {
      console.error('Failed to add to registry:', err)
    }
  }

  const handleDeleteFromRegistry = async (entryId) => {
    try {
      await sentinelApi.deleteFromRegistry(entryId)
      loadRegistry()
    } catch (err) {
      console.error('Failed to delete from registry:', err)
    }
  }

  const clearImage = () => {
    setSelectedImage(null)
    setImagePreview(null)
    setAnalysisResult(null)
    setIsEditing(false)
    setEditedReport(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleStartEdit = () => {
    if (analysisResult?.report) {
      setEditedReport({
        plate_number: analysisResult.report.plate_number || '',
        violation_description: analysisResult.report.violation_description || '',
        violation_type: analysisResult.report.violation_type || 'other'
      })
      setIsEditing(true)
    }
  }

  const handleSaveEdit = () => {
    if (analysisResult && editedReport) {
      setAnalysisResult(prev => ({
        ...prev,
        report: {
          ...prev.report,
          ...editedReport
        }
      }))
      setIsEditing(false)
    }
  }

  return (
    <div className="min-h-screen p-6 page-enter">
      {/* Email Notification Toast */}
      {emailNotification && (
        <div className={`fixed top-20 right-6 z-50 flex items-center gap-3 px-5 py-4 rounded-xl shadow-2xl animate-fade-in-up
          ${emailNotification.success 
            ? 'bg-emerald-500/90 text-white border border-emerald-400/20' 
            : 'bg-red-500/90 text-white border border-red-400/20'}`}>
          {emailNotification.success ? (
            <Mail size={20} className="text-white" />
          ) : (
            <AlertTriangle size={20} className="text-white" />
          )}
          <span className="font-medium">{emailNotification.message}</span>
          <button onClick={() => setEmailNotification(null)} className="ml-2 p-1 hover:bg-white/20 rounded-lg">
            <X size={16} />
          </button>
        </div>
      )}

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center shadow-lg shadow-red-500/20">
            <Shield size={24} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">OneWay Sentinel</h1>
            <p className="text-slate-400 text-sm">Motor Violation Assistant</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 p-1 bg-black/40 rounded-xl w-fit border border-white/5">
        {[
          { id: 'report', label: 'Report Violation', icon: Camera },
          { id: 'timeline', label: 'Timeline', icon: Clock },
          { id: 'parking', label: 'Parking Assist', icon: Car },
          { id: 'registry', label: 'Registry', icon: User },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200
              ${activeTab === tab.id 
                ? 'bg-primary text-white shadow-lg shadow-primary/20' 
                : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Report Violation Tab */}
      {activeTab === 'report' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fade-in-up">
          {/* Upload Section */}
          <div className="bg-black/60 backdrop-blur-2xl border border-white/10 rounded-2xl p-6 card-lift">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Camera size={20} className="text-primary" />
              Upload Evidence
            </h2>
            
            {/* Location Status */}
            <div className={`flex items-center gap-2 p-3 rounded-lg mb-4 ${
              deviceLocation 
                ? 'bg-green-500/10 border border-green-500/20' 
                : 'bg-yellow-500/10 border border-yellow-500/20'
            }`}>
              <MapPin size={16} className={deviceLocation ? 'text-green-400' : 'text-yellow-400'} />
              <span className={`text-sm ${deviceLocation ? 'text-green-400' : 'text-yellow-400'}`}>
                {deviceLocation 
                  ? `Location captured: ${deviceLocation.latitude.toFixed(4)}, ${deviceLocation.longitude.toFixed(4)}`
                  : locationError || 'Getting device location...'
                }
              </span>
            </div>
            
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageSelect}
              className="hidden"
            />
            
            {!imagePreview ? (
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-white/10 rounded-xl p-12 text-center cursor-pointer
                           hover:border-primary/50 hover:bg-primary/5 transition-all duration-300 group"
              >
                <Upload size={48} className="mx-auto text-slate-500 group-hover:text-primary transition-colors mb-4" />
                <p className="text-slate-400 group-hover:text-white transition-colors">
                  Click or drag image to upload
                </p>
                <p className="text-slate-500 text-sm mt-2">
                  JPEG, PNG supported • EXIF data will be extracted
                </p>
              </div>
            ) : (
              <div className="relative">
                <img
                  src={imagePreview}
                  alt="Evidence preview"
                  className="w-full h-64 object-cover rounded-xl"
                />
                <button
                  onClick={clearImage}
                  className="absolute top-2 right-2 p-2 bg-black/60 rounded-lg text-white hover:bg-red-500 transition-colors"
                >
                  <X size={16} />
                </button>
              </div>
            )}

            {imagePreview && !analysisResult && (
              <button
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                className="w-full mt-4 py-3 bg-primary hover:bg-orange-600 text-white font-bold rounded-xl
                           shadow-lg shadow-primary/20 transition-all duration-200 flex items-center justify-center gap-2
                           disabled:opacity-50 disabled:cursor-not-allowed btn-press"
              >
                {isAnalyzing ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Analyzing with AI...
                  </>
                ) : (
                  <>
                    <Eye size={18} />
                    Analyze Violation
                  </>
                )}
              </button>
            )}
          </div>

          {/* Analysis Result */}
          <div className="bg-black/60 backdrop-blur-2xl border border-white/10 rounded-2xl p-6 card-lift">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <FileWarning size={20} className="text-primary" />
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
            
            {!analysisResult ? (
              <div className="h-64 flex items-center justify-center text-slate-500 text-center">
                <div>
                  <Shield size={48} className="mx-auto mb-4 opacity-30" />
                  <p>Upload an image to analyze</p>
                  <p className="text-sm mt-1">AI will detect plates and violations</p>
                </div>
              </div>
            ) : analysisResult.success ? (
              <div className="space-y-4 animate-fade-in-up">
                {/* Authenticity Badge */}
                <div className={`flex items-center gap-2 p-3 rounded-lg ${
                  analysisResult.report?.is_authentic 
                    ? 'bg-green-500/10 border border-green-500/20' 
                    : 'bg-red-500/10 border border-red-500/20'
                }`}>
                  {analysisResult.report?.is_authentic ? (
                    <>
                      <CheckCircle size={18} className="text-green-400" />
                      <span className="text-green-400 font-medium">Authentic Image</span>
                    </>
                  ) : (
                    <>
                      <AlertTriangle size={18} className="text-red-400" />
                      <span className="text-red-400 font-medium">Potentially Manipulated</span>
                    </>
                  )}
                  <span className="ml-auto text-sm text-slate-400">
                    {Math.round((analysisResult.report?.confidence || 0) * 100)}% confidence
                  </span>
                </div>

                {/* Details - Editable */}
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-3 bg-white/5 rounded-lg">
                    <span className="text-2xl">{VIOLATION_ICONS[isEditing ? editedReport?.violation_type : analysisResult.report?.violation_type] || '⚠️'}</span>
                    <div className="flex-1">
                      <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">Violation</p>
                      {isEditing ? (
                        <div className="space-y-2">
                          <select
                            value={editedReport?.violation_type || 'other'}
                            onChange={(e) => setEditedReport(prev => ({ ...prev, violation_type: e.target.value }))}
                            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-primary/50"
                          >
                            <option value="no_helmet">No Helmet</option>
                            <option value="triple_riding">Triple Riding</option>
                            <option value="wrong_side">Wrong Side</option>
                            <option value="no_parking">No Parking</option>
                            <option value="signal_jump">Signal Jump</option>
                            <option value="obstruction">Obstruction</option>
                            <option value="other">Other</option>
                          </select>
                          <input
                            type="text"
                            value={editedReport?.violation_description || ''}
                            onChange={(e) => setEditedReport(prev => ({ ...prev, violation_description: e.target.value }))}
                            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm placeholder:text-slate-500 focus:outline-none focus:border-primary/50"
                            placeholder="Violation description"
                          />
                        </div>
                      ) : (
                        <p className="text-white font-medium">{analysisResult.report?.violation_description}</p>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3 p-3 bg-white/5 rounded-lg">
                    <Car size={24} className="text-slate-400" />
                    <div className="flex-1">
                      <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">License Plate</p>
                      {isEditing ? (
                        <input
                          type="text"
                          value={editedReport?.plate_number || ''}
                          onChange={(e) => setEditedReport(prev => ({ ...prev, plate_number: e.target.value.toUpperCase() }))}
                          className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white font-bold text-lg placeholder:text-slate-500 focus:outline-none focus:border-primary/50"
                          placeholder="Enter plate number"
                        />
                      ) : (
                        <p className="text-white font-bold text-lg">{analysisResult.report?.plate_number || 'Not detected'}</p>
                      )}
                    </div>
                  </div>

                  {analysisResult.exif_data?.location_string && (
                    <div className="flex items-center gap-3 p-3 bg-white/5 rounded-lg">
                      <MapPin size={24} className="text-slate-400" />
                      <div>
                        <p className="text-xs text-slate-400 uppercase tracking-wider">
                          Location {analysisResult.exif_data.location_source === 'device' && '(Device GPS)'}
                        </p>
                        <p className="text-white">{analysisResult.exif_data.location_string}</p>
                      </div>
                    </div>
                  )}

                  {analysisResult.exif_data?.timestamp && (
                    <div className="flex items-center gap-3 p-3 bg-white/5 rounded-lg">
                      <Clock size={24} className="text-slate-400" />
                      <div>
                        <p className="text-xs text-slate-400 uppercase tracking-wider">Timestamp</p>
                        <p className="text-white">{analysisResult.exif_data.timestamp}</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Actions */}
                {analysisResult.report?.is_authentic && (
                  <button
                    onClick={() => handleSendToMVD(analysisResult.report.id)}
                    className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 text-white font-bold rounded-xl
                               flex items-center justify-center gap-2 transition-all duration-200 btn-press"
                  >
                    <Mail size={18} />
                    Send Report to MVD
                  </button>
                )}
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-red-400 text-center">
                <div>
                  <AlertTriangle size={48} className="mx-auto mb-4" />
                  <p>{analysisResult.error_message}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Timeline Tab */}
      {activeTab === 'timeline' && (
        <div className="bg-black/60 backdrop-blur-2xl border border-white/10 rounded-2xl p-6 animate-fade-in-up">
          <h2 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
            <Clock size={20} className="text-primary" />
            Reported Violations
          </h2>
          
          {reports.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-slate-500 text-center">
              <div>
                <FileWarning size={48} className="mx-auto mb-4 opacity-30" />
                <p>No violation reports yet</p>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {reports.map((report, idx) => (
                <div 
                  key={report.id}
                  className="flex items-center gap-4 p-4 bg-white/5 rounded-xl hover:bg-white/10 transition-all duration-200 animate-fade-in-up"
                  style={{ animationDelay: `${idx * 50}ms` }}
                >
                  <span className="text-2xl">{VIOLATION_ICONS[report.violation_type] || '⚠️'}</span>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-bold text-white">{report.plate_number || 'Unknown Plate'}</span>
                      <span className={`px-2 py-0.5 text-[10px] uppercase tracking-widest font-bold rounded-lg
                        ${STATUS_COLORS[report.status]?.bg} ${STATUS_COLORS[report.status]?.text} ${STATUS_COLORS[report.status]?.border} border`}>
                        {STATUS_LABELS[report.status]}
                      </span>
                    </div>
                    <p className="text-sm text-slate-400 truncate">{report.violation_description}</p>
                    <p className="text-xs text-slate-500 mt-1">{report.created_at}</p>
                  </div>

                  {report.status === 'verified' && (
                    <button
                      onClick={() => handleSendToMVD(report.id)}
                      className="px-4 py-2 bg-emerald-500/10 text-emerald-400 rounded-lg text-sm font-medium
                                 hover:bg-emerald-500 hover:text-white transition-all duration-200 flex items-center gap-2"
                    >
                      <Mail size={14} />
                      Send to MVD
                    </button>
                  )}

                  <ChevronRight size={18} className="text-slate-500" />
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Parking Assist Tab */}
      {activeTab === 'parking' && (
        <div className="max-w-xl animate-fade-in-up">
          <div className="bg-black/60 backdrop-blur-2xl border border-white/10 rounded-2xl p-6 card-lift">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Car size={20} className="text-primary" />
              Parking Obstruction Assistant
            </h2>
            
            <p className="text-slate-400 text-sm mb-6">
              Enter the license plate of the vehicle blocking you. If registered in our system, 
              an automated call will be dispatched to the owner.
            </p>

            <div className="flex gap-3">
              <div className="flex-1 relative">
                <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="text"
                  value={parkingPlate}
                  onChange={(e) => setParkingPlate(e.target.value.toUpperCase())}
                  placeholder="Enter plate number (e.g., KL 01 AB 1234)"
                  className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white
                             placeholder:text-slate-500 focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
                />
              </div>
              <button
                onClick={handleParkingAssist}
                disabled={!parkingPlate.trim() || isLoading}
                className="px-6 py-3 bg-primary hover:bg-orange-600 text-white font-bold rounded-xl
                           shadow-lg shadow-primary/20 transition-all duration-200 disabled:opacity-50 btn-press"
              >
                {isLoading ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <Phone size={18} />
                )}
              </button>
            </div>

            {parkingResult && (
              <div className={`mt-4 p-4 rounded-xl animate-fade-in-up ${
                parkingResult.success && parkingResult.owner_found 
                  ? 'bg-green-500/10 border border-green-500/20' 
                  : 'bg-yellow-500/10 border border-yellow-500/20'
              }`}>
                {parkingResult.owner_found ? (
                  <div className="flex items-center gap-3">
                    <CheckCircle size={20} className="text-green-400" />
                    <div>
                      <p className="font-medium text-green-400">{parkingResult.call_status}</p>
                      <p className="text-sm text-slate-400 mt-1">{parkingResult.message}</p>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center gap-3">
                    <AlertTriangle size={20} className="text-yellow-400" />
                    <p className="text-yellow-400">{parkingResult.message}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Registry Tab */}
      {activeTab === 'registry' && (
        <div className="bg-black/60 backdrop-blur-2xl border border-white/10 rounded-2xl p-6 animate-fade-in-up">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <User size={20} className="text-primary" />
              OneWay Vehicle Registry
            </h2>
            <button
              onClick={() => setShowAddRegistry(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-orange-600 text-white 
                         font-medium rounded-xl transition-all duration-200 btn-press"
            >
              <Plus size={16} />
              Add Vehicle
            </button>
          </div>

          <p className="text-slate-400 text-sm mb-6">
            Register vehicles to enable the Parking Assistant feature. Phone numbers are encrypted and 
            only used for automated parking obstruction notifications.
          </p>

          {/* Add Registry Form */}
          {showAddRegistry && (
            <div className="mb-6 p-4 bg-white/5 rounded-xl border border-white/10 animate-fade-in-up">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <input
                  type="text"
                  value={newRegistry.plate}
                  onChange={(e) => setNewRegistry(p => ({ ...p, plate: e.target.value.toUpperCase() }))}
                  placeholder="Plate Number *"
                  className="px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white
                             placeholder:text-slate-500 focus:outline-none focus:border-primary/50"
                />
                <input
                  type="text"
                  value={newRegistry.name}
                  onChange={(e) => setNewRegistry(p => ({ ...p, name: e.target.value }))}
                  placeholder="Owner Name (optional)"
                  className="px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white
                             placeholder:text-slate-500 focus:outline-none focus:border-primary/50"
                />
                <input
                  type="tel"
                  value={newRegistry.phone}
                  onChange={(e) => setNewRegistry(p => ({ ...p, phone: e.target.value }))}
                  placeholder="Phone Number *"
                  className="px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white
                             placeholder:text-slate-500 focus:outline-none focus:border-primary/50"
                />
              </div>
              <div className="flex justify-end gap-3 mt-4">
                <button
                  onClick={() => setShowAddRegistry(false)}
                  className="px-4 py-2 text-slate-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddToRegistry}
                  disabled={!newRegistry.plate || !newRegistry.phone}
                  className="px-6 py-2 bg-primary hover:bg-orange-600 text-white font-medium rounded-xl
                             transition-all duration-200 disabled:opacity-50 btn-press"
                >
                  Add to Registry
                </button>
              </div>
            </div>
          )}

          {/* Registry Table */}
          {registry.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-slate-500 text-center">
              <div>
                <Car size={48} className="mx-auto mb-4 opacity-30" />
                <p>No vehicles in registry</p>
                <p className="text-sm mt-1">Add vehicles to enable parking assist</p>
              </div>
            </div>
          ) : (
            <div className="overflow-hidden rounded-xl border border-white/10">
              <table className="w-full">
                <thead>
                  <tr className="bg-white/5 border-b border-white/10">
                    <th className="text-left px-4 py-3 text-xs font-bold text-slate-400 uppercase tracking-wider">Plate Number</th>
                    <th className="text-left px-4 py-3 text-xs font-bold text-slate-400 uppercase tracking-wider">Owner</th>
                    <th className="text-left px-4 py-3 text-xs font-bold text-slate-400 uppercase tracking-wider">Phone</th>
                    <th className="text-left px-4 py-3 text-xs font-bold text-slate-400 uppercase tracking-wider">Added</th>
                    <th className="w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {registry.map((entry, idx) => (
                    <tr 
                      key={entry.id} 
                      className="border-b border-white/5 hover:bg-white/5 transition-colors animate-fade-in-up"
                      style={{ animationDelay: `${idx * 50}ms` }}
                    >
                      <td className="px-4 py-3 font-bold text-white">{entry.plate_number}</td>
                      <td className="px-4 py-3 text-slate-400">{entry.owner_name || '—'}</td>
                      <td className="px-4 py-3 text-slate-400">{entry.owner_phone}</td>
                      <td className="px-4 py-3 text-slate-500 text-sm">{entry.created_at?.split('T')[0]}</td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => handleDeleteFromRegistry(entry.id)}
                          className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all"
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
