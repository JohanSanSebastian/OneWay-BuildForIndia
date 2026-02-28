import { X, TrendingUp } from 'lucide-react'
import { BillingLineChart } from './Charts'

export default function HistoryModal({ isOpen, onClose, account, history, isLoading }) {
  if (!isOpen) return null

  const serviceNames = { kseb: 'KSEB', kwa: 'KWA', echallan: 'e-Challan', ksmart: 'K-Smart' }
  const chartData = history?.map(item => ({ date: item.date, amount: item.amount })) || []

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm modal-backdrop" onClick={onClose} />
      <div className="relative bg-[#0f1120] border border-[#1e2140] rounded-xl max-w-[680px] w-full max-h-[90vh] overflow-y-auto shadow-2xl modal-content">
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '18px 24px', borderBottom: '1px solid #1e2140', position: 'sticky', top: 0, background: '#0f1120' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 36, height: 36, background: 'rgba(99,102,241,0.12)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <TrendingUp size={18} color="#6366f1" />
            </div>
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: '#fff', margin: 0 }}>Billing History</h3>
              <p style={{ fontSize: 12, color: '#4a5270', margin: '2px 0 0' }}>
                {serviceNames[account?.service_type]} — {account?.label}
              </p>
            </div>
          </div>
          <button onClick={onClose} style={{ background: '#1e2140', border: 'none', borderRadius: 8, padding: 8, cursor: 'pointer', color: '#4a5270', display: 'flex', alignItems: 'center' }}>
            <X size={16} />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: '20px 24px' }}>
          {isLoading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200 }}>
              <div style={{ width: 36, height: 36, border: '3px solid #1e2140', borderTopColor: '#6366f1', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
              <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            </div>
          ) : (
            <>
              {/* Chart */}
              <div style={{ marginBottom: 24 }}>
                <p style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 14 }}>Monthly Trend</p>
                {chartData.length > 0
                  ? <BillingLineChart data={chartData} />
                  : <div style={{ height: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#4a5270', fontSize: 13 }}>No historical data</div>
                }
              </div>

              {/* Table */}
              <div>
                <p style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 14 }}>Transaction History</p>
                <div style={{ borderRadius: 8, border: '1px solid #1e2140', overflow: 'hidden' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ background: '#0a0b18' }}>
                        {['Date', 'Amount', 'Units', 'Status'].map(h => (
                          <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: '#4a5270', textTransform: 'uppercase', letterSpacing: 0.8 }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {history?.length > 0 ? history.map((item, i) => (
                        <tr key={i} style={{ borderTop: '1px solid #1e2140' }}>
                          <td style={{ padding: '12px 16px', fontSize: 13, color: '#94a3b8' }}>{item.date}</td>
                          <td style={{ padding: '12px 16px', fontSize: 13, fontWeight: 700, color: '#fff' }}>₹{item.amount?.toLocaleString()}</td>
                          <td style={{ padding: '12px 16px', fontSize: 13, color: '#4a5270' }}>{item.units || item.units_consumed || '—'}</td>
                          <td style={{ padding: '12px 16px' }}>
                            <span className={`badge ${item.status === 'paid' ? 'badge-paid' : 'badge-unpaid'}`}>{item.status}</span>
                          </td>
                        </tr>
                      )) : (
                        <tr><td colSpan={4} style={{ padding: '24px', textAlign: 'center', color: '#4a5270', fontSize: 13 }}>No history available</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
