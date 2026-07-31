import { useRef, type PointerEvent as ReactPointerEvent } from 'react'
import { Minus, Plus } from 'lucide-react'
import { cn } from '@/lib/utils'

const FINE_STEP = 0.1

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function roundToStep(value: number, step: number) {
  return Math.round(value / step) * step
}

type WeightSliderProps = {
  value: number
  onChange: (value: number) => void
  min: number
  max: number
  className?: string
}

/**
 * 体重を横バーのタップ・ドラッグで調整するスライダー。
 * ネイティブ input[type=range] はタップ位置へジャンプする挙動がブラウザ次第なため、
 * ポインタ位置から直接値を計算する独自実装にしている。
 * 微調整用に ±0.1kg ボタンも両端に添える。
 */
export function WeightSlider({ value, onChange, min, max, className }: WeightSliderProps) {
  const trackRef = useRef<HTMLDivElement>(null)

  const setFromClientX = (clientX: number) => {
    const el = trackRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const ratio = clamp((clientX - rect.left) / rect.width, 0, 1)
    const raw = min + ratio * (max - min)
    onChange(Math.round(clamp(roundToStep(raw, FINE_STEP), min, max) * 10) / 10)
  }

  const handlePointerDown = (event: ReactPointerEvent<HTMLDivElement>) => {
    event.currentTarget.setPointerCapture(event.pointerId)
    setFromClientX(event.clientX)
  }

  const handlePointerMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (event.buttons !== 1) return
    setFromClientX(event.clientX)
  }

  const nudge = (delta: number) => {
    onChange(Math.round(clamp(value + delta, min, max) * 10) / 10)
  }

  const percent = ((value - min) / (max - min)) * 100

  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <button
        type="button"
        onClick={() => nudge(-FINE_STEP)}
        className="border-border/70 text-muted-foreground hover:text-foreground hover:border-brand/50 flex size-9 shrink-0 items-center justify-center rounded-full border transition-colors active:scale-95"
        aria-label="0.1kg 減らす"
      >
        <Minus className="size-4" />
      </button>

      <div
        ref={trackRef}
        role="slider"
        tabIndex={0}
        aria-label="体重"
        aria-valuemin={min}
        aria-valuemax={max}
        aria-valuenow={value}
        aria-valuetext={`${value.toFixed(1)} kg`}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onKeyDown={(event) => {
          if (event.key === 'ArrowRight' || event.key === 'ArrowUp') {
            event.preventDefault()
            nudge(FINE_STEP)
          }
          if (event.key === 'ArrowLeft' || event.key === 'ArrowDown') {
            event.preventDefault()
            nudge(-FINE_STEP)
          }
        }}
        className="bg-secondary ring-border/70 relative h-14 flex-1 touch-none rounded-full ring-1 select-none"
      >
        <div
          aria-hidden
          className="from-brand-deep to-brand absolute inset-y-0 left-0 rounded-full bg-gradient-to-r"
          style={{ width: `${percent}%` }}
        />
        <div
          aria-hidden
          className="bg-background border-brand absolute top-1/2 size-9 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 shadow-[0_2px_10px_-2px_var(--brand)]"
          style={{ left: `${percent}%` }}
        />
      </div>

      <button
        type="button"
        onClick={() => nudge(FINE_STEP)}
        className="border-border/70 text-muted-foreground hover:text-foreground hover:border-brand/50 flex size-9 shrink-0 items-center justify-center rounded-full border transition-colors active:scale-95"
        aria-label="0.1kg 増やす"
      >
        <Plus className="size-4" />
      </button>
    </div>
  )
}
