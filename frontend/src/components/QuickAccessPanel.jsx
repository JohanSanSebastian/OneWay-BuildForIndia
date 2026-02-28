import { useNavigate } from 'react-router-dom'
import { AlertTriangle, Plus, Settings, Car } from 'lucide-react'

const QUICK_ACTIONS = [
  {
    id: 'traffic',
    label: 'Traffic Sentinel',
    description: 'Report violations',
    icon: Car,
    path: '/sentinel',
    gradient: 'from-red-500 to-orange-500',
    shadowColor: 'shadow-red-500/20'
  },
  {
    id: 'disaster',
    label: 'Disaster Alert',
    description: 'Report incidents',
    icon: AlertTriangle,
    path: '/disaster',
    gradient: 'from-amber-500 to-yellow-500',
    shadowColor: 'shadow-amber-500/20'
  },
  {
    id: 'add-bills',
    label: 'Add Bills',
    description: 'Link new accounts',
    icon: Plus,
    path: '/#add',
    gradient: 'from-emerald-500 to-green-500',
    shadowColor: 'shadow-emerald-500/20'
  },
  {
    id: 'settings',
    label: 'Settings',
    description: 'Preferences',
    icon: Settings,
    path: '/settings',
    gradient: 'from-blue-500 to-cyan-500',
    shadowColor: 'shadow-blue-500/20'
  }
]

export default function QuickAccessPanel({ onAddBillsClick }) {
  const navigate = useNavigate()

  const handleClick = (action) => {
    if (action.id === 'add-bills' && onAddBillsClick) {
      onAddBillsClick()
    } else {
      navigate(action.path)
    }
  }

  return (
    <div className="bg-black/60 backdrop-blur-2xl border border-white/10 rounded-2xl p-4 h-full flex flex-col card-lift overflow-hidden min-h-0">
      <div className="grid grid-cols-2 gap-3 flex-1 min-h-0 overflow-hidden">
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action.id}
            onClick={() => handleClick(action)}
            className={`group relative flex flex-col items-center justify-center p-4 rounded-xl 
                       bg-white/5 border border-white/10 hover:border-white/20
                       transition-all duration-300 hover:-translate-y-1 hover:shadow-lg ${action.shadowColor}
                       overflow-hidden`}
          >
            {/* Gradient background on hover */}
            <div className={`absolute inset-0 bg-gradient-to-br ${action.gradient} opacity-0 
                            group-hover:opacity-10 transition-opacity duration-300`} />
            
            {/* Icon */}
            <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${action.gradient} 
                            flex items-center justify-center mb-2 shadow-lg ${action.shadowColor}
                            group-hover:scale-110 transition-transform duration-300`}>
              <action.icon size={20} className="text-white" />
            </div>
            
            {/* Label */}
            <span className="text-xs font-bold text-white group-hover:text-white transition-colors">
              {action.label}
            </span>
            <span className="text-[10px] text-slate-500 group-hover:text-slate-400 transition-colors">
              {action.description}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
