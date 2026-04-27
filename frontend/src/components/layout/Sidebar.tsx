type Page = 'upload' | 'analyze' | 'search'

interface SidebarProps {
  current: Page
  onNavigate: (page: Page) => void
}

const navItems: { id: Page; label: string; icon: string }[] = [
  { id: 'upload', label: 'Upload', icon: '📄' },
  { id: 'analyze', label: 'Analyze', icon: '🤖' },
  { id: 'search', label: 'Search', icon: '🔍' },
]

export function Sidebar({ current, onNavigate }: SidebarProps) {
  return (
    <aside className="flex h-screen w-56 flex-col bg-slate-900 text-slate-100 flex-shrink-0">
      {/* Brand */}
      <div className="px-6 py-5 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <span className="text-emerald-400 text-xl font-bold">₿</span>
          <span className="text-base font-semibold tracking-tight">FinanceAdviser</span>
        </div>
        <p className="mt-1 text-xs text-slate-400">AI-powered financial analysis</p>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ id, label, icon }) => (
          <button
            key={id}
            onClick={() => onNavigate(id)}
            className={`w-full flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
              current === id
                ? 'bg-emerald-600 text-white'
                : 'text-slate-300 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <span className="text-base">{icon}</span>
            {label}
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-slate-800">
        <p className="text-xs text-slate-500">v0.1.0</p>
      </div>
    </aside>
  )
}
