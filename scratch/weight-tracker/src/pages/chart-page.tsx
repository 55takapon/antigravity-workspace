import { lazy, Suspense, useMemo, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import {
  PERIOD_OPTIONS,
  summarize,
  toDailyPoints,
  withMovingAverage,
  type PeriodKey,
} from '@/features/weights/chart-data'
import { useWeightRange } from '@/features/weights/queries'

// Recharts はこの画面に来たときだけ読み込む（初回バンドルを軽く保つため）
const WeightLineChart = lazy(() => import('@/features/weights/weight-line-chart'))

export function ChartPage() {
  const [period, setPeriod] = useState<PeriodKey>('30d')
  const range = useWeightRange(period)

  const dailyPoints = useMemo(() => toDailyPoints(range.data ?? []), [range.data])
  const chartPoints = useMemo(() => withMovingAverage(dailyPoints), [dailyPoints])
  const summary = useMemo(() => summarize(dailyPoints), [dailyPoints])

  return (
    <div className="space-y-4">
      <div className="bg-card ring-border/70 inline-flex w-full gap-1 rounded-xl p-1 ring-1">
        {PERIOD_OPTIONS.map((option) => (
          <button
            key={option.key}
            type="button"
            onClick={() => setPeriod(option.key)}
            className={cn(
              'flex-1 rounded-lg py-2 text-sm font-medium transition-colors',
              period === option.key
                ? 'bg-brand text-primary-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground',
            )}
          >
            {option.label}
          </button>
        ))}
      </div>

      {range.isPending ? (
        <div className="bg-muted h-72 animate-pulse rounded-xl" />
      ) : !summary ? (
        <Card className="border-white/8">
          <CardContent className="text-muted-foreground py-10 text-center text-sm">
            この期間の記録がありません
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-4 gap-2">
            <SummaryTile
              label="増減"
              value={`${summary.change > 0 ? '+' : summary.change < 0 ? '−' : '±'}${Math.abs(summary.change).toFixed(1)}`}
              emphasize
            />
            <SummaryTile label="最大" value={summary.max.toFixed(1)} />
            <SummaryTile label="最小" value={summary.min.toFixed(1)} />
            <SummaryTile label="平均" value={summary.average.toFixed(1)} />
          </div>

          <Card className="border-white/8">
            <CardContent className="px-2 pt-4">
              <Suspense
                fallback={
                  <div className="flex h-65 items-center justify-center">
                    <Loader2 className="text-muted-foreground size-5 animate-spin" />
                  </div>
                }
              >
                <WeightLineChart points={chartPoints} showMovingAverage={period !== '7d'} />
              </Suspense>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}

function SummaryTile({
  label,
  value,
  emphasize,
}: {
  label: string
  value: string
  emphasize?: boolean
}) {
  return (
    <div className="bg-card ring-border/70 rounded-xl px-2 py-2.5 text-center ring-1">
      <p className="text-muted-foreground text-[10px] font-medium tracking-wide">{label}</p>
      <p
        className={cn(
          'mt-0.5 text-sm font-semibold tabular-nums',
          emphasize && 'text-brand',
        )}
      >
        {value}
      </p>
    </div>
  )
}
