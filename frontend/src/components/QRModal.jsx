import { X } from 'lucide-react'
import { useState, useEffect } from 'react'

export default function QRModal({ isOpen, onClose, qrCode, serviceName, amount, onPaymentComplete }) {
  const [isLoading, setIsLoading] = useState(true)
  const [loadingProgress, setLoadingProgress] = useState(0)

  useEffect(() => {
    if (isOpen) {
      setIsLoading(true)
      setLoadingProgress(0)
      
      // Animate progress over 3.5 seconds
      const duration = 3500
      const interval = 50
      const steps = duration / interval
      let step = 0
      
      const progressTimer = setInterval(() => {
        step++
        setLoadingProgress(Math.min((step / steps) * 100, 100))
        if (step >= steps) {
          clearInterval(progressTimer)
        }
      }, interval)
      
      // Complete after 3.5 seconds
      const timer = setTimeout(() => {
        setIsLoading(false)
      }, duration)
      
      return () => {
        clearTimeout(timer)
        clearInterval(progressTimer)
      }
    }
  }, [isOpen])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm modal-backdrop"
        onClick={onClose}
      ></div>

      {/* Modal */}
      <div className="relative bg-slate-800 rounded-2xl border border-slate-700 
                      shadow-2xl max-w-sm w-full overflow-hidden modal-content">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-700">
          <div>
            <h3 className="text-lg font-semibold text-white">Scan to Pay</h3>
            <p className="text-slate-400 text-sm">{serviceName}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-slate-700/50 text-slate-400 
                       hover:text-white hover:bg-slate-700 transition-all duration-200 hover:rotate-90"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* QR Code Display */}
        <div className="p-8 flex flex-col items-center">
          <div className="bg-white p-4 rounded-xl relative">
            {isLoading ? (
              <div className="w-48 h-48 flex items-center justify-center">
                {/* Circular loading animation */}
                <div className="relative w-24 h-24">
                  {/* Background circle */}
                  <svg className="w-full h-full transform -rotate-90">
                    <circle
                      cx="48"
                      cy="48"
                      r="44"
                      stroke="#e2e8f0"
                      strokeWidth="6"
                      fill="none"
                    />
                    {/* Progress circle */}
                    <circle
                      cx="48"
                      cy="48"
                      r="44"
                      stroke="#d97706"
                      strokeWidth="6"
                      fill="none"
                      strokeLinecap="round"
                      strokeDasharray={`${2 * Math.PI * 44}`}
                      strokeDashoffset={`${2 * Math.PI * 44 * (1 - loadingProgress / 100)}`}
                      className="transition-all duration-75 ease-linear"
                    />
                  </svg>
                  {/* Percentage text */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-slate-600 font-bold text-sm">
                      {Math.round(loadingProgress)}%
                    </span>
                  </div>
                </div>
                <p className="absolute bottom-4 text-xs text-slate-500 font-medium">
                  Generating QR...
                </p>
              </div>
            ) : (
              <img 
                src={qrCode ? `data:image/png;base64,${qrCode}` : '/upi-qr.png'} 
                alt="Payment QR Code"
                className="w-48 h-48 object-contain animate-fade-in-scale"
              />
            )}
          </div>

          {/* Amount */}
          <div className="mt-6 text-center">
            <p className="text-slate-400 text-sm">Amount</p>
            <p className="text-3xl font-bold text-white">
              ₹{amount?.toLocaleString('en-IN') || 0}
            </p>
          </div>

          {/* Instructions */}
          <div className="mt-6 text-center text-sm text-slate-400">
            <p>Open your UPI app and scan this QR code</p>
            <p className="mt-1">Payment session expires in 5 minutes</p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-5 border-t border-slate-700 bg-slate-800/50">
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 py-2.5 px-4 rounded-xl bg-slate-700 text-white 
                         font-medium hover:bg-slate-600 transition-all"
            >
              Cancel
            </button>
            <button
              onClick={() => {
                if (onPaymentComplete) onPaymentComplete()
                onClose()
              }}
              disabled={isLoading}
              className="flex-1 py-2.5 px-4 rounded-xl bg-emerald-500 text-white 
                         font-medium hover:bg-emerald-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Payment Done
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
