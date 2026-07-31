import { Controller, type UseFormReturn } from 'react-hook-form'
import { z } from 'zod'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { WEIGHT_MAX_KG, WEIGHT_MIN_KG } from '@/lib/constants'
import { fromDateTimeLocalValue } from '@/lib/date'
import { WeightSlider } from '@/features/weights/weight-slider'
import type { WeightInput } from '@/features/weights/types'

/** スライダーの可動域 */
export const SLIDER_MIN_KG = 60
export const SLIDER_MAX_KG = 80

export const weightFormSchema = z.object({
  weight: z
    .number()
    .min(WEIGHT_MIN_KG, `${WEIGHT_MIN_KG}kg より大きい値にしてください`)
    .max(WEIGHT_MAX_KG, `${WEIGHT_MAX_KG}kg より小さい値にしてください`),
  recordedAt: z.string().min(1, '日時を入力してください'),
  note: z.string().max(100, 'メモは100文字までです'),
})

export type WeightFormValues = z.infer<typeof weightFormSchema>

/** フォームの値を保存用の形へ変換する（体重は小数第1位に丸める） */
export function toWeightInput(values: WeightFormValues): WeightInput {
  return {
    weight_kg: Math.round(values.weight * 10) / 10,
    recorded_at: fromDateTimeLocalValue(values.recordedAt),
    note: values.note.trim() === '' ? null : values.note.trim(),
  }
}

/** 記録画面と編集モーダルで共通に使う入力欄 */
export function WeightFormFields({
  form,
  idPrefix,
  showDateTime = true,
}: {
  form: UseFormReturn<WeightFormValues>
  idPrefix: string
  /** 記録画面ではスマホの内部時計を自動採用するため日時欄を出さない */
  showDateTime?: boolean
}) {
  const { errors } = form.formState

  return (
    <div className="space-y-4">
      <div className="space-y-3">
        <Label>体重</Label>
        <Controller
          control={form.control}
          name="weight"
          render={({ field }) => (
            <div className="space-y-3">
              <p className="text-center text-3xl font-semibold tabular-nums">
                {field.value.toFixed(1)}
                <span className="text-muted-foreground ml-1 text-base font-normal">kg</span>
              </p>
              <WeightSlider
                value={field.value}
                onChange={field.onChange}
                min={SLIDER_MIN_KG}
                max={SLIDER_MAX_KG}
              />
            </div>
          )}
        />
        {errors.weight && (
          <p className="text-destructive text-center text-xs">{errors.weight.message}</p>
        )}
      </div>

      {showDateTime && (
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
      )}

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
