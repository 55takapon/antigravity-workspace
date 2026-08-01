import { requireSupabase } from '@/lib/supabase'
import type { WeightRecord, WeightRepository } from '@/features/weights/types'

const COLUMNS = 'id, recorded_at, weight_kg, note'

/** numeric(5,2) は文字列で返ることがあるため数値に正規化する */
function normalize(row: {
  id: string
  recorded_at: string
  weight_kg: number | string
  note: string | null
}): WeightRecord {
  return {
    id: row.id,
    recorded_at: row.recorded_at,
    weight_kg: Number(row.weight_kg),
    note: row.note,
  }
}

export const supabaseWeightRepository: WeightRepository = {
  async list({ limit, offset }) {
    const { data, error } = await requireSupabase()
      .from('weights')
      .select(COLUMNS)
      .order('recorded_at', { ascending: false })
      .range(offset, offset + limit - 1)

    if (error) throw error
    return (data ?? []).map(normalize)
  },

  async listSince(since) {
    let query = requireSupabase()
      .from('weights')
      .select(COLUMNS)
      .order('recorded_at', { ascending: true })

    if (since) query = query.gte('recorded_at', since.toISOString())

    const { data, error } = await query
    if (error) throw error
    return (data ?? []).map(normalize)
  },

  async create(input) {
    // user_id は DB 側の default auth.uid() が埋める。
    // 同じ日（JST基準）にすでに記録があれば、DBの一意制約（user_id, local_date）により
    // 新規作成ではなく上書きになる。
    const { data, error } = await requireSupabase()
      .from('weights')
      .upsert(input, { onConflict: 'user_id,local_date' })
      .select(COLUMNS)
      .single()

    if (error) throw error
    return normalize(data)
  },

  async update(id, input) {
    const { data, error } = await requireSupabase()
      .from('weights')
      .update(input)
      .eq('id', id)
      .select(COLUMNS)
      .single()

    if (error) {
      // 編集で日付をずらした先に、すでに別の記録がある場合（1日1件の制約違反）
      if (error.code === '23505') {
        throw new Error('その日はすでに記録があります。日付を変えるか、既存の記録を編集してください。')
      }
      throw error
    }
    return normalize(data)
  },

  async remove(id) {
    const { error } = await requireSupabase().from('weights').delete().eq('id', id)
    if (error) throw error
  },
}
