'use client'

import { useState } from 'react'
import styles from './dashboard.module.css'

export default function Dashboard() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleUpload = async () => {
    if (!file) return
    setLoading(true)
    
    const formData = new FormData()
    formData.append('file', file)
    formData.append('reference_id', `REF-${Date.now()}`)

    try {
      const response = await fetch('/api/v1/verify', {
        method: 'POST',
        headers: { 'X-API-Key': 'test_key' },
        body: formData
      })
      const data = await response.json()
      setResult(data)
    } catch (error) {
      console.error('Upload failed', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.logo}>AADHAAR INTEL</h1>
      </header>

      <main className={styles.main}>
        <section className={`${styles.card} glass-card`}>
          <h2>Identity Verification</h2>
          <div className={styles.dropzone}>
            <input 
              type="file" 
              onChange={(e) => setFile(e.target.files?.[0] || null)} 
              className={styles.fileInput}
            />
            <p>{file ? file.name : 'Click or drop Aadhaar document'}</p>
          </div>
          <button 
            onClick={handleUpload} 
            className={styles.button}
            disabled={loading || !file}
          >
            {loading ? 'Processing...' : 'Verify Now'}
          </button>
        </section>

        {result && (
          <section className={`${styles.card} glass-card ${styles.resultCard}`}>
            <div className={styles.resultHeader}>
              <h3>{result.name || 'Verification Result'}</h3>
              <span className={`${styles.badge} ${styles[result.risk_score?.toLowerCase()]}`}>
                {result.risk_score} Risk
              </span>
            </div>
            <div className={styles.grid}>
              <div className={styles.item}><label>Aadhaar</label><span>{result.masked_aadhaar}</span></div>
              <div className={styles.item}><label>Gender</label><span>{result.gender}</span></div>
              <div className={styles.item}><label>DOB</label><span>{result.dob}</span></div>
            </div>
            <div className={styles.address}>
              <label>Address</label>
              <p>{result.address?.full}</p>
            </div>
          </section>
        )}
      </main>
    </div>
  )
}
