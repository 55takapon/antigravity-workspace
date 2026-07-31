import { useEffect, useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { formatDateTime, toDateKey, toDateTimeLocalValue } from '@/lib/date'
import { toDailyPoints } from '@/features/weights/chart-data'
import { useCreateWeight, useWeightHistory } from '@/features/weights/queries'
import type { WeightRecord } from '@/features/weights/types'
import { WeightDelta } from '@/features/weights/weight-delta'
import {
  WeightFormFields,
  toWeightInput,
  weightFormSchema,
  type WeightFormValues,
} from '@/features/weights/weight-form'

/** 記録がまだ1件もないときのスライダー初期値 */
const DEFAULT_WEIGHT_KG = 60

// 今日はヒーローに大きく出ているので、ここでは おととい → 昨日 の2つだけ
const RECENT_DAYS = [
  { label: 'おととい', offset: 2 },
  { label: '昨日', offset: 1 },
]

/** おととい・昨日の体重を、記録が無い日は null で並べる */
function useRecentDays(records: WeightRecord[]) {
  return useMemo(() => {
    // toDailyPoints は昇順を期待するため、新しい順の records を反転させる
    const daily = toDailyPoints([...records].reverse())
    const byDateKey = new Map(daily.map((point) => [point.dateKey, point.weight]))

    const today = new Date()
    today.setHours(0, 0, 0, 0)

    return RECENT_DAYS.map(({ label, offset }) => {
      const date = new Date(today)
      date.setDate(date.getDate() - offset)
      return { label, weight: byDateKey.get(toDateKey(date)) ?? null }
    })
  }, [records])
}

export function RecordPage() {
  const history = useWeightHistory()
  const createWeight = useCreateWeight()

  const records = history.data?.pages.flat() ?? []
  const latest = records[0]
  const previous = records[1]
  const recentDays = useRecentDays(records)

  const form = useForm<WeightFormValues>({
    resolver: zodResolver(weightFormSchema),
    defaultValues: {
      weight: DEFAULT_WEIGHT_KG,
      recordedAt: toDateTimeLocalValue(new Date()),
      note: '',
    },
  })

  // 直近の体重が読み込まれたら、まだ操作していない場合に限りスライダーの初期位置をそこに合わせる
  useEffect(() => {
    if (latest && !form.formState.isDirty) {
      form.setValue('weight', latest.weight_kg)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [latest?.weight_kg])

  const onSubmit = (values: WeightFormValues) => {
    // 日時はスマホの内部時計から自動取得する（記録画面では編集不可）
    const input = toWeightInput({ ...values, recordedAt: toDateTimeLocalValue(new Date()) })

    createWeight.mutate(input, {
      onSuccess: () => {
        toast.success('記録しました')
        form.reset({ weight: values.weight, recordedAt: toDateTimeLocalValue(new Date()), note: '' })
      },
      onError: (error) => {
        toast.error('保存に失敗しました', {
          description: error instanceof Error ? error.message : undefined,
        })
      },
    })
  }

  return (
    <div className="space-y-4">
      <Card className="relative overflow-hidden border-white/8">
        {/* カード内側の光。装飾のみ */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              'radial-gradient(80% 120% at 50% -20%, color-mix(in oklab, var(--brand) 16%, transparent), transparent 65%)',
          }}
        />

        <CardContent className="relative flex flex-col items-center gap-1 py-3 text-center">
          <p className="text-muted-foreground text-[11px] font-medium tracking-[0.14em] uppercase">
            Latest
          </p>

          {history.isPending ? (
            <div className="bg-muted my-3 h-14 w-44 animate-pulse rounded-xl" />
          ) : latest ? (
            <>
              <div className="flex items-baseline gap-1.5">
                <span className="from-brand-bright via-foreground to-foreground bg-gradient-to-br bg-clip-text text-6xl leading-none font-semibold tracking-tight text-transparent">
                  {latest.weight_kg.toFixed(1)}
                </span>
                <span className="text-muted-foreground text-lg font-medium">kg</span>
              </div>

              <div className="mt-2.5 text-sm">
                <WeightDelta
                  variant="pill"
                  delta={previous ? latest.weight_kg - previous.weight_kg : null}
                />
              </div>

              <p className="text-muted-foreground mt-2 text-xs">
                {formatDateTime(latest.recorded_at)}
              </p>
            </>
          ) : (
            <p className="text-muted-foreground py-5 text-sm">
              まだ記録がありません。下から最初の1件を登録してください。
            </p>
          )}
        </CardContent>
      </Card>

      {!history.isPending && (
        <div className="grid grid-cols-2 gap-2">
          {recentDays.map(({ label, weight }) => (
            <div
              key={label}
              className="bg-card/50 ring-border/70 rounded-xl px-2 py-2 text-center ring-1"
            >
              <p className="text-muted-foreground text-[10px] font-medium tracking-wide">
                {label}
              </p>
              <p className="mt-0.5 text-sm font-semibold tabular-nums">
                {weight !== null ? (
                  <>
                    {weight.toFixed(1)}
                    <span className="text-muted-foreground ml-0.5 text-[10px] font-normal">
                      kg
                    </span>
                  </>
                ) : (
                  <span className="text-muted-foreground">—</span>
                )}
              </p>
            </div>
          ))}
        </div>
      )}

      <Card className="border-white/8">
        <CardContent>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5" noValidate>
            <WeightFormFields form={form} idPrefix="record" showDateTime={false} />
            <p className="text-muted-foreground -mt-2 text-center text-xs">
              日時は保存時のスマホの時刻が自動で使われます
            </p>
            <Button
              type="submit"
              className="from-brand-bright to-brand h-12 w-full bg-gradient-to-r text-base font-semibold shadow-[0_6px_24px_-8px_var(--brand)]"
              disabled={createWeight.isPending}
            >
              {createWeight.isPending ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Plus className="size-4" />
              )}
              記録する
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
