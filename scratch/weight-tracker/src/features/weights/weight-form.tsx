import type { UseFormReturn } from 'react-hook-form'
import { z } from 'zod'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { WEIGHT_MAX_KG, WEIGHT_MIN_KG } from '@/lib/constants'
import { fromDateTimeLocalValue } from '@/lib/date'
import type { WeightInput } from '@/features/weights/types'

export const weightFormSchema = z.object({
  weight: z
    .string()
    .min(1, '体重を入力してください')
    .refine((value) => {
      const n = Number(value)
      return Number.isFinite(n) && n > WEIGHT_MIN_KG && n < WEIGHT_MAX_KG
    }, `${WEIGHT_MIN_KG}〜${WEIGHT_MAX_KG} kg の範囲で入力してください`),
  recordedAt: z.string().min(1, '日時を入力してください'),
  note: z.string().max(100, 'メモは100文字までです'),
})

export type WeightFormValues = z.infer<typeof weightFormSchema>

/** フォームの値を保存用の形へ変換する（体重は小数第1位に丸める） */
export function toWeightInput(values: WeightFormValues): WeightInput {
  return {
    weight_kg: Math.round(Number(values.weight) * 10) / 10,
    recorded_at: fromDateTimeLocalValue(values.recordedAt),
    note: values.note.trim() === '' ? null : values.note.trim(),
  }
}

/** 記録画面と編集モーダルで共通に使う入力欄 */
export function WeightFormFields({
  form,
  idPrefix,
}: {
  form: UseFormReturn<WeightFormValues>
  idPrefix: string
}) {
  const { errors } = form.formState

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor={`${idPrefix}-weight`}>体重</Label>
        <div className="relative">
          <Input
            id={`${idPrefix}-weight`}
            type="text"
            inputMode="decimal"
            autoComplete="off"
            placeholder="68.4"
            aria-invalid={Boolean(errors.weight)}
            className="h-14 pr-12 text-2xl font-semibold"
            {...form.register('weight')}
          />
          <span className="text-muted-foreground pointer-events-none absolute inset-y-0 right-4 flex items-center text-sm">
            kg
          </span>
        </div>
        {errors.weight && <p className="text-destructive text-xs">{errors.weight.message}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor={`${idPrefix}-recorded-at`}>日時</Label>
        <Input
          id={`${idPrefix}-recorded-at`}
          type="datetime-local"
          aria-invalid={Boolean(errors.recordedAt)}
          {...form.register('recordedAt')}
        />
        {errors.recordedAt && (
          <p className="text-destructive text-xs">{errors.recordedAt.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor={`${idPrefix}-note`}>メモ（任意）</Label>
        <Input
          id={`${idPrefix}-note`}
          type="text"
          placeholder="飲み会の翌日 など"
          aria-invalid={Boolean(errors.note)}
          {...form.register('note')}
        />
        {errors.note && <p className="text-destructive text-xs">{errors.note.message}</p>}
      </div>
    </div>
  )
}
