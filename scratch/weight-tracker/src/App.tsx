import { useState } from 'react'
import { Loader2, LogOut } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { AppShell, type TabKey } from '@/components/layout/app-shell'
import { isPreviewMode } from '@/lib/env'
import { useAuth } from '@/features/auth/auth-context'
import { LoginPage } from '@/pages/login-page'
import { RecordPage } from '@/pages/record-page'
import { ChartPage } from '@/pages/chart-page'
import { HistoryPage } from '@/pages/history-page'

export default function App() {
  const { status, signOut } = useAuth()
  // 画面切替はルーターを使わず state で持つ（3画面のみのため）
  const [tab, setTab] = useState<TabKey>('record')

  if (status === 'loading') {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Loader2 className="text-muted-foreground size-6 animate-spin" />
      </div>
    )
  }

  if (status === 'unauthenticated') {
    return <LoginPage />
  }

  const headerAction = isPreviewMode ? (
    <span className="bg-muted text-muted-foreground rounded-full px-2.5 py-1 text-xs font-medium">
      プレビュー
    </span>
  ) : (
    <Button variant="ghost" size="sm" onClick={() => signOut()} aria-label="ログアウト">
      <LogOut className="size-4" />
      ログアウト
    </Button>
  )

  return (
    <AppShell tab={tab} onTabChange={setTab} headerAction={headerAction}>
      {tab === 'record' && <RecordPage />}
      {tab === 'chart' && <ChartPage />}
      {tab === 'history' && <HistoryPage />}
    </AppShell>
  )
}
