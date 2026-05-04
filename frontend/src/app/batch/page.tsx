'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import api from '@/lib/api'

interface BatchJob {
  job_id: string
  status: string
  total_count: number
  completed_count: number
  failed_count: number
}

export default function BatchPage() {
  const [files, setFiles] = useState<File[]>([])
  const [loading, setLoading] = useState(false)
  const [job, setJob] = useState<BatchJob | null>(null)
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback((dropped: File[]) => {
    setFiles((prev) => [...prev, ...dropped].slice(0, 500))
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': [], 'application/pdf': [], 'text/xml': [] },
    maxFiles: 500,
  })

  const pollJob = async (jobId: string) => {
    for (let i = 0; i < 60; i++) {
      await new Promise((r) => setTimeout(r, 3000))
      try {
        const res = await api.get(`/batch/${jobId}/status`)
        setJob(res.data)
        if (res.data.status === 'COMPLETED' || res.data.status === 'FAILED') return
      } catch {}
    }
  }

  const handleSubmit = async () => {
    if (!files.length) return
    setLoading(true)
    setError(null)

    const form = new FormData()
    files.forEach((f) => form.append('files', f))

    try {
      const res = await api.post('/batch', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setJob(res.data)
      await pollJob(res.data.job_id)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Submission failed')
    } finally {
      setLoading(false)
    }
  }

  const progress = job ? Math.round(((job.completed_count + job.failed_count) / (job.total_count || 1)) * 100) : 0

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Bulk Verification</h1>
      <p className="text-gray-500 text-sm">Upload up to 500 Aadhaar documents at once</p>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition ${
          isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'
        }`}
      >
        <input {...getInputProps()} />
        <p className="text-gray-500">
          {files.length ? `${files.length} file(s) selected` : 'Drop Aadhaar images / PDFs / XMLs here'}
        </p>
      </div>

      {files.length > 0 && (
        <div className="text-sm text-gray-600 max-h-32 overflow-y-auto">
          {files.map((f, i) => <div key={i}>{f.name}</div>)}
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={!files.length || loading}
        className="w-full py-3 bg-blue-600 text-white rounded-xl font-semibold disabled:opacity-50 hover:bg-blue-700"
      >
        {loading ? 'Processing…' : 'Submit Batch'}
      </button>

      {error && <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">{error}</div>}

      {job && (
        <div className="p-6 bg-white border rounded-xl shadow space-y-4">
          <div className="flex justify-between">
            <span className="font-medium">Job {job.job_id.slice(0, 8)}…</span>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              job.status === 'COMPLETED' ? 'bg-green-100 text-green-700' :
              job.status === 'FAILED' ? 'bg-red-100 text-red-700' :
              'bg-yellow-100 text-yellow-700'
            }`}>{job.status}</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-3">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="flex justify-between text-sm text-gray-600">
            <span>{job.completed_count} completed</span>
            <span>{job.failed_count} failed</span>
            <span>{job.total_count} total</span>
          </div>
        </div>
      )}
    </div>
  )
}
