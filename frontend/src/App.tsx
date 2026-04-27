import { useState } from 'react'
import { Layout } from './components/layout/Layout'
import { UploadPage } from './components/pages/UploadPage'
import { AnalyzePage } from './components/pages/AnalyzePage'
import { SearchPage } from './components/pages/SearchPage'

type Page = 'upload' | 'analyze' | 'search'

export default function App() {
  const [page, setPage] = useState<Page>('upload')

  const pageMap: Record<Page, React.ReactNode> = {
    upload: <UploadPage />,
    analyze: <AnalyzePage />,
    search: <SearchPage />,
  }

  return (
    <Layout current={page} onNavigate={setPage}>
      {pageMap[page]}
    </Layout>
  )
}
