import { useRef, useState } from 'react'
import { uploadCsv, type UploadResult } from '../adminApi'

interface Props {
  onClose: () => void
  onDone: () => void
}

export function CsvUpload({ onClose, onDone }: Props) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<UploadResult | null>(null)
  const [error, setError] = useState('')

  async function handleUpload() {
    if (!file) return
    setUploading(true)
    setError('')
    setResult(null)
    try {
      const res = await uploadCsv(file)
      setResult(res)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Upload failed'
      try {
        const parsed = JSON.parse(msg)
        if (parsed.errors) {
          setError(`Validation failed: ${parsed.errors.length} error(s)`)
          setResult({ added: 0, skipped: 0, skipped_names: [], embedded: 0, errors: parsed.errors })
          return
        }
      } catch { /* not JSON */ }
      setError(msg)
    } finally {
      setUploading(false)
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] ?? null
    setFile(f)
    setResult(null)
    setError('')
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Upload Products CSV</h2>
        <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', margin: '0 0 16px' }}>
          Required columns: name, category, price, stock. Optional: brand, short_description, description, tags (comma-separated), specs (JSON).
        </p>

        <div className="upload-area" onClick={() => fileRef.current?.click()}>
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            onChange={handleFileChange}
          />
          {file ? (
            <span style={{ fontWeight: 600, color: 'var(--text)' }}>{file.name}</span>
          ) : (
            <span>Click to select a .csv file</span>
          )}
        </div>

        {error && <div style={{ marginTop: 12, color: 'var(--bad)', fontSize: '0.9rem' }}>{error}</div>}

        {result && !error && (
          <div className="upload-result">
            <p className="success">
              {result.added} added, {result.skipped} skipped
              {result.embedded > 0 ? `, ${result.embedded} embedded` : ''}
            </p>
            {result.skipped_names.length > 0 && (
              <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', margin: '8px 0 0' }}>
                Skipped (already exist): {result.skipped_names.join(', ')}
              </p>
            )}
          </div>
        )}

        {result?.errors && result.errors.length > 0 && (
          <ul className="upload-errors">
            {result.errors.map((e, i) => (
              <li key={i}>Row {e.row}: {e.reason}</li>
            ))}
          </ul>
        )}

        <div className="modal-actions">
          {result && !error ? (
            <button type="button" className="btn btn-accent btn-sm" onClick={onDone}>Done</button>
          ) : (
            <>
              <button
                type="button"
                className="btn btn-accent btn-sm"
                disabled={!file || uploading}
                onClick={handleUpload}
              >
                {uploading ? <><span className="spinner" /> Uploading...</> : 'Upload'}
              </button>
              <button type="button" className="btn btn-outline btn-sm" onClick={onClose}>Cancel</button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
