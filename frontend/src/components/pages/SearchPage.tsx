import { useState } from 'react'
import { api } from '../../api/client'
import type { DocumentResult } from '../../types/api'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'

export function SearchPage() {
  const [query, setQuery] = useState('')
  const [k, setK] = useState(5)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<DocumentResult[] | null>(null)
  const [error, setError] = useState('')
  const [searched, setSearched] = useState(false)

  const canSearch = query.trim().length >= 1 && !loading

  const handleSearch = async () => {
    if (!canSearch) return
    setLoading(true)
    setError('')
    setResults(null)
    setSearched(false)
    try {
      const data = await api.searchWithScores({ query: query.trim(), k })
      setResults(data.results)
      setSearched(true)
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Search failed. Please try again.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch()
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <Card title="Document Search">
        {/* Search input */}
        <label className="block text-sm font-medium text-slate-700 mb-1">Search query</label>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKey}
          placeholder="e.g. restaurant expenses, grocery spending…"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />

        {/* k slider */}
        <div className="mt-4">
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Results: <span className="text-emerald-600 font-semibold">{k}</span>
          </label>
          <input
            type="range"
            min={1}
            max={20}
            value={k}
            onChange={(e) => setK(Number(e.target.value))}
            className="w-full accent-emerald-600"
          />
          <div className="flex justify-between text-xs text-slate-400 mt-0.5">
            <span>1</span>
            <span>20</span>
          </div>
        </div>

        <div className="mt-5 flex justify-end">
          <Button onClick={handleSearch} loading={loading} disabled={!canSearch}>
            {loading ? 'Searching…' : 'Search'}
          </Button>
        </div>
      </Card>

      {/* Error */}
      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-5 py-4 text-sm text-red-700">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Results */}
      {searched && results !== null && (
        <div>
          <p className="text-sm text-slate-500 mb-3">
            {results.length > 0
              ? `Found ${results.length} result${results.length !== 1 ? 's' : ''}`
              : 'No results found'}
          </p>

          <div className="space-y-4">
            {results.map((r, i) => (
              <ResultCard key={i} doc={r} index={i + 1} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function ResultCard({ doc, index }: { doc: DocumentResult; index: number }) {
  const score = doc.score !== undefined ? doc.score.toFixed(4) : null
  const relevancePct =
    doc.score !== undefined
      ? Math.max(0, Math.min(100, Math.round((1 - doc.score) * 100)))
      : null

  return (
    <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-emerald-700 text-xs font-semibold">
            {index}
          </span>
          <span className="text-sm font-medium text-slate-700 truncate max-w-xs">
            {doc.source}
          </span>
          <span className="text-xs text-slate-400">· p.{doc.page}</span>
        </div>

        {score !== null && (
          <div className="text-right flex-shrink-0">
            <div className="text-xs text-slate-400">similarity</div>
            <div className="text-sm font-semibold text-emerald-600">{relevancePct}%</div>
            <div className="text-xs text-slate-300">(score {score})</div>
          </div>
        )}
      </div>

      {/* Content snippet */}
      <p className="text-sm text-slate-600 leading-relaxed line-clamp-4">
        {doc.content}
      </p>
    </div>
  )
}
