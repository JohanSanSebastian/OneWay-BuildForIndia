import { useState } from 'react'

const ROW = ({ title, subtitle, children }) => (
  <div className="bg-black/60 backdrop-blur-2xl border border-white/5 rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 group hover:border-primary/30 transition-colors relative overflow-hidden">
    <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full filter blur-2xl group-hover:bg-primary/10 transition-colors pointer-events-none"></div>
    <div className="relative z-10">
      <p className="font-bold text-white text-lg mb-1 tracking-tight">{title}</p>
      <p className="text-sm font-medium text-slate-400">{subtitle}</p>
    </div>
    <div className="relative z-10">
      {children}
    </div>
  </div>
)

const STEPS = [5, 15, 30, 60]

export default function Settings() {
  const [notifications, setNotifications] = useState(true)
  const [stepIndex, setStepIndex] = useState(2) // default 30 min

  return (
    <div className="py-8 md:py-12">
      <div className="max-w-[1400px] mx-auto px-6">
        <div className="mb-10">
          <h1 className="text-4xl font-bold text-white tracking-tight mb-2 drop-shadow-md">Settings</h1>
          <p className="text-slate-400 font-medium">Configure your dashboard preferences</p>
        </div>

        <div className="flex flex-col gap-4">
          <ROW title="Push Notifications" subtitle="Receive alerts for new bills and due dates">
            <label className="toggle">
              <input type="checkbox" checked={notifications} onChange={e => setNotifications(e.target.checked)} />
              <div className="toggle-track" />
              <div className="toggle-thumb" />
            </label>
          </ROW>

          <ROW title="Auto-refresh Interval" subtitle="How often to check for updates">
            <div className="w-full md:w-56 flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="text-primary font-bold text-lg">{STEPS[stepIndex]} min</span>
              </div>
              <input
                type="range"
                min={0}
                max={STEPS.length - 1}
                step={1}
                value={stepIndex}
                onChange={e => setStepIndex(Number(e.target.value))}
                className="slider-themed w-full"
              />
              <div className="flex justify-between px-0.5">
                {STEPS.map(s => (
                  <span key={s} className="text-[10px] font-bold text-slate-500 uppercase">{s}m</span>
                ))}
              </div>
            </div>
          </ROW>

          <ROW title="Clear All Data" subtitle="Remove all accounts and cached data">
            <button
              className="w-full md:w-auto px-6 py-3 bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500 hover:text-white rounded-xl font-bold transition-all shadow-[0_4px_15px_rgba(239,68,68,0.1)] hover:shadow-[0_4px_15px_rgba(239,68,68,0.4)] hover:-translate-y-0.5"
            >
              Clear Data
            </button>
          </ROW>
        </div>
      </div>
    </div>
  )
}
