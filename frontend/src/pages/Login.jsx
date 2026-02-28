import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { RefreshCw, AlertCircle, X, UserPlus } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { authApi } from '../api'

function makeCaptcha() {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return Array.from({ length: 5 }, () => chars[Math.floor(Math.random() * chars.length)]).join('')
}

const SEARCH_TYPES = [
    { id: 'challan', label: 'Consumer ID' },
    { id: 'vehicle', label: 'Vehicle Number' },
    { id: 'dl', label: 'DL Number' },
]

export default function Login() {
    const navigate = useNavigate()
    const location = useLocation()
    const { login } = useAuth()
    const from = location.state?.from?.pathname || '/'

    const [searchType, setSearchType] = useState('challan')
    const [searchVal, setSearchVal] = useState('')
    const [captchaCode, setCaptchaCode] = useState(makeCaptcha)
    const [captchaInput, setCaptchaInput] = useState('')
    const [challanMsg, setChallanMsg] = useState('')
    const [loading, setLoading] = useState(false)
    const [authSuccess, setAuthSuccess] = useState(false)

    // Registration modal state
    const [showRegister, setShowRegister] = useState(false)
    const [regData, setRegData] = useState({ name: '', phone: '', consumer_id: '', vehicle_number: '', dl_number: '' })
    const [regLoading, setRegLoading] = useState(false)
    const [regError, setRegError] = useState('')

    const handleGetDetail = async (e) => {
        e.preventDefault()
        setChallanMsg('')
        if (!searchVal.trim()) { setChallanMsg('error:Please enter your ID.'); return }
        if (captchaInput.trim().toUpperCase() !== captchaCode) {
            setChallanMsg('error:Incorrect captcha. Please try again.')
            return
        }
        setLoading(true)
        try {
            const { data } = await authApi.login(searchVal.trim(), searchType)
            login(data.user, data.token)

            setAuthSuccess(true)
            setTimeout(() => {
                navigate(from, { replace: true })
            }, 750)

        } catch (err) {
            const msg = err.response?.data?.detail || 'No record found. Please check your details.'
            setChallanMsg(`error:${msg}`)
            setCaptchaCode(makeCaptcha())
            setCaptchaInput('')
            setLoading(false)
        }
    }

    const handleRegister = async (e) => {
        e.preventDefault()
        setRegError('')
        if (!regData.name.trim() || !regData.phone.trim() || !regData.consumer_id.trim()) {
            setRegError('Name, phone and consumer ID are required.')
            return
        }
        setRegLoading(true)
        try {
            const { data } = await authApi.register(regData)
            login(data.user, data.token)
            setShowRegister(false)
            setAuthSuccess(true)
            setTimeout(() => {
                navigate(from, { replace: true })
            }, 750)
        } catch (err) {
            setRegError(err.response?.data?.detail || 'Registration failed. Please try again.')
            setRegLoading(false)
        }
    }

    // Full screen loading overlay
    if (authSuccess) {
        return (
            <div style={{
                position: 'fixed', inset: 0,
                background: '#090914', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999
            }}>
                <div className="bars-4"></div>
            </div>
        )
    }

    return (
        <div className="relative flex h-screen w-full flex-col overflow-hidden bg-earth-dark text-slate-100 font-sans antialiased">
            <div className="absolute inset-0 z-0 w-full h-full bg-cover bg-center bg-no-repeat transition-all duration-700" style={{ backgroundImage: 'url("https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?q=80&w=2000&auto=format&fit=crop")' }}>
                <div className="absolute inset-0 bg-gradient-to-b from-orange-900/20 via-transparent to-black/60"></div>
                <div className="absolute inset-0 horizon-gradient"></div>
            </div>

            <div className="relative z-10 flex flex-col items-center pt-12 text-center px-6">
                <div className="flex items-center gap-3 mb-2">
                    <h1 className="text-white text-5xl font-bold leading-tight tracking-tight drop-shadow-xl">OneWay <span className="text-primary">Kerala</span></h1>
                </div>
                <p className="text-slate-200 text-lg font-medium drop-shadow-md max-w-xl">Premium Utility Management for the Land of Great Beauty</p>
            </div>

            <div className="flex-grow"></div>

            <form onSubmit={handleGetDetail} className="relative z-20 w-full bg-earth-panel backdrop-blur-2xl border-t border-white/10 shadow-[0_-10px_40px_rgba(0,0,0,0.5)]">
                <div className="max-w-[1400px] mx-auto px-6 py-6 lg:py-8">
                    {challanMsg && (
                        <div className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-xl text-red-200 text-sm flex items-center justify-center gap-2">
                            <AlertCircle size={16} /> <span>{challanMsg.replace('error:', '')}</span>
                        </div>
                    )}

                    <div className="flex flex-col lg:flex-row items-end lg:items-center justify-between gap-6 lg:gap-8">

                        {/* Login Method */}
                        <div className="flex flex-col gap-3 w-full lg:w-auto min-w-[280px]">
                            <span className="text-primary text-xs font-bold uppercase tracking-widest px-1">Login Method</span>
                            <div className="flex bg-black/30 p-1 rounded-xl border border-white/5 gap-1">
                                {SEARCH_TYPES.map(type => (
                                    <button
                                        key={type.id}
                                        type="button"
                                        onClick={() => setSearchType(type.id)}
                                        className={`flex-1 px-4 py-2 rounded-lg text-sm font-bold transition-all ${searchType === type.id ? 'bg-primary text-white shadow-lg' : 'text-slate-300 hover:text-white hover:bg-white/5'}`}
                                    >
                                        {type.id === 'challan' ? 'Consumer ID' : type.id === 'vehicle' ? 'Vehicle No.' : 'License'}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Enter Identification */}
                        <div className="flex flex-col lg:flex-row gap-4 flex-grow w-full">
                            <div className="flex flex-col gap-2 flex-grow">
                                <span className="text-slate-400 text-xs font-semibold px-1">Enter Identification</span>
                                <div className="relative flex items-center group">
                                    <input
                                        className="w-full h-12 bg-white/5 border border-white/10 rounded-xl px-4 text-white focus:ring-2 focus:ring-primary focus:border-transparent transition-all placeholder:text-slate-500"
                                        placeholder={`e.g., ${searchType === 'vehicle' ? 'KL-1234' : searchType === 'dl' ? '12345678' : '1000123'}`}
                                        type="text"
                                        value={searchVal}
                                        onChange={e => setSearchVal(e.target.value)}
                                    />
                                </div>
                            </div>

                            {/* Verification */}
                            <div className="flex flex-col gap-2 min-w-[240px]">
                                <span className="text-slate-400 text-xs font-semibold px-1">Verification</span>
                                <div className="flex gap-2">
                                    <div onClick={() => { setCaptchaCode(makeCaptcha()); setCaptchaInput('') }} className="h-12 w-24 bg-white/10 rounded-xl border border-white/10 flex items-center justify-center relative overflow-hidden group cursor-pointer" title="Refresh">
                                        <span className="text-lg font-bold text-white/80 italic tracking-wider z-10">{captchaCode}</span>
                                        <div className="absolute inset-0 bg-gradient-to-tr from-primary/10 to-transparent"></div>
                                        <div className="absolute top-0 left-0 w-full h-full opacity-20 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]"></div>
                                    </div>
                                    <input
                                        className="w-full h-12 bg-white/5 border border-white/10 rounded-xl px-4 text-white focus:ring-2 focus:ring-primary focus:border-transparent transition-all placeholder:text-slate-500"
                                        placeholder="Code"
                                        type="text"
                                        value={captchaInput}
                                        onChange={e => setCaptchaInput(e.target.value)}
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Login Button */}
                        <div className="flex flex-col lg:flex-row items-center gap-4 w-full lg:w-auto pt-4 lg:pt-0">
                            <button disabled={loading} type="submit" className={`w-full lg:w-48 h-14 bg-primary hover:bg-orange-600 text-white font-bold rounded-xl shadow-[0_4px_20px_rgba(217,119,6,0.4)] flex items-center justify-center gap-2 transition-all transform ${loading ? 'opacity-70 cursor-not-allowed' : 'hover:-translate-y-1 active:scale-95'} text-lg`}>
                                <span>{loading ? 'Verifying...' : 'Login'}</span>
                            </button>
                            <div className="flex lg:flex-col justify-between lg:justify-center items-center gap-2 text-xs font-medium w-full lg:w-auto px-2">
                                <a className="text-slate-400 hover:text-primary transition-colors" href="#">Forgot Details?</a>
                                <div className="hidden lg:block w-full h-[1px] bg-white/5"></div>
                                <button
                                    type="button"
                                    onClick={() => setShowRegister(true)}
                                    className="text-slate-400 hover:text-primary transition-colors"
                                >
                                    Register Account
                                </button>
                            </div>
                        </div>

                    </div>

                    {/* Footer */}
                    <div className="mt-6 pt-6 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4">
                        <div className="flex items-center gap-6">
                            <div className="flex items-center gap-2 text-slate-500">
                                <span className="material-symbols-outlined text-sm">water_drop</span>
                                <span className="text-[10px] uppercase tracking-widest font-bold">Water</span>
                            </div>
                            <div className="flex items-center gap-2 text-slate-500">
                                <span className="material-symbols-outlined text-sm">bolt</span>
                                <span className="text-[10px] uppercase tracking-widest font-bold">Power</span>
                            </div>
                            <div className="flex items-center gap-2 text-slate-500">
                                <span className="material-symbols-outlined text-sm">directions_car</span>
                                <span className="text-[10px] uppercase tracking-widest font-bold">Transport</span>
                            </div>
                        </div>
                        <p className="text-slate-500 text-[10px] uppercase tracking-[0.2em] font-medium">© 2024 GOVERNMENT OF KERALA · DEPARTMENT OF UTILITIES</p>
                    </div>
                </div>
            </form>

            {/* ─── Registration Modal ─── */}
            {showRegister && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    <div className="absolute inset-0 bg-black/70 backdrop-blur-md" onClick={() => setShowRegister(false)}></div>

                    <div className="relative bg-[#130E0B]/95 backdrop-blur-2xl rounded-2xl border border-white/10 shadow-[0_25px_60px_rgba(0,0,0,0.5)] max-w-md w-full overflow-hidden">
                        {/* Decorative glow */}
                        <div className="absolute -top-20 -right-20 w-40 h-40 bg-primary/10 rounded-full filter blur-[60px] pointer-events-none"></div>
                        <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-accent-cyan/5 rounded-full filter blur-[60px] pointer-events-none"></div>

                        {/* Header */}
                        <div className="flex items-center justify-between p-5 border-b border-white/10">
                            <div className="flex items-center gap-3">
                                <div className="w-9 h-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
                                    <UserPlus size={18} className="text-primary" />
                                </div>
                                <h3 className="text-lg font-bold text-white tracking-tight">Create Account</h3>
                            </div>
                            <button
                                type="button"
                                onClick={() => setShowRegister(false)}
                                className="p-2 rounded-xl bg-white/5 border border-white/5 text-slate-400 hover:text-white hover:bg-white/10 transition-all"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Form */}
                        <form onSubmit={handleRegister} className="p-5 space-y-4">
                            {regError && (
                                <div className="p-3 bg-red-500/20 border border-red-500/50 rounded-xl text-red-200 text-sm flex items-center gap-2">
                                    <AlertCircle size={16} /> <span>{regError}</span>
                                </div>
                            )}

                            <div>
                                <label className="block text-[10px] font-bold text-slate-400 tracking-[0.1em] uppercase mb-2">Full Name *</label>
                                <input
                                    type="text"
                                    value={regData.name}
                                    onChange={e => setRegData(p => ({ ...p, name: e.target.value }))}
                                    placeholder="Enter your full name"
                                    className="w-full px-4 py-3 rounded-xl bg-black/40 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-primary/50 focus:shadow-[0_0_15px_rgba(217,119,6,0.1)] transition-all font-medium"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-[10px] font-bold text-slate-400 tracking-[0.1em] uppercase mb-2">Phone Number *</label>
                                <input
                                    type="tel"
                                    value={regData.phone}
                                    onChange={e => setRegData(p => ({ ...p, phone: e.target.value }))}
                                    placeholder="e.g., 9876543210"
                                    className="w-full px-4 py-3 rounded-xl bg-black/40 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-primary/50 focus:shadow-[0_0_15px_rgba(217,119,6,0.1)] transition-all font-medium"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-[10px] font-bold text-slate-400 tracking-[0.1em] uppercase mb-2">Consumer ID *</label>
                                <input
                                    type="text"
                                    value={regData.consumer_id}
                                    onChange={e => setRegData(p => ({ ...p, consumer_id: e.target.value }))}
                                    placeholder="Your utility consumer ID"
                                    className="w-full px-4 py-3 rounded-xl bg-black/40 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-primary/50 focus:shadow-[0_0_15px_rgba(217,119,6,0.1)] transition-all font-medium"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-[10px] font-bold text-slate-400 tracking-[0.1em] uppercase mb-2">
                                    Vehicle Number <span className="text-slate-500 normal-case tracking-normal">(optional)</span>
                                </label>
                                <input
                                    type="text"
                                    value={regData.vehicle_number}
                                    onChange={e => setRegData(p => ({ ...p, vehicle_number: e.target.value }))}
                                    placeholder="e.g., KL-07-AB-1234"
                                    className="w-full px-4 py-3 rounded-xl bg-black/40 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-primary/50 focus:shadow-[0_0_15px_rgba(217,119,6,0.1)] transition-all font-medium"
                                />
                            </div>

                            <div>
                                <label className="block text-[10px] font-bold text-slate-400 tracking-[0.1em] uppercase mb-2">
                                    Driving License No. <span className="text-slate-500 normal-case tracking-normal">(optional)</span>
                                </label>
                                <input
                                    type="text"
                                    value={regData.dl_number}
                                    onChange={e => setRegData(p => ({ ...p, dl_number: e.target.value }))}
                                    placeholder="e.g., KL-07-20190012345"
                                    className="w-full px-4 py-3 rounded-xl bg-black/40 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-primary/50 focus:shadow-[0_0_15px_rgba(217,119,6,0.1)] transition-all font-medium"
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={regLoading}
                                className={`w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-primary text-white font-bold hover:bg-orange-600 shadow-[0_4px_20px_rgba(217,119,6,0.3)] transition-all hover:-translate-y-0.5 ${regLoading ? 'opacity-70 cursor-not-allowed' : ''}`}
                            >
                                <UserPlus size={18} />
                                {regLoading ? 'Creating Account...' : 'Register'}
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}
