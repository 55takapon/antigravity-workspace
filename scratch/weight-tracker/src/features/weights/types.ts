/** 1件の体重記録。recorded_at は UTC の ISO 文字列 */
export type WeightRecord = {
  id: string
  recorded_at: string
  weight_kg: number
  note: string | null
}

/** 登録・更新時の入力値 */
export type WeightInput = {
  recorded_at: string
  weight_kg: number
  note: string | null
}

/** データ層のインターフェース（Supabase / プレビュー用ダミーで実装を差し替える） */
export type WeightRepository = {
  /** 新しい順に取得（履歴のページング用） */
  list(params: { limit: number; offset: number }): Promise<WeightRecord[]>
  /** 指定日時以降を古い順に取得（グラフ用。since が null なら全期間） */
  listSince(since: Date | null): Promise<WeightRecord[]>
  create(input: WeightInput): Promise<WeightRecord>
  update(id: string, input: WeightInput): Promise<WeightRecord>
  remove(id: string): Promise<void>
}
