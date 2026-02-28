import { RefreshCw } from 'lucide-react'

const SERVICE_META = {
  kseb: { name: 'KSEB', icon: '⚡', unit: 'kWh' },
  kwa: { name: 'KWA', icon: '💧', unit: 'L' },
  echallan: { name: 'e-Challan', icon: '🚗', unit: null },
  ksmart: { name: 'K-Smart', icon: '🏛', unit: null },
}

export default function UtilityCard({ account, billData, isLoading, onRefresh, onPayNow, onViewHistory, onRemove }) {
  const meta = SERVICE_META[account.service_type] || { name: account.service_type, icon: '📄' }
  const paid = billData?.status === 'paid'
  const amount = billData?.amount_due ?? '—'
  const units = billData?.units_consumed


  return (
    <div className="h-full bg-black/60 backdrop-blur-2xl border-white/10 rounded-2xl p-5 flex flex-col gap-3 relative overflow-hidden group hover:border-primary/30 transition-all duration-300 card-lift animate-fade-in-up">
      {/* Decorative gradient blur */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full filter blur-2xl group-hover:bg-primary/20 transition-all duration-500 pointer-events-none"></div>

      {/* Header */}
      <div className="flex items-start justify-between relative z-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-black/40 border border-white/5 flex items-center justify-center text-xl shadow-inner">
            {meta.icon}
          </div>
          <div>
            <p className="font-bold text-white leading-tight">{meta.name}</p>
            <p className="text-xs text-slate-400 mt-0.5">{account.consumer_id}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className={`px-2 py-1 text-[10px] uppercase tracking-widest font-bold rounded-lg ${paid ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-orange-500/10 text-orange-400 border border-orange-500/20'
            }`}>
            {paid ? 'Paid' : 'Unpaid'}
          </span>
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="text-slate-400 hover:text-white transition-colors disabled:opacity-50"
          >
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          </button>
          {onRemove && (
            <button
              onClick={() => onRemove(account)}
              className="ml-2 text-red-400 hover:text-red-600 transition-colors text-xs font-bold px-2 py-1 border border-red-400/30 rounded-lg bg-red-500/10"
              title="Remove this service"
            >
              Remove
            </button>
          )}
        </div>
      </div>

      {/* Label */}
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest relative z-10">{account.label}</p>

      {/* Amount text */}
      <div className="relative z-10 flex-grow">
        <p className={`text-3xl font-extrabold tracking-tight ${paid ? 'text-green-400' : amount > 0 ? 'text-red-400' : 'text-white'}`}>
          ₹{typeof amount === 'number' ? amount.toLocaleString() : amount}
        </p>
        {units != null && meta.unit && (
          <p className="text-xs font-bold text-slate-400 mt-1">
            {typeof units === 'number' ? units.toLocaleString() : units} {meta.unit} consumed
          </p>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3 mt-auto relative z-10 pt-2 border-t border-white/5">
        {!paid && (
          <button
            onClick={() => onPayNow(account)}
            className="flex-1 bg-primary hover:bg-orange-600 text-white font-bold py-2.5 rounded-xl shadow-[0_4px_15px_rgba(217,119,6,0.3)] transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_8px_25px_rgba(217,119,6,0.4)] active:scale-95 text-sm btn-press glow-hover"
          >
            Pay Now
          </button>
        )}
        <button
          onClick={() => onViewHistory(account)}
          className={`font-bold text-sm text-slate-400 hover:text-white transition-all duration-200 py-2.5 btn-press ${paid ? 'w-full bg-white/5 hover:bg-white/10 rounded-xl border border-white/5 hover:border-white/20' : ''}`}
        >
          History
        </button>
      </div>
    </div>
  )
}
