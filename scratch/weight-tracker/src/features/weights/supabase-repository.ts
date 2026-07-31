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
    // user_id は DB 側の default auth.uid() が埋める
    const { data, error } = await requireSupabase()
      .from('weights')
      .insert(input)
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

    if (error) throw error
    return normalize(data)
  },

  async remove(id) {
    const { error } = await requireSupabase().from('weights').delete().eq('id', id)
    if (error) throw error
  },
}
