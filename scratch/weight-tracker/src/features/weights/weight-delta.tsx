import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react'
import { cn } from '@/lib/utils'

type WeightDeltaProps = {
  /** 直前の記録との差分（kg）。null なら比較対象なし */
  delta: number | null
  /** ピル型の背景を付ける（記録画面の大きい表示用） */
  variant?: 'plain' | 'pill'
  className?: string
}

/** 増減を色分けして表示する。増加=赤系、減少=緑系 */
export function WeightDelta({ delta, variant = 'plain', className }: WeightDeltaProps) {
  const rounded = delta === null ? null : Math.round(delta * 10) / 10

  const { Icon, label, tone } =
    rounded === null
      ? { Icon: Minus, label: '比較なし', tone: 'muted' as const }
      : rounded > 0
        ? { Icon: ArrowUpRight, label: `+${rounded.toFixed(1)} kg`, tone: 'up' as const }
        : rounded < 0
          ? { Icon: ArrowDownRight, label: `−${Math.abs(rounded).toFixed(1)} kg`, tone: 'down' as const }
          : { Icon: Minus, label: '±0.0 kg', tone: 'flat' as const }

  const toneClass = {
    up: 'text-rose-400',
    down: 'text-emerald-400',
    flat: 'text-muted-foreground',
    muted: 'text-muted-foreground',
  }[tone]

  const pillClass = {
    up: 'bg-rose-500/12 ring-rose-500/25',
    down: 'bg-emerald-500/12 ring-emerald-500/25',
    flat: 'bg-muted ring-border',
    muted: 'bg-muted ring-border',
  }[tone]

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 font-medium tabular-nums',
        toneClass,
        variant === 'pill' && cn('rounded-full px-2.5 py-1 ring-1 ring-inset', pillClass),
        className,
      )}
    >
      <Icon className="size-3.5" aria-hidden />
      {label}
    </span>
  )
}
