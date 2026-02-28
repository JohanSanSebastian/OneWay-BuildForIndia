import { useState, useEffect } from 'react'
import { Plus, UserCircle2, ChevronRight, Trash2 } from 'lucide-react'
import { useProfiles } from '../context/ProfilesContext'


export default function Profiles() {
  const { profiles, addProfile, deleteProfile } = useProfiles()
  const [newName, setNewName] = useState('')
  const [adding, setAdding] = useState(false)
  const [billsPaid, setBillsPaid] = useState({})

  useEffect(() => {
    // For each profile, fetch paid bills for all accounts
    const fetchPaid = async () => {
      const result = {}
      for (const profile of profiles) {
        result[profile.id] = []
        for (const acc of profile.accounts || []) {
          try {
            const res = await import('../api')
            const { utilitiesApi } = res
            const { data } = await utilitiesApi.getHistory(acc.service_type, acc.consumer_id)
            const paid = (data || []).filter(b => b.status === 'paid')
            if (paid.length > 0) {
              result[profile.id].push({
                ...acc,
                paidBills: paid
              })
            }
          } catch {}
        }
      }
      setBillsPaid(result)
    }
    if (profiles.length > 0) fetchPaid()
  }, [profiles])

  const handleAdd = () => {
    if (!newName.trim()) return
    addProfile(newName)
    setNewName('')
    setAdding(false)
  }

  return (
    <div className="py-8 md:py-12">
      <div className="max-w-[1400px] mx-auto px-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-start justify-between mb-10 gap-4">
          <div>
            <h1 className="text-4xl font-bold text-white tracking-tight mb-2 drop-shadow-md">Profiles</h1>
            <p className="text-slate-400 font-medium">Organize accounts by location</p>
          </div>
          <button
            className="flex items-center gap-2 bg-primary hover:bg-orange-600 text-white rounded-xl px-4 py-3 font-bold text-sm shadow-[0_4px_20px_rgba(217,119,6,0.3)] transition-all hover:-translate-y-0.5"
            onClick={() => setAdding(true)}
          >
            <Plus size={16} /> Add Profile
          </button>
        </div>

        {/* Add profile inline form */}
        {adding && (
          <div className="bg-black/60 backdrop-blur-2xl border border-primary/50 rounded-2xl p-6 mb-6 flex flex-col md:flex-row gap-4">
            <input
              value={newName}
              onChange={e => setNewName(e.target.value)}
              placeholder="Profile name (e.g. Home, Office)"
              className="flex-1 h-12 bg-black/40 border border-white/10 rounded-xl px-4 text-white focus:ring-2 focus:ring-primary focus:border-transparent transition-all placeholder:text-slate-500"
              onKeyDown={e => e.key === 'Enter' && handleAdd()}
              autoFocus
            />
            <div className="flex gap-2">
              <button
                className="bg-primary hover:bg-orange-600 text-white font-bold h-12 px-6 rounded-xl transition-all shadow-[0_4px_15px_rgba(217,119,6,0.3)] hover:-translate-y-0.5"
                onClick={handleAdd}
              >
                Add
              </button>
              <button
                className="bg-white/5 hover:bg-white/10 text-slate-300 font-bold h-12 px-6 rounded-xl border border-white/10 transition-colors"
                onClick={() => setAdding(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Empty state */}
        {profiles.length === 0 && !adding && (
          <div className="bg-black/60 backdrop-blur-2xl border-white/10 rounded-2xl p-10 flex flex-col items-center justify-center text-center min-h-[250px]">
            <div className="w-16 h-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center mb-4">
              <UserCircle2 size={28} className="text-primary" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">No profiles yet</h3>
            <p className="text-slate-400 text-sm mb-6 max-w-sm">
              Create a profile first (e.g. Home, Office) before adding utility bills.
            </p>
            <button
              onClick={() => setAdding(true)}
              className="flex items-center gap-2 bg-primary hover:bg-orange-600 text-white rounded-xl px-5 py-3 font-bold text-sm shadow-[0_4px_20px_rgba(217,119,6,0.3)] transition-all hover:-translate-y-0.5"
            >
              <Plus size={16} /> Create First Profile
            </button>
          </div>
        )}

        {/* Profile list */}
        {profiles.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {profiles.map(p => (
              <div
                key={p.id}
                className="bg-black/60 backdrop-blur-2xl border border-white/5 rounded-2xl p-6 flex flex-col gap-4 group transition-colors relative overflow-hidden"
              >
                <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full filter blur-2xl group-hover:bg-primary/10 transition-colors pointer-events-none"></div>

                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-black/40 border border-white/5 rounded-xl flex items-center justify-center shrink-0 shadow-inner relative z-10">
                    <UserCircle2 size={24} className="text-primary" />
                  </div>
                  <div className="flex-1 relative z-10">
                    <p className="font-extrabold text-white text-lg tracking-tight leading-tight mb-1">{p.name}</p>
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest">{p.accounts.length} linked accounts</p>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteProfile(p.id) }}
                    className="text-slate-500 hover:text-red-400 p-2 transition-colors relative z-10"
                  >
                    <Trash2 size={18} />
                  </button>
                  <ChevronRight size={20} className="text-slate-600 group-hover:text-primary transition-colors relative z-10" />
                </div>

                {/* Bills Paid Section */}
                <div className="mt-2">
                  <p className="text-xs font-bold text-green-400 mb-1">Bills Paid</p>
                  {billsPaid[p.id] && billsPaid[p.id].length > 0 ? (
                    <ul className="text-xs text-slate-300 space-y-1 max-h-32 overflow-y-auto">
                      {billsPaid[p.id].map(acc => (
                        <li key={acc.id}>
                          <span className="font-bold text-white">{acc.label || acc.service_type}</span>: {acc.paidBills.length} paid
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <span className="text-xs text-slate-500">No bills paid yet</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
