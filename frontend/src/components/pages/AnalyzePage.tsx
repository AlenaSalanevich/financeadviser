import { useState } from 'react'
import { api } from '../../api/client'
import type { SummaryResponse, RecommendationsResponse } from '../../types/api'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import { MarkdownRenderer } from '../ui/MarkdownRenderer'

type Mode = 'summary' | 'recommendations'

type Result = SummaryResponse | RecommendationsResponse | null

function isSummary(r: Result): r is SummaryResponse {
  return r !== null && 'summary' in r
}

export function AnalyzePage() {
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState<Mode>('summary')
  const [source, setSource] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<Result>(null)
  const [error, setError] = useState('')

  const canSubmit = query.trim().length >= 5 && !loading

  const handleSubmit = async () => {
    if (!canSubmit) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const req = {
        query: query.trim(),
        k: 5,
        source: source.trim() || null,
      }
      const data =
        mode === 'summary' ? await api.getSummary(req) : await api.getRecommendations(req)
      setResult(data)
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Request failed. Please try again.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const content = result ? (isSummary(result) ? result.summary : result.recommendations) : null

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <Card title="AI Financial Analysis">
        {/* Mode toggle */}
        <div className="flex gap-2 mb-5">
          {(['summary', 'recommendations'] as Mode[]).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                mode === m
                  ? 'bg-emerald-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {m === 'summary' ? '📊 Summary' : '💡 Recommendations'}
            </button>
          ))}
        </div>

        {/* Query input */}
        <label className="block text-sm font-medium text-slate-700 mb-1">
          Your question
        </label>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={
            mode === 'summary'
              ? 'e.g. Summarize my January spending…'
              : 'e.g. How can I reduce my monthly expenses?'
          }
          rows={3}
          maxLength={500}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none"
        />
        <div className="flex justify-between items-center mt-1 mb-4">
          <span className="text-xs text-slate-400">min 5 chars</span>
          <span className="text-xs text-slate-400">{query.length}/500</span>
        </div>

        {/* Optional source filter */}
        <label className="block text-sm font-medium text-slate-700 mb-1">
          Filter by document <span className="text-slate-400 font-normal">(optional)</span>
        </label>
        <input
          value={source}
          onChange={(e) => setSource(e.target.value)}
          placeholder="e.g. bank_statement_jan_2024.pdf"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />

        <div className="mt-5 flex justify-end">
          <Button onClick={handleSubmit} loading={loading} disabled={!canSubmit}>
            {loading ? 'Analyzing…' : mode === 'summary' ? 'Generate Summary' : 'Get Recommendations'}
          </Button>
        </div>
      </Card>

      {/* Error */}
      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-5 py-4 text-sm text-red-700">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Result */}
      {result && content && (
        <Card title={mode === 'summary' ? 'Spending Summary' : 'Financial Recommendations'}>
          {/* Metadata */}
          <div className="flex flex-wrap gap-3 mb-5">
            <Meta label="Model" value={result.model} />
            <Meta label="Documents analyzed" value={String(result.documents_used)} />
            {result.sources.length > 0 && (
              <Meta label="Sources" value={result.sources.join(', ')} />
            )}
          </div>

          {/* Markdown output */}
          <MarkdownRenderer content={content} />
        </Card>
      )}
    </div>
  )
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-slate-50 border border-slate-100 px-3 py-1.5">
      <span className="text-xs text-slate-400">{label}: </span>
      <span className="text-xs font-medium text-slate-600">{value}</span>
    </div>
  )
}
