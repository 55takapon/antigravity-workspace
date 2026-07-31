import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { formatDateTime, toDateTimeLocalValue } from '@/lib/date'
import { useCreateWeight, useWeightHistory } from '@/features/weights/queries'
import { WeightDelta } from '@/features/weights/weight-delta'
import {
  WeightFormFields,
  toWeightInput,
  weightFormSchema,
  type WeightFormValues,
} from '@/features/weights/weight-form'

export function RecordPage() {
  const history = useWeightHistory()
  const createWeight = useCreateWeight()

  const records = history.data?.pages.flat() ?? []
  const latest = records[0]
  const previous = records[1]

  const form = useForm<WeightFormValues>({
    resolver: zodResolver(weightFormSchema),
    defaultValues: {
      weight: '',
      recordedAt: toDateTimeLocalValue(new Date()),
      note: '',
    },
  })

  const onSubmit = (values: WeightFormValues) => {
    createWeight.mutate(toWeightInput(values), {
      onSuccess: () => {
        toast.success('記録しました')
        form.reset({ weight: '', recordedAt: toDateTimeLocalValue(new Date()), note: '' })
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

      <Card className="border-white/8">
        <CardContent>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5" noValidate>
            <WeightFormFields form={form} idPrefix="record" />
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
