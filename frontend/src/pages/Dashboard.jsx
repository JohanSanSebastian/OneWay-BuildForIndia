import { useState, useEffect, useCallback } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Plus, RefreshCw, Wallet, Clock, UserCircle2 } from 'lucide-react'
import UtilityCard from '../components/UtilityCard'
import QRModal from '../components/QRModal'
import AddAccountModal from '../components/AddAccountModal'
import HistoryModal from '../components/HistoryModal'
import { ServiceComparisonChart, MonthlyTrendChart } from '../components/Charts'
import QuickAccessPanel from '../components/QuickAccessPanel'
import DisasterChatbot from '../components/DisasterChatbot'
import DashboardMap from '../components/DashboardMap'
import { utilitiesApi, paymentsApi, profilesApi } from '../api'
import { useProfiles } from '../context/ProfilesContext'

const SERVICE_CHART_META = {
  kseb: { name: 'KSEB', color: '#d97706', fill: '#d97706' },
  kwa: { name: 'KWA', color: '#119bb0', fill: '#119bb0' },
  echallan: { name: 'e-Challan', color: '#f59e0b', fill: '#f59e0b' },
  ksmart: { name: 'K-Smart', color: '#fbbf24', fill: '#fbbf24' },
}

const LAYOUT_CACHE_KEY = 'oneway_dashboard_layout'

// Load cached layout from localStorage
const loadCachedLayout = () => {
  try {
    const cached = localStorage.getItem(LAYOUT_CACHE_KEY)
    if (cached) {
      const data = JSON.parse(cached)
      // Validate cache is not too old (24 hours)
      if (data.timestamp && Date.now() - data.timestamp < 24 * 60 * 60 * 1000) {
        return data
      }
    }
  } catch (e) {
    console.warn('Failed to load cached layout:', e)
  }
  return null
}

// Save layout to localStorage
const saveCachedLayout = (accounts, billData) => {
  try {
    localStorage.setItem(LAYOUT_CACHE_KEY, JSON.stringify({
      accounts,
      billData,
      timestamp: Date.now()
    }))
  } catch (e) {
    console.warn('Failed to save layout cache:', e)
  }
}

export default function Dashboard() {
  // Load cached layout for instant display (only on mount)
  const [cachedLayout] = useState(() => loadCachedLayout())
  
  const [accounts, setAccounts] = useState(cachedLayout?.accounts || [])
  const [billData, setBillData] = useState(cachedLayout?.billData || {})
  const [loadingAccounts, setLoadingAccounts] = useState({})
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [isQRModalOpen, setIsQRModalOpen] = useState(false)
  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false)
  const [selectedAccount, setSelectedAccount] = useState(null)
  const [qrCode, setQrCode] = useState('')
  const [history, setHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)
  // Only show initial loading if we don't have cached data
  const [initialLoading, setInitialLoading] = useState(!cachedLayout)

  const { profiles, linkAccount } = useProfiles()

  const totalDue = accounts.length === 0
    ? 0
    : Object.values(billData)
        .filter(b => b && b.status !== 'paid' && typeof b.amount_due === 'number' && b.amount_due > 0)
        .reduce((s, b) => s + b.amount_due, 0)

  const unpaidCount = accounts.length === 0
    ? 0
    : Object.values(billData).filter(b => b?.status === 'unpaid').length

  // Load all accounts from backend profiles on mount
  useEffect(() => {
    const loadAccounts = async () => {
      setInitialLoading(true)
      try {
        const { data: allProfiles } = await profilesApi.getAll()
        const allAccounts = []
        for (const profile of allProfiles) {
          if (profile.accounts && profile.accounts.length > 0) {
            for (const acc of profile.accounts) {
              allAccounts.push({
                ...acc,
                profile_id: profile.id,
              })
            }
          }
        }
        setAccounts(allAccounts)
      } catch (err) {
        console.error('Failed to load accounts:', err)
      } finally {
        setInitialLoading(false)
      }
    }
    loadAccounts()
  }, [])

  // Auto-fetch bills for all accounts when they load
  const fetchBillForAccount = useCallback(async (account) => {
    setLoadingAccounts(p => ({ ...p, [account.id]: true }))
    try {
      const numberPlate = account.service_type === 'echallan' ? (account.number_plate || account.consumer_id) : null
      const { data } = await utilitiesApi.fetchBill(account.service_type, account.consumer_id, numberPlate)
      setBillData(p => ({ ...p, [account.id]: data }))
    } catch (err) {
      console.error(`Failed to fetch bill for ${account.consumer_id}:`, err)
      setBillData(p => ({ ...p, [account.id]: { amount_due: 0, status: 'unknown', error: true } }))
    } finally {
      setLoadingAccounts(p => ({ ...p, [account.id]: false }))
    }
  }, [])

  useEffect(() => {
    if (accounts.length > 0) {
      accounts.forEach(account => {
        if (!billData[account.id]) {
          fetchBillForAccount(account)
        }
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accounts])

  // Persist layout state for instant load on refresh
  useEffect(() => {
    if (accounts.length > 0 && Object.keys(billData).length > 0) {
      saveCachedLayout(accounts, billData)
    }
  }, [accounts, billData])

  // Chart data state - fetched from backend to avoid data fabrication
  const [comparisonData, setComparisonData] = useState([])
  const [trendData, setTrendData] = useState([])
  const [trendLines, setTrendLines] = useState([])

  // Fetch chart data from backend when accounts or billData change
  useEffect(() => {
    const fetchChartData = async () => {
      if (accounts.length === 0) {
        setComparisonData([])
        setTrendData([])
        setTrendLines([])
        return
      }
      
      // Only fetch when we have bill data loaded
      const loadedBills = Object.keys(billData).filter(id => !loadingAccounts[id])
      if (loadedBills.length === 0) return
      
      try {
        const { data } = await utilitiesApi.getChartData(accounts, billData)
        setComparisonData(data.comparison_data || [])
        setTrendData(data.trend_data || [])
        setTrendLines(data.trend_lines || [])
      } catch (err) {
        console.error('Failed to fetch chart data:', err)
        // Fallback to local computation for comparison only (no trend fabrication)
        const serviceTypes = [...new Set(accounts.map(a => a.service_type))]
        const comparison = serviceTypes.map(type => {
          const meta = SERVICE_CHART_META[type] || { name: type, fill: '#94a3b8' }
          const totalAmount = accounts
            .filter(a => a.service_type === type)
            .reduce((sum, a) => sum + (billData[a.id]?.amount_due || 0), 0)
          return { service: meta.name, amount: totalAmount, fill: meta.fill }
        })
        setComparisonData(comparison)
        // No trend data if backend fails - zero fabrication policy
        setTrendData([])
        setTrendLines([])
      }
    }
    
    fetchChartData()
  }, [accounts, billData, loadingAccounts])

  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    if (location.hash === '#add') {
      setIsAddModalOpen(true)
      navigate(location.pathname, { replace: true })
    }
  }, [location, navigate])

  const handleRefresh = async (account) => {
    await fetchBillForAccount(account)
  }

  const handlePayNow = (account) => {
    setSelectedAccount(account)
    const bill = billData[account.id]
    if (!bill || bill.status === 'paid' || !bill.amount_due) return
    
    // Show QR modal immediately with default QR code
    setQrCode('')
    setIsQRModalOpen(true)
    
    // Fetch real QR in background (non-blocking)
    paymentsApi.initiate(account.id, account.service_type, account.consumer_id)
      .then(({ data }) => {
        if (data.qr_code_base64) {
          setQrCode(data.qr_code_base64)
        }
      })
      .catch(() => {
        // Keep showing default QR on error
      })
  }

  const handleViewHistory = async (account) => {
    setSelectedAccount(account)
    setIsHistoryModalOpen(true)
    setHistoryLoading(true)
    try {
      const { data } = await utilitiesApi.getHistory(account.service_type, account.consumer_id)
      setHistory(data)
    } catch {
      setHistory([])
    } finally {
      setHistoryLoading(false)
    }
  }

  const handlePaymentComplete = useCallback(() => {
    // After payment, refresh the bill for the selected account
    if (selectedAccount) {
      const accountId = selectedAccount.id
      // Immediately update the bill as paid
      setBillData(prev => {
        const updated = {
          ...prev,
          [accountId]: {
            ...prev[accountId],
            amount_due: 0,
            status: 'paid'
          }
        }
        // Also update the cache
        saveCachedLayout(accounts, updated)
        return updated
      })
    }
  }, [selectedAccount, accounts])

  const handleRemoveAccount = async (account) => {
    // Remove the account from backend and update state
    try {
      await profilesApi.removeAccount(account.profile_id, account.id)
    } catch (err) {
      console.error('Failed to remove account:', err)
    }
    setAccounts(prev => prev.filter(a => a.id !== account.id))
    setBillData(prev => {
      const copy = { ...prev }
      delete copy[account.id]
      return copy
    })
    // Update cache
    saveCachedLayout(accounts.filter(a => a.id !== account.id), billData)
  }

  const handleAddAccount = async (account) => {
    // Add the account to the backend profile
    try {
      const { data: newAcc } = await profilesApi.addAccount(account.profile_id, {
        service_type: account.service_type,
        consumer_id: account.consumer_id,
        label: account.label,
        profile_id: account.profile_id,
      })
      setAccounts(p => [...p, newAcc])

      // Link account to profile in local context
      if (account.profile_id) {
        linkAccount(account.profile_id, newAcc.id)
      }

      // Immediately fetch bill data via browser agent
      fetchBillForAccount(newAcc)
    } catch (err) {
      console.error('Failed to add account:', err)
      // Fallback: add locally
      const fallbackAcc = { ...account, id: Date.now().toString() }
      setAccounts(p => [...p, fallbackAcc])
      if (account.profile_id) {
        linkAccount(account.profile_id, fallbackAcc.id)
      }
      fetchBillForAccount(fallbackAcc)
    }
  }

  return (
    <div className="py-8 md:py-12 page-enter">
      <div className="max-w-[1400px] mx-auto px-6">
        {/* Header row */}
        <div className="mb-6 animate-fade-in flex items-center gap-4">
          <img src="/logo.jpg" alt="Logo" className="w-12 h-12 rounded-xl shadow-lg border border-white/10 bg-white/10" />
          <div>
            <h1 className="text-4xl font-bold text-white tracking-tight mb-2 drop-shadow-md">Dashboard</h1>
            <p className="text-slate-400 font-medium">Manage your Kerala utility bills seamlessly</p>
          </div>
        </div>

        {/* Unified 3-Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-10 items-start">

          {/* Left 2 Columns: Stats + Utility Grid + Charts (when ≤2 accounts) */}
          <div className="lg:col-span-2 flex flex-col gap-6">

            {initialLoading ? (
              <div className="bg-black/60 backdrop-blur-2xl border-white/10 rounded-2xl p-10 flex flex-col items-center justify-center text-center min-h-[300px]">
                <div className="bars-4 mb-4"></div>
                <p className="text-slate-400 text-sm font-medium">Loading your accounts...</p>
              </div>
            ) : accounts.length === 0 ? (
              /* Empty state */
              profiles.length === 0 ? (
                /* No profiles exist - prompt to create one first */
                <div className="bg-black/60 backdrop-blur-2xl border-white/10 rounded-2xl p-10 flex flex-col items-center justify-center text-center min-h-[300px]">
                  <div className="w-16 h-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center mb-4">
                    <UserCircle2 size={28} className="text-primary" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">Create a profile first</h3>
                  <p className="text-slate-400 text-sm mb-6 max-w-sm">
                    Set up a profile (e.g. Home, Office) before adding your utility bills.
                  </p>
                  <button
                    onClick={() => navigate('/profiles')}
                    className="flex items-center gap-2 bg-primary hover:bg-orange-600 text-white rounded-xl px-5 py-3 font-bold text-sm shadow-[0_4px_20px_rgba(217,119,6,0.3)] transition-all hover:-translate-y-0.5"
                  >
                    <Plus size={16} /> Go to Profiles
                  </button>
                </div>
              ) : (
                /* Profiles exist but no bills yet */
                <div className="bg-black/60 backdrop-blur-2xl border-white/10 rounded-2xl p-10 flex flex-col items-center justify-center text-center min-h-[300px]">
                  <div className="w-16 h-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center mb-4">
                    <Wallet size={28} className="text-primary" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">No bills yet</h3>
                  <p className="text-slate-400 text-sm mb-6 max-w-sm">
                    Add your first utility bill to start tracking payments and usage.
                  </p>
                  <button
                    onClick={() => setIsAddModalOpen(true)}
                    className="flex items-center gap-2 bg-primary hover:bg-orange-600 text-white rounded-xl px-5 py-3 font-bold text-sm shadow-[0_4px_20px_rgba(217,119,6,0.3)] transition-all hover:-translate-y-0.5"
                  >
                    <Plus size={16} /> Add Your First Bill
                  </button>
                </div>
              )
            ) : (
              <>
                {/* Stat Cards Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-black/60 backdrop-blur-2xl border-white/10 rounded-2xl p-4 flex flex-col gap-3 relative overflow-hidden group h-[130px] justify-center">
                    <div className="absolute -right-6 -top-6 w-24 h-24 bg-white/5 rounded-full filter blur-xl group-hover:bg-primary/10 transition-colors"></div>
                    <div className="w-10 h-10 rounded-xl bg-black/40 border border-white/5 flex items-center justify-center shrink-0 shadow-inner">
                      <Wallet size={18} className="text-primary" />
                    </div>
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 tracking-[0.1em] uppercase mb-1">TOTAL DUE</p>
                      <p className={`text-2xl font-extrabold tracking-tight ${totalDue > 0 ? 'text-red-400' : 'text-green-400'}`}>₹{totalDue.toLocaleString()}</p>
                    </div>
                  </div>

                  <div className="bg-black/60 backdrop-blur-2xl border-white/10 rounded-2xl p-4 flex flex-col gap-3 relative overflow-hidden group h-[130px] justify-center">
                    <div className="absolute -right-6 -top-6 w-24 h-24 bg-white/5 rounded-full filter blur-xl group-hover:bg-primary/10 transition-colors"></div>
                    <div className="w-10 h-10 rounded-xl bg-black/40 border border-white/5 flex items-center justify-center shrink-0 shadow-inner">
                      <Clock size={18} className="text-orange-400" />
                    </div>
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 tracking-[0.1em] uppercase mb-1">UNPAID BILLS</p>
                      <p className="text-2xl font-extrabold text-white tracking-tight">{unpaidCount}</p>
                    </div>
                  </div>
                </div>

                {/* Utility Cards Grid - equal height */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-stagger">
                  {accounts.map((account, index) => (
                    <div key={account.id} className="h-[260px]" style={{ animationDelay: `${index * 50}ms` }}>
                      <UtilityCard
                        account={account}
                        billData={billData[account.id]}
                        isLoading={loadingAccounts[account.id]}
                        onRefresh={() => handleRefresh(account)}
                        onPayNow={handlePayNow}
                        onViewHistory={handleViewHistory}
                        onRemove={handleRemoveAccount}
                      />
                    </div>
                  ))}
                </div>

                {/* Charts INSIDE left column when 1-2 accounts */}
                {accounts.length <= 2 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-black/60 backdrop-blur-2xl border-white/10 rounded-2xl p-6 relative overflow-hidden animate-fade-in-up card-lift" style={{ animationDelay: '100ms' }}>
                      <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full filter blur-[80px] pointer-events-none"></div>
                      <p className="text-xs font-bold text-slate-400 tracking-widest uppercase mb-6 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
                        Current Amounts by Service
                      </p>
                      <div className="relative z-10 w-full overflow-hidden">
                        <ServiceComparisonChart data={comparisonData} />
                      </div>
                    </div>

                    <div className="bg-black/60 backdrop-blur-2xl border-white/10 rounded-2xl p-6 relative overflow-hidden animate-fade-in-up card-lift" style={{ animationDelay: '150ms' }}>
                      <div className="absolute bottom-0 left-0 w-64 h-64 bg-accent-cyan/5 rounded-full filter blur-[80px] pointer-events-none"></div>
                      <p className="text-xs font-bold text-slate-400 tracking-widest uppercase mb-6 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-accent-cyan animate-pulse"></span>
                        {trendData.length > 0 ? 'Billing History' : 'No History Available'}
                      </p>
                      <div className="relative z-10 w-full overflow-hidden">
                        {trendData.length > 0 ? (
                          <MonthlyTrendChart data={trendData} lines={trendLines} />
                        ) : (
                          <div className="h-[220px] flex items-center justify-center text-slate-500 text-sm">
                            Historical data will appear here once available
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Right Column: Quick Access + Chatbot + Live Map */}
          <div className="flex flex-col gap-6">
            <div className="h-[200px]">
              <QuickAccessPanel onAddBillsClick={() => setIsAddModalOpen(true)} />
            </div>
            <div className="h-[320px]">
              <DisasterChatbot onIncidentReported={() => {}} />
            </div>
            <div className="h-[350px] lg:flex-1 min-h-[300px]">
              <DashboardMap />
            </div>
          </div>
        </div>

        {/* Charts BELOW grid when >2 accounts */}
        {accounts.length > 2 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-black/60 backdrop-blur-2xl border-white/10 rounded-2xl p-6 relative overflow-hidden animate-fade-in-up card-lift" style={{ animationDelay: '200ms' }}>
              <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full filter blur-[80px] pointer-events-none"></div>
              <p className="text-xs font-bold text-slate-400 tracking-widest uppercase mb-6 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
                Current Amounts by Service
              </p>
              <div className="relative z-10 w-full overflow-hidden">
                <ServiceComparisonChart data={comparisonData} />
              </div>
            </div>

            <div className="bg-black/60 backdrop-blur-2xl border-white/10 rounded-2xl p-6 relative overflow-hidden animate-fade-in-up card-lift" style={{ animationDelay: '250ms' }}>
              <div className="absolute bottom-0 left-0 w-64 h-64 bg-accent-cyan/5 rounded-full filter blur-[80px] pointer-events-none"></div>
              <p className="text-xs font-bold text-slate-400 tracking-widest uppercase mb-6 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-accent-cyan animate-pulse"></span>
                {trendData.length > 0 ? 'Billing History' : 'No History Available'}
              </p>
              <div className="relative z-10 w-full overflow-hidden">
                {trendData.length > 0 ? (
                  <MonthlyTrendChart data={trendData} lines={trendLines} />
                ) : (
                  <div className="h-[220px] flex items-center justify-center text-slate-500 text-sm">
                    Historical data will appear here once available
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      <AddAccountModal isOpen={isAddModalOpen} onClose={() => setIsAddModalOpen(false)} onAdd={handleAddAccount} profiles={profiles} existingAccounts={accounts} />
      <QRModal isOpen={isQRModalOpen} onClose={() => setIsQRModalOpen(false)} qrCode={qrCode} serviceName={selectedAccount?.label} amount={billData[selectedAccount?.id]?.amount_due} onPaymentComplete={handlePaymentComplete} />
      <HistoryModal isOpen={isHistoryModalOpen} onClose={() => setIsHistoryModalOpen(false)} account={selectedAccount} history={history} isLoading={historyLoading} />
    </div>
  )
}
