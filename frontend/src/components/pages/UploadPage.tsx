import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { api } from '../../api/client'
import type { UploadResponse } from '../../types/api'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'

type Status = 'idle' | 'uploading' | 'success' | 'error'

export function UploadPage() {
  const [status, setStatus] = useState<Status>('idle')
  const [result, setResult] = useState<UploadResponse | null>(null)
  const [errorMsg, setErrorMsg] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length > 0) {
      setSelectedFile(accepted[0])
      setStatus('idle')
      setResult(null)
      setErrorMsg('')
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxSize: 50 * 1024 * 1024,
    multiple: false,
  })

  const handleUpload = async () => {
    if (!selectedFile) return
    setStatus('uploading')
    setErrorMsg('')
    try {
      const data = await api.uploadPdf(selectedFile)
      setResult(data)
      setStatus('success')
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Upload failed. Please try again.'
      setErrorMsg(msg)
      setStatus('error')
    }
  }

  const reset = () => {
    setStatus('idle')
    setResult(null)
    setErrorMsg('')
    setSelectedFile(null)
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Card title="Upload PDF Document">
        {/* Drop zone */}
        <div
          {...getRootProps()}
          className={`flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-emerald-400 bg-emerald-50'
              : 'border-slate-300 hover:border-emerald-400 hover:bg-slate-50'
          }`}
        >
          <input {...getInputProps()} />
          <div className="text-4xl mb-3">📄</div>
          {isDragActive ? (
            <p className="text-emerald-600 font-medium">Drop your PDF here</p>
          ) : (
            <>
              <p className="text-slate-600 font-medium">Drag & drop a PDF, or click to browse</p>
              <p className="mt-1 text-sm text-slate-400">PDF only · max 50 MB</p>
            </>
          )}
        </div>

        {/* Selected file */}
        {selectedFile && (
          <div className="mt-4 flex items-center justify-between rounded-lg bg-slate-50 border border-slate-200 px-4 py-3">
            <div>
              <p className="text-sm font-medium text-slate-700">{selectedFile.name}</p>
              <p className="text-xs text-slate-400">
                {(selectedFile.size / 1024).toFixed(1)} KB
              </p>
            </div>
            <Button variant="ghost" onClick={reset} className="text-slate-400 hover:text-slate-600">
              ✕
            </Button>
          </div>
        )}

        {/* Upload button */}
        <div className="mt-4 flex justify-end">
          <Button
            onClick={handleUpload}
            loading={status === 'uploading'}
            disabled={!selectedFile || status === 'uploading'}
          >
            {status === 'uploading' ? 'Uploading…' : 'Upload & Embed'}
          </Button>
        </div>
      </Card>

      {/* Success */}
      {status === 'success' && result && (
        <Card>
          <div className="flex items-start gap-4">
            <span className="text-3xl">✅</span>
            <div className="flex-1">
              <p className="font-semibold text-slate-800">Upload successful!</p>
              <p className="mt-1 text-sm text-slate-500">{result.message}</p>
              <div className="mt-3 grid grid-cols-2 gap-3">
                <Stat label="Filename" value={result.filename} />
                <Stat label="Chunks stored" value={String(result.chunks_stored)} />
                <Stat label="File size" value={`${(result.size_bytes / 1024).toFixed(1)} KB`} />
              </div>
              <Button variant="secondary" className="mt-4" onClick={reset}>
                Upload another
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Error */}
      {status === 'error' && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-5 py-4 text-sm text-red-700">
          <strong>Error:</strong> {errorMsg}
        </div>
      )}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-50 border border-slate-100 px-3 py-2">
      <p className="text-xs text-slate-400">{label}</p>
      <p className="text-sm font-medium text-slate-700 truncate">{value}</p>
    </div>
  )
}
