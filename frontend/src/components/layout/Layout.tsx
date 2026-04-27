import React from 'react'
import { Sidebar } from './Sidebar'

type Page = 'upload' | 'analyze' | 'search'

interface LayoutProps {
  current: Page
  onNavigate: (page: Page) => void
  children: React.ReactNode
}

const pageTitles: Record<Page, string> = {
  upload: 'Upload Document',
  analyze: 'AI Analysis',
  search: 'Document Search',
}

export function Layout({ current, onNavigate, children }: LayoutProps) {
  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      <Sidebar current={current} onNavigate={onNavigate} />

      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="bg-white border-b border-slate-200 px-8 py-4 flex-shrink-0">
          <h1 className="text-lg font-semibold text-slate-800">{pageTitles[current]}</h1>
        </header>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto p-8">
          {children}
        </main>
      </div>
    </div>
  )
}
