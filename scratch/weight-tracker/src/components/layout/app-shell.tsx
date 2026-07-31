import type { ReactNode } from 'react'
import { History, LineChart, Scale } from 'lucide-react'
import { cn } from '@/lib/utils'

/** 切り替え可能な3画面 */
export type TabKey = 'record' | 'chart' | 'history'

const NAV_ITEMS = [
  { key: 'record', label: '記録', icon: Scale },
  { key: 'chart', label: 'グラフ', icon: LineChart },
  { key: 'history', label: '履歴', icon: History },
] as const

type AppShellProps = {
  tab: TabKey
  onTabChange: (tab: TabKey) => void
  /** ヘッダー右側に置く要素（ログアウトなど） */
  headerAction?: ReactNode
  children: ReactNode
}

/**
 * 共通レイアウト。
 * モバイルファーストで、PCでは最大幅640pxのコンテナに中央寄せする。
 */
export function AppShell({ tab, onTabChange, headerAction, children }: AppShellProps) {
  return (
    <div className="relative min-h-dvh bg-background">
      {/* 画面上部のうっすらとしたオレンジの光。装飾のみ */}
      <div
        aria-hidden
        className="pointer-events-none fixed inset-x-0 top-0 h-72"
        style={{
          background:
            'radial-gradient(70% 100% at 50% 0%, color-mix(in oklab, var(--brand) 20%, transparent), transparent 70%)',
        }}
      />

      <header className="pt-safe sticky top-0 z-10 border-b border-border/70 bg-background/70 backdrop-blur-xl">
        <div className="mx-auto flex h-14 w-full max-w-160 items-center justify-between px-4">
          <div className="flex items-center gap-2.5">
            <span className="from-brand-bright to-brand-deep flex size-7 items-center justify-center rounded-lg bg-gradient-to-br shadow-[0_2px_12px_-2px_var(--brand)]">
              <Scale className="size-4 text-black/80" />
            </span>
            <h1 className="text-base font-semibold tracking-tight">体重記録</h1>
          </div>
          {headerAction}
        </div>
      </header>

      {/* 下部ナビゲーションと重ならないように余白を確保する */}
      <main className="relative mx-auto w-full max-w-160 px-4 pt-5 pb-28">{children}</main>

      <nav
        aria-label="メインナビゲーション"
        className="pb-safe fixed inset-x-0 bottom-0 z-10 border-t border-border/70 bg-background/80 backdrop-blur-xl"
      >
        <div className="mx-auto flex w-full max-w-160 items-stretch">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon
            const active = tab === item.key
            return (
              <button
                key={item.key}
                type="button"
                onClick={() => onTabChange(item.key)}
                aria-current={active ? 'page' : undefined}
                className={cn(
                  'relative flex flex-1 flex-col items-center gap-1 py-2.5 text-xs font-medium',
                  'transition-colors duration-200 active:scale-[0.97]',
                  active ? 'text-brand' : 'text-muted-foreground hover:text-foreground',
                )}
              >
                {/* アクティブなタブの上端に出るインジケーター */}
                <span
                  aria-hidden
                  className={cn(
                    'from-brand-bright to-brand absolute top-0 h-0.5 w-10 rounded-full bg-gradient-to-r transition-opacity duration-200',
                    active ? 'opacity-100' : 'opacity-0',
                  )}
                />
                <Icon
                  className={cn(
                    'size-5 transition-transform duration-200',
                    active && 'scale-110 drop-shadow-[0_0_8px_var(--brand)]',
                  )}
                />
                {item.label}
              </button>
            )
          })}
        </div>
      </nav>
    </div>
  )
}
