import { createContext, useContext } from 'react'

export type AuthUser = {
  id: string
  email: string | null
}

export type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated'

export type AuthContextValue = {
  status: AuthStatus
  user: AuthUser | null
  /** Magic Link を送信する */
  signInWithEmail: (email: string) => Promise<void>
  signOut: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth は AuthProvider の内側で使うこと')
  return value
}
