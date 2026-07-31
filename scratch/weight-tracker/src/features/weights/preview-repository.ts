import type { WeightRecord, WeightRepository } from '@/features/weights/types'

/**
 * プレビューモード専用のダミーデータ層。
 * 環境変数が未設定のときだけ使われ、localStorage に保存する。
 * Supabase を設定すればこのファイルは実行されない。
 */

const STORAGE_KEY = 'weight-tracker:preview'
const NETWORK_DELAY_MS = 120

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

/** 直近120日ぶんのそれらしい推移を生成する */
function seed(): WeightRecord[] {
  const records: WeightRecord[] = []
  const start = new Date()
  start.setHours(0, 0, 0, 0)

  let weight = 71.4
  for (let i = 119; i >= 0; i--) {
    const day = new Date(start)
    day.setDate(start.getDate() - i)

    // ゆるやかな減少 + 日々のブレ
    weight += -0.022 + (Math.sin(i * 1.7) + Math.cos(i * 0.6)) * 0.18
    if (i % 11 === 0) weight += 0.35

    const morning = new Date(day)
    morning.setHours(7, 20 + (i % 25), 0, 0)
    records.push({
      id: `preview-${i}-a`,
      recorded_at: morning.toISOString(),
      weight_kg: Math.round(weight * 10) / 10,
      note: i % 17 === 0 ? '飲み会の翌日' : null,
    })

    // 週に1回ほど夜も測っている想定（1日複数件のケース）
    if (i % 7 === 3) {
      const night = new Date(day)
      night.setHours(22, 10, 0, 0)
      records.push({
        id: `preview-${i}-b`,
        recorded_at: night.toISOString(),
        weight_kg: Math.round((weight + 0.6) * 10) / 10,
        note: null,
      })
    }
  }
  return records
}

function load(): WeightRecord[] {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (raw) {
    try {
      return JSON.parse(raw) as WeightRecord[]
    } catch {
      // 壊れていたら作り直す
    }
  }
  const seeded = seed()
  save(seeded)
  return seeded
}

function save(records: WeightRecord[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(records))
}

const byRecordedAtDesc = (a: WeightRecord, b: WeightRecord) =>
  b.recorded_at.localeCompare(a.recorded_at)

export const previewWeightRepository: WeightRepository = {
  async list({ limit, offset }) {
    await sleep(NETWORK_DELAY_MS)
    return load().sort(byRecordedAtDesc).slice(offset, offset + limit)
  },

  async listSince(since) {
    await sleep(NETWORK_DELAY_MS)
    const all = load().sort((a, b) => a.recorded_at.localeCompare(b.recorded_at))
    if (!since) return all
    return all.filter((r) => new Date(r.recorded_at) >= since)
  },

  async create(input) {
    await sleep(NETWORK_DELAY_MS)
    const record: WeightRecord = { id: crypto.randomUUID(), ...input }
    save([record, ...load()])
    return record
  },

  async update(id, input) {
    await sleep(NETWORK_DELAY_MS)
    const records = load()
    const index = records.findIndex((r) => r.id === id)
    if (index < 0) throw new Error('記録が見つかりません')
    const updated: WeightRecord = { id, ...input }
    records[index] = updated
    save(records)
    return updated
  },

  async remove(id) {
    await sleep(NETWORK_DELAY_MS)
    save(load().filter((r) => r.id !== id))
  },
}
