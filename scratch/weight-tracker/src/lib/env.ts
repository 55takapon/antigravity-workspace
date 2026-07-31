const url = import.meta.env.VITE_SUPABASE_URL as string | undefined
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined

export const SUPABASE_URL = url ?? ''
export const SUPABASE_ANON_KEY = anonKey ?? ''

/** .env.local が設定済みかどうか */
export const isSupabaseConfigured = Boolean(url && anonKey)

/**
 * 環境変数が未設定のときだけ有効になるプレビューモード。
 * ブラウザ内のダミーデータで全画面を確認するための開発用フォールバックで、
 * Supabase を設定すれば自動的に無効になる。
 */
export const isPreviewMode = !isSupabaseConfigured
