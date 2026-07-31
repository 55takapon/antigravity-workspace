import { DAILY_SAMPLE, MOVING_AVERAGE_DAYS } from '@/lib/constants'
import { toDateKey } from '@/lib/date'
import type { WeightRecord } from '@/features/weights/types'

export type PeriodKey = '7d' | '30d' | '90d' | 'all'

export const PERIOD_OPTIONS: { key: PeriodKey; label: string; days: number | null }[] = [
  { key: '7d', label: '1週間', days: 7 },
  { key: '30d', label: '1ヶ月', days: 30 },
  { key: '90d', label: '3ヶ月', days: 90 },
  { key: 'all', label: '全期間', days: null },
]

export type DailyPoint = {
  dateKey: string
  date: Date
  weight: number
  note: string | null
}

export type ChartPoint = DailyPoint & {
  /** 直近 MOVING_AVERAGE_DAYS 日以内の実データ平均。窓内に1件でもあれば値が入る */
  movingAverage: number
}

/**
 * 1日に複数件あるとき、DAILY_SAMPLE の設定に従って1点へ丸める。
 * records は recorded_at 昇順であること。
 */
export function toDailyPoints(records: WeightRecord[]): DailyPoint[] {
  const byDate = new Map<string, WeightRecord>()

  for (const record of records) {
    const key = toDateKey(record.recorded_at)
    const existing = byDate.get(key)
    if (!existing || DAILY_SAMPLE === 'last') {
      byDate.set(key, record)
    }
    // DAILY_SAMPLE === 'first' のときは昇順なので最初の1件をそのまま残す
  }

  return Array.from(byDate.values())
    .sort((a, b) => a.recorded_at.localeCompare(b.recorded_at))
    .map((record) => ({
      dateKey: toDateKey(record.recorded_at),
      date: new Date(record.recorded_at),
      weight: record.weight_kg,
      note: record.note,
    }))
}

/** 直近 N 日移動平均を付与する（スライド窓・O(n)） */
export function withMovingAverage(points: DailyPoint[]): ChartPoint[] {
  const result: ChartPoint[] = []
  let start = 0
  let sum = 0

  for (let i = 0; i < points.length; i++) {
    sum += points[i].weight

    const windowStart = new Date(points[i].date)
    windowStart.setDate(windowStart.getDate() - (MOVING_AVERAGE_DAYS - 1))

    while (points[start].date < windowStart) {
      sum -= points[start].weight
      start++
    }

    const count = i - start + 1
    result.push({ ...points[i], movingAverage: Math.round((sum / count) * 100) / 100 })
  }

  return result
}

export type ChartSummary = {
  /** 期間内の増減（末尾 - 先頭） */
  change: number
  max: number
  min: number
  average: number
}

export function summarize(points: DailyPoint[]): ChartSummary | null {
  if (points.length === 0) return null

  const weights = points.map((p) => p.weight)
  const max = Math.max(...weights)
  const min = Math.min(...weights)
  const average = weights.reduce((sum, w) => sum + w, 0) / weights.length
  const change = points[points.length - 1].weight - points[0].weight

  return { change, max, min, average }
}
