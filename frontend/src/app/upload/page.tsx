'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import api from '@/lib/api'

interface VerifyResult {
  request_id: string
  reference_id: string
  status: string
  name?: string
  dob?: string
  gender?: string
  masked_aadhaar?: string
  qr_valid?: boolean
  risk_score?: string
  processing_time_ms?: number
  error_message?: string
}

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<VerifyResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [polling, setPolling] = useState(false)

  const onDrop = useCallback((files: File[]) => {
    if (files[0]) setFile(files[0])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': [], 'application/pdf': [], 'text/xml': [] },
    maxFiles: 1,
  })

  const pollStatus = async (requestId: string) => {
    setPolling(true)
    for (let i = 0; i < 30; i++) {
      await new Promise((r) => setTimeout(r, 2000))
      try {
        const res = await api.get(`/verify/${requestId}/status`)
        if (res.data.status === 'COMPLETED' || res.data.status === 'FAILED') {
          setResult(res.data)
          setPolling(false)
          return
        }
      } catch {}
    }
    setPolling(false)
    setError('Verification timed out. Check results page later.')
  }

  const handleSubmit = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)

    const form = new FormData()
    form.append('file', file)
    form.append('reference_id', `REF-${Date.now()}`)

    try {
      const res = await api.post('/verify', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult(res.data)
      if (res.data.status === 'PENDING' || res.data.status === 'PROCESSING') {
        await pollStatus(res.data.request_id)
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Submission failed')
    } finally {
      setLoading(false)
    }
  }

  const riskColor = (r?: string) =>
    r === 'HIGH' ? 'text-red-600' : r === 'MEDIUM' ? 'text-yellow-600' : 'text-green-600'

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Single Verification</h1>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition ${
          isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'
        }`}
      >
        <input {...getInputProps()} />
        <p className="text-gray-500">
          {file ? file.name : 'Drop Aadhaar image / PDF / XML here, or click to browse'}
        </p>
      </div>

      <button
        onClick={handleSubmit}
        disabled={!file || loading}
        className="w-full py-3 bg-blue-600 text-white rounded-xl font-semibold disabled:opacity-50 hover:bg-blue-700"
      >
        {loading ? 'Processing…' : polling ? 'Polling…' : 'Verify Document'}
      </button>

      {error && <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">{error}</div>}

      {result && (
        <div className="p-6 bg-white border rounded-xl shadow space-y-3">
          <div className="flex justify-between items-center">
            <h2 className="font-semibold text-lg">Result</h2>
            <span
              className={`px-3 py-1 rounded-full text-sm font-medium ${
                result.status === 'COMPLETED' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              }`}
            >
              {result.status}
            </span>
          </div>
          {result.name && <p><span className="text-gray-500">Name:</span> {result.name}</p>}
          {result.dob && <p><span className="text-gray-500">DOB:</span> {result.dob}</p>}
          {result.gender && <p><span className="text-gray-500">Gender:</span> {result.gender}</p>}
          {result.masked_aadhaar && <p><span className="text-gray-500">UID:</span> {result.masked_aadhaar}</p>}
          {result.qr_valid !== undefined && (
            <p><span className="text-gray-500">QR Valid:</span> {result.qr_valid ? '✓ Yes' : '✗ No'}</p>
          )}
          {result.risk_score && (
            <p>
              <span className="text-gray-500">Risk:</span>{' '}
              <span className={`font-semibold ${riskColor(result.risk_score)}`}>{result.risk_score}</span>
            </p>
          )}
          {result.processing_time_ms !== undefined && (
            <p className="text-xs text-gray-400">Processed in {result.processing_time_ms}ms</p>
          )}
          {result.error_message && (
            <p className="text-red-600 text-sm">{result.error_message}</p>
          )}
        </div>
      )}
    </div>
  )
}
