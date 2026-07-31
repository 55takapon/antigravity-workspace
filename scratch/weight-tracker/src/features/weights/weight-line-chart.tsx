import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipContentProps,
} from 'recharts'
import type { ValueType, NameType } from 'recharts/types/component/DefaultTooltipContent'
import { CHART_Y_MARGIN_KG } from '@/lib/constants'
import { formatDateTime, formatShortDate } from '@/lib/date'
import type { ChartPoint } from '@/features/weights/chart-data'

type WeightLineChartProps = {
  points: ChartPoint[]
  /** 1週間表示のときは移動平均線を出さない */
  showMovingAverage: boolean
}

/** ラベルが密集しすぎないよう、点数に応じて X 軸目盛りを間引く */
function computeTickInterval(pointCount: number): number {
  const maxTicks = 6
  if (pointCount <= maxTicks) return 0
  return Math.ceil(pointCount / maxTicks) - 1
}

function CustomTooltip({ active, payload }: TooltipContentProps<ValueType, NameType>) {
  if (!active || !payload?.length) return null
  const point = payload[0].payload as ChartPoint

  return (
    <div className="border-border/70 bg-popover text-popover-foreground rounded-lg border px-3 py-2 text-xs shadow-lg">
      <p className="font-medium">{formatDateTime(point.date)}</p>
      <p className="mt-1 text-sm font-semibold">{point.weight.toFixed(1)} kg</p>
      {point.note && <p className="text-muted-foreground mt-0.5 max-w-40 truncate">{point.note}</p>}
    </div>
  )
}

/** Recharts 本体。動的 import でグラフ画面にだけ読み込まれる */
export default function WeightLineChart({ points, showMovingAverage }: WeightLineChartProps) {
  const weights = points.map((p) => p.weight)
  const yMin = Math.min(...weights) - CHART_Y_MARGIN_KG
  const yMax = Math.max(...weights) + CHART_Y_MARGIN_KG
  const tickInterval = computeTickInterval(points.length)

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={points} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
        <CartesianGrid stroke="var(--border)" vertical={false} />
        <XAxis
          dataKey="dateKey"
          tickFormatter={(value: string) => formatShortDate(value)}
          interval={tickInterval}
          tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }}
          axisLine={{ stroke: 'var(--border)' }}
          tickLine={false}
        />
        <YAxis
          domain={[yMin, yMax]}
          tickFormatter={(value: number) => value.toFixed(1)}
          tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={40}
        />
        <Tooltip content={CustomTooltip} cursor={{ stroke: 'var(--border)' }} />
        {showMovingAverage && (
          <Line
            type="monotone"
            dataKey="movingAverage"
            name="7日移動平均"
            stroke="var(--chart-2)"
            strokeWidth={2}
            strokeDasharray="4 3"
            dot={false}
            isAnimationActive={false}
          />
        )}
        <Line
          type="monotone"
          dataKey="weight"
          name="体重"
          stroke="var(--chart-1)"
          strokeWidth={2.5}
          dot={points.length <= 31}
          activeDot={{ r: 4 }}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
