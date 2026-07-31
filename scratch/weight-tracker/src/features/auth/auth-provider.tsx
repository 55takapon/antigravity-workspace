import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { isPreviewMode } from '@/lib/env'
import { supabase } from '@/lib/supabase'
import { AuthContext, type AuthStatus, type AuthUser } from '@/features/auth/auth-context'

/** プレビューモードで使う仮のユーザー */
const PREVIEW_USER: AuthUser = { id: 'preview-user', email: 'preview@example.com' }

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>(isPreviewMode ? 'authenticated' : 'loading')
  const [user, setUser] = useState<AuthUser | null>(isPreviewMode ? PREVIEW_USER : null)

  useEffect(() => {
    if (!supabase) return

    // 再訪時は保存済みセッションから復元される
    supabase.auth.getSession().then(({ data }) => {
      const sessionUser = data.session?.user
      setUser(sessionUser ? { id: sessionUser.id, email: sessionUser.email ?? null } : null)
      setStatus(sessionUser ? 'authenticated' : 'unauthenticated')
    })

    const { data: subscription } = supabase.auth.onAuthStateChange((_event, session) => {
      const sessionUser = session?.user
      setUser(sessionUser ? { id: sessionUser.id, email: sessionUser.email ?? null } : null)
      setStatus(sessionUser ? 'authenticated' : 'unauthenticated')
    })

    return () => subscription.subscription.unsubscribe()
  }, [])

  const value = useMemo(
    () => ({
      status,
      user,
      signInWithEmail: async (email: string) => {
        if (!supabase) return
        const { error } = await supabase.auth.signInWithOtp({
          email,
          options: { emailRedirectTo: window.location.origin },
        })
        if (error) throw error
      },
      signOut: async () => {
        if (!supabase) return
        await supabase.auth.signOut()
      },
    }),
    [status, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
