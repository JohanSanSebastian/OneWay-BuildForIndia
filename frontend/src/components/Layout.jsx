import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Home, Users, Settings, LogOut } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useProfiles } from '../context/ProfilesContext'
import backwatersBg from '../assets/kerala-backwaters.jpg'

const NAV = [
  { path: '/', label: 'Dashboard' },
  { path: '/profiles', label: 'Profiles' },
  { path: '/sentinel', label: 'Traffic' },
  { path: '/disaster', label: 'Disaster' },
  { path: '/settings', label: 'Settings' },
]

export default function Layout({ children }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const { profiles } = useProfiles()

  const handleLogout = () => { logout(); navigate('/login', { replace: true }) }

  return (
    <div className="min-h-screen flex flex-col bg-earth-dark text-slate-100 font-sans antialiased">
      {/* Background elements */}
      <div className="fixed inset-0 z-0 bg-cover bg-center pointer-events-none opacity-40 mix-blend-screen" style={{ backgroundImage: `url(${backwatersBg})` }}></div>

      {/* Nav */}
      <header className="sticky top-0 z-50 bg-[#130E0B]/80 border-b border-white/10 backdrop-blur-2xl shadow-lg">
        <div className="max-w-[1200px] mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-white hover:text-primary transition-colors">
            <span className="font-bold text-xl tracking-tight">OneWay <span className="text-primary">Kerala</span></span>
          </Link>

          <nav className="flex items-center gap-2">
            {NAV.map(({ path, label }) => {
              const active = location.pathname === path
              const link = (
                <Link
                  key={path}
                  to={path}
                  className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${active ? 'bg-primary/20 text-primary' : 'text-slate-400 hover:text-slate-100 hover:bg-white/5'
                    }`}
                >
                  {label}
                </Link>
              )

              if (path === '/') {
                return [
                  link,
                  <button
                    key="add"
                    onClick={() => navigate(profiles.length > 0 ? '/#add' : '/profiles')}
                    className="px-4 py-2 rounded-lg text-sm font-bold transition-all text-slate-400 hover:text-slate-100 hover:bg-white/5"
                  >
                    Add Bills
                  </button>
                ]
              }

              return link
            })}

            <div className="w-[1px] h-5 bg-white/10 mx-2" />

            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 text-sm font-bold transition-all"
            >
              <LogOut size={16} /> <span className="hidden sm:inline">Logout</span>
            </button>
          </nav>
        </div>
      </header>

      <main className="flex-1 relative z-10">{children}</main>

      <footer className="border-t border-white/10 py-6 text-center relative z-10 bg-earth-panel">
        <span className="text-xs text-slate-500 font-medium uppercase tracking-widest">
          © 2026 GOVERNMENT OF KERALA · DEPARTMENT OF UTILITIES
        </span>
      </footer>
    </div>
  )
}
