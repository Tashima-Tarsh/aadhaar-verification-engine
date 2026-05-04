'use client'

import { useState, useEffect } from 'react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import api from '@/lib/api'

interface Summary {
  total_verifications: number
  completed: number
  failed: number
  risk_breakdown: Record<string, number>
  avg_processing_time_ms: number
  period_days: number
}

const RISK_COLORS: Record<string, string> = {
  LOW: '#22c55e',
  MEDIUM: '#f59e0b',
  HIGH: '#ef4444',
  UNKNOWN: '#94a3b8',
}

export default function ReportsPage() {
  const [days, setDays] = useState(30)
  const [summary, setSummary] = useState<Summary | null>(null)
  const [loading, setLoading] = useState(false)

  const fetchSummary = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/reports/summary?days=${days}`)
      setSummary(res.data)
    } catch {}
    setLoading(false)
  }

  useEffect(() => { fetchSummary() }, [days])

  const exportCsv = () => {
    const token = localStorage.getItem('access_token') || ''
    window.open(`/api/v1/reports/export/csv?days=${days}`, '_blank')
  }

  const pieData = summary
    ? Object.entries(summary.risk_breakdown).map(([name, value]) => ({ name, value }))
    : []

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <div className="flex gap-3">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="border rounded-xl px-4 py-2 text-sm"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>
          <button
            onClick={exportCsv}
            className="px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700"
          >
            Export CSV
          </button>
        </div>
      </div>

      {loading && <div className="text-gray-400 text-center py-10">Loading…</div>}

      {summary && !loading && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Total', value: summary.total_verifications, color: 'bg-blue-50 text-blue-700' },
              { label: 'Completed', value: summary.completed, color: 'bg-green-50 text-green-700' },
              { label: 'Failed', value: summary.failed, color: 'bg-red-50 text-red-700' },
              { label: 'Avg Time', value: `${Math.round(summary.avg_processing_time_ms)}ms`, color: 'bg-purple-50 text-purple-700' },
            ].map(({ label, value, color }) => (
              <div key={label} className={`p-5 rounded-xl ${color} font-semibold`}>
                <p className="text-2xl">{value}</p>
                <p className="text-sm opacity-70">{label}</p>
              </div>
            ))}
          </div>

          <div className="bg-white border rounded-xl p-6">
            <h2 className="font-semibold mb-4">Risk Distribution</h2>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label>
                    {pieData.map((entry) => (
                      <Cell key={entry.name} fill={RISK_COLORS[entry.name] || '#94a3b8'} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-400 text-center py-8">No data for this period</p>
            )}
          </div>
        </>
      )}
    </div>
  )
}
