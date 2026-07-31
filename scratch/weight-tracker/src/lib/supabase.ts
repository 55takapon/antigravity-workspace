import { createClient, type SupabaseClient } from '@supabase/supabase-js'
import { SUPABASE_ANON_KEY, SUPABASE_URL, isSupabaseConfigured } from '@/lib/env'

/**
 * Supabase クライアント。
 * 環境変数が未設定のときは null（プレビューモード）。
 * セッションは localStorage に自動永続化され、再訪時に自動ログインされる。
 */
export const supabase: SupabaseClient | null = isSupabaseConfigured
  ? createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
      },
    })
  : null

/** null チェックを毎回書かずに済ませるための取り出し口 */
export function requireSupabase(): SupabaseClient {
  if (!supabase) {
    throw new Error('Supabase が未設定です（VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY）')
  }
  return supabase
}
