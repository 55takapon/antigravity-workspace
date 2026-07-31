/**
 * 日時ユーティリティ。
 * DB は UTC の ISO 文字列で保持し、表示・集計はすべてローカルタイムゾーンで行う。
 */

const WEEKDAYS = ['日', '月', '火', '水', '木', '金', '土'] as const

const pad = (n: number) => String(n).padStart(2, '0')

/** ローカル日付キー（YYYY-MM-DD）。日付グルーピングと1日1点への丸めに使う */
export function toDateKey(value: string | Date): string {
  const d = typeof value === 'string' ? new Date(value) : value
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

/** 履歴の日付見出し（例: 7月31日(金)、今日、昨日） */
export function formatDateHeading(value: string | Date): string {
  const d = typeof value === 'string' ? new Date(value) : value
  const key = toDateKey(d)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(today.getDate() - 1)

  if (key === toDateKey(today)) return '今日'
  if (key === toDateKey(yesterday)) return '昨日'
  return `${d.getMonth() + 1}月${d.getDate()}日(${WEEKDAYS[d.getDay()]})`
}

/** 履歴の行に使う短い日付（例: 7/31(金)）。「今日」「昨日」のような特別扱いはしない */
export function formatShortWeekday(value: string | Date): string {
  const d = typeof value === 'string' ? new Date(value) : value
  return `${d.getMonth() + 1}/${d.getDate()}(${WEEKDAYS[d.getDay()]})`
}

/** 時刻（例: 08:05） */
export function formatTime(value: string | Date): string {
  const d = typeof value === 'string' ? new Date(value) : value
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}

/** グラフのX軸ラベル（例: 7/31） */
export function formatShortDate(value: string | Date): string {
  const d = typeof value === 'string' ? new Date(value) : value
  return `${d.getMonth() + 1}/${d.getDate()}`
}

/** 日時＋時刻（例: 7月31日(金) 08:05） */
export function formatDateTime(value: string | Date): string {
  const d = typeof value === 'string' ? new Date(value) : value
  return `${d.getMonth() + 1}月${d.getDate()}日(${WEEKDAYS[d.getDay()]}) ${formatTime(d)}`
}

/** <input type="datetime-local"> 用の値（ローカル時刻） */
export function toDateTimeLocalValue(value: string | Date): string {
  const d = typeof value === 'string' ? new Date(value) : value
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

/** datetime-local の値を UTC の ISO 文字列へ */
export function fromDateTimeLocalValue(value: string): string {
  return new Date(value).toISOString()
}

/** n 日前の 00:00（ローカル） */
export function daysAgoStart(days: number): Date {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  d.setDate(d.getDate() - days + 1)
  return d
}
