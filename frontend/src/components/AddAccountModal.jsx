import { useState } from 'react'
import { X, Plus, UserCircle2 } from 'lucide-react'

const services = [
  { id: 'kseb', name: 'KSEB (Electricity)', icon: '⚡' },
  { id: 'kwa', name: 'KWA (Water)', icon: '💧' },
  { id: 'echallan', name: 'e-Challan (Traffic)', icon: '🚗' },
  { id: 'ksmart', name: 'K-Smart (Municipal)', icon: '🏛️' },
]

export default function AddAccountModal({ isOpen, onClose, onAdd, profiles = [], existingAccounts = [] }) {
  const [serviceType, setServiceType] = useState('kseb')
  const [consumerId, setConsumerId] = useState('')
  const [label, setLabel] = useState('')
  const [selectedProfile, setSelectedProfile] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  // Auto-select first profile if none selected
  const effectiveProfile = selectedProfile || (profiles.length > 0 ? profiles[0].id : '')

  // Check for duplicate: same profile + same service type
  const isDuplicate = existingAccounts.some(
    a => a.profile_id === effectiveProfile && a.service_type === serviceType
  )

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!consumerId || !label || !effectiveProfile) return

    if (isDuplicate) {
      const profileName = profiles.find(p => p.id === effectiveProfile)?.name || 'this profile'
      const serviceName = services.find(s => s.id === serviceType)?.name || serviceType
      setError(`${serviceName} bill already exists under "${profileName}"`)
      return
    }

    setError('')
    setIsSubmitting(true)
    await onAdd?.({
      service_type: serviceType,
      consumer_id: consumerId,
      label: label,
      profile_id: effectiveProfile,
    })
    setIsSubmitting(false)
    setConsumerId('')
    setLabel('')
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-md modal-backdrop"
        onClick={onClose}
      ></div>

      {/* Modal */}
      <div className="relative bg-[#130E0B]/95 backdrop-blur-2xl rounded-2xl border border-white/10 
                      shadow-[0_25px_60px_rgba(0,0,0,0.5)] max-w-md w-full overflow-hidden modal-content">

        {/* Decorative glow */}
        <div className="absolute -top-20 -right-20 w-40 h-40 bg-primary/10 rounded-full filter blur-[60px] pointer-events-none animate-pulse-slow"></div>
        <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-accent-cyan/5 rounded-full filter blur-[60px] pointer-events-none animate-pulse-slow"></div>

        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
              <Plus size={18} className="text-primary" />
            </div>
            <h3 className="text-lg font-bold text-white tracking-tight">Add Bill</h3>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-white/5 border border-white/5 text-slate-400 hover:text-white hover:bg-white/10 transition-all duration-200 hover:rotate-90"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-5">
          {/* Profile Selector */}
          <div>
            <label className="block text-[10px] font-bold text-slate-400 tracking-[0.1em] uppercase mb-3">
              Profile
            </label>
            <div className="grid grid-cols-2 gap-2">
              {profiles.map((profile) => (
                <button
                  key={profile.id}
                  type="button"
                  onClick={() => setSelectedProfile(profile.id)}
                  className={`p-3 rounded-xl border transition-all text-left flex items-center gap-2 ${(selectedProfile || profiles[0]?.id) === profile.id
                    ? 'border-primary bg-primary/15 text-white shadow-[0_0_15px_rgba(217,119,6,0.15)]'
                    : 'border-white/10 bg-black/30 text-slate-300 hover:border-white/20 hover:bg-black/40'
                    }`}
                >
                  <UserCircle2 size={18} className={
                    (selectedProfile || profiles[0]?.id) === profile.id ? 'text-primary' : 'text-slate-500'
                  } />
                  <span className="text-sm font-semibold">{profile.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Service Type */}
          <div>
            <label className="block text-[10px] font-bold text-slate-400 tracking-[0.1em] uppercase mb-3">
              Service Type
            </label>
            <div className="grid grid-cols-2 gap-2">
              {services.map((service) => (
                <button
                  key={service.id}
                  type="button"
                  onClick={() => setServiceType(service.id)}
                  className={`p-3 rounded-xl border transition-all text-left ${serviceType === service.id
                    ? 'border-primary bg-primary/15 text-white shadow-[0_0_15px_rgba(217,119,6,0.15)]'
                    : 'border-white/10 bg-black/30 text-slate-300 hover:border-white/20 hover:bg-black/40'
                    }`}
                >
                  <span className="text-xl mr-2">{service.icon}</span>
                  <span className="text-sm font-semibold">{service.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Consumer ID */}
          <div>
            <label className="block text-[10px] font-bold text-slate-400 tracking-[0.1em] uppercase mb-2">
              Consumer ID / Account Number
            </label>
            <input
              type="text"
              value={consumerId}
              onChange={(e) => setConsumerId(e.target.value)}
              placeholder="Enter your consumer ID"
              className="w-full px-4 py-3 rounded-xl bg-black/40 border border-white/10 
                         text-white placeholder-slate-500 focus:outline-none focus:border-primary/50
                         focus:shadow-[0_0_15px_rgba(217,119,6,0.1)] transition-all font-medium"
              required
            />
          </div>

          {/* Label */}
          <div>
            <label className="block text-[10px] font-bold text-slate-400 tracking-[0.1em] uppercase mb-2">
              Label (e.g., Home Electricity)
            </label>
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="Give this bill a name"
              className="w-full px-4 py-3 rounded-xl bg-black/40 border border-white/10 
                         text-white placeholder-slate-500 focus:outline-none focus:border-primary/50
                         focus:shadow-[0_0_15px_rgba(217,119,6,0.1)] transition-all font-medium"
              required
            />
          </div>

          {/* Duplicate / Error Warning */}
          {(isDuplicate || error) && (
            <div className="flex items-center gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/20">
              <span className="text-red-400 text-sm font-semibold">
                {error || `This bill type already exists under "${profiles.find(p => p.id === effectiveProfile)?.name}"`}
              </span>
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={isSubmitting || !consumerId || !label || !effectiveProfile || isDuplicate}
            className="w-full flex items-center justify-center gap-2 py-3 px-4 
                       rounded-xl bg-primary text-white font-bold 
                       hover:bg-orange-600 shadow-[0_4px_20px_rgba(217,119,6,0.3)]
                       transition-all hover:-translate-y-0.5 disabled:opacity-50 
                       disabled:cursor-not-allowed disabled:hover:translate-y-0"
          >
            <Plus className="w-5 h-5" />
            {isSubmitting ? 'Adding...' : 'Add Bill'}
          </button>
        </form>
      </div>
    </div>
  )
}
