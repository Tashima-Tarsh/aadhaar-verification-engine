'use client'

import { useState } from 'react'
import api from '@/lib/api'

interface Result {
  request_id: string
  reference_id: string
  status: string
  name?: string
  dob?: string
  gender?: string
  masked_aadhaar?: string
  qr_valid?: boolean
  risk_score?: string
  image_quality_score?: number
  processing_time_ms?: number
  error_code?: string
  error_message?: string
  address?: {
    full?: string
    state?: string
    district?: string
    pincode?: string
    status: string
  }
}

export default function ResultsPage() {
  const [requestId, setRequestId] = useState('')
  const [result, setResult] = useState<Result | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const lookup = async () => {
    if (!requestId.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.get(`/verify/${requestId.trim()}/result`)
      setResult(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Not found')
    } finally {
      setLoading(false)
    }
  }

  const riskBadge = (r?: string) => {
    const map: Record<string, string> = {
      LOW: 'bg-green-100 text-green-700',
      MEDIUM: 'bg-yellow-100 text-yellow-700',
      HIGH: 'bg-red-100 text-red-700',
    }
    return map[r || ''] || 'bg-gray-100 text-gray-700'
  }

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Lookup Result</h1>

      <div className="flex gap-3">
        <input
          type="text"
          value={requestId}
          onChange={(e) => setRequestId(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && lookup()}
          placeholder="Enter Request ID (UUID)"
          className="flex-1 border rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={lookup}
          disabled={loading}
          className="px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold disabled:opacity-50 hover:bg-blue-700"
        >
          {loading ? '…' : 'Lookup'}
        </button>
      </div>

      {error && <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">{error}</div>}

      {result && (
        <div className="p-6 bg-white border rounded-xl shadow space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="font-semibold text-lg">Verification Details</h2>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              result.status === 'COMPLETED' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}>{result.status}</span>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            {result.name && <div><p className="text-gray-400">Full Name</p><p className="font-medium">{result.name}</p></div>}
            {result.dob && <div><p className="text-gray-400">Date of Birth</p><p className="font-medium">{result.dob}</p></div>}
            {result.gender && <div><p className="text-gray-400">Gender</p><p className="font-medium">{result.gender}</p></div>}
            {result.masked_aadhaar && <div><p className="text-gray-400">Aadhaar UID</p><p className="font-medium font-mono">{result.masked_aadhaar}</p></div>}
          </div>

          <div className="flex gap-3 flex-wrap">
            {result.qr_valid !== undefined && (
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${result.qr_valid ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                QR {result.qr_valid ? 'Valid' : 'Invalid'}
              </span>
            )}
            {result.risk_score && (
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${riskBadge(result.risk_score)}`}>
                Risk: {result.risk_score}
              </span>
            )}
          </div>

          {result.address?.full && (
            <div className="text-sm">
              <p className="text-gray-400 mb-1">Address</p>
              <p>{result.address.full}</p>
              {result.address.state && <p className="text-gray-500">{result.address.district}, {result.address.state} {result.address.pincode}</p>}
            </div>
          )}

          {result.processing_time_ms !== undefined && (
            <p className="text-xs text-gray-400">Processed in {result.processing_time_ms}ms</p>
          )}

          {result.error_message && (
            <div className="p-3 bg-red-50 rounded text-red-600 text-sm">
              {result.error_code && <span className="font-mono font-medium">[{result.error_code}] </span>}
              {result.error_message}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
