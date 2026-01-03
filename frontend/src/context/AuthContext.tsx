import { createContext, useContext, useEffect, useState, useCallback, useMemo, type ReactNode } from 'react'
import type { Session, User } from '@supabase/supabase-js'
import { getSupabaseClient } from '@/lib/supabase/client'

interface AuthResult {
  success: boolean
  error?: string
}

interface AuthContextType {
  user: User | null
  session: Session | null
  isLoading: boolean
  signUp: (email: string, password: string) => Promise<AuthResult>
  signIn: (email: string, password: string) => Promise<AuthResult>
  signOut: () => Promise<void>
  resetPassword: (email: string) => Promise<AuthResult>
  updatePassword: (password: string) => Promise<AuthResult>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const supabase = useMemo(() => getSupabaseClient(), [])

  useEffect(() => {
    supabase.auth
      .getSession()
      .then(({ data: { session } }) => {
        setSession(session)
        setIsLoading(false)
      })
      .catch((error: unknown) => {
        console.error('Failed to get session:', error)
      })

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setIsLoading(false)
    })

    return () => {
      subscription.unsubscribe()
    }
  }, [supabase])

  const signUp = useCallback(
    async (email: string, password: string): Promise<AuthResult> => {
      const { error } = await supabase.auth.signUp({
        email: email.toLowerCase().trim(),
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/`,
        },
      })
      if (error) return { success: false, error: error.message }
      return { success: true }
    },
    [supabase],
  )

  const signIn = useCallback(
    async (email: string, password: string): Promise<AuthResult> => {
      const { error } = await supabase.auth.signInWithPassword({
        email: email.toLowerCase().trim(),
        password,
      })
      if (error) return { success: false, error: error.message }
      return { success: true }
    },
    [supabase],
  )

  const signOut = useCallback(async () => {
    await supabase.auth.signOut()
  }, [supabase])

  const resetPassword = useCallback(
    async (email: string): Promise<AuthResult> => {
      const { error } = await supabase.auth.resetPasswordForEmail(email.toLowerCase().trim(), {
        redirectTo: `${window.location.origin}/auth/reset-password`,
      })
      if (error) return { success: false, error: error.message }
      return { success: true }
    },
    [supabase],
  )

  const updatePassword = useCallback(
    async (password: string): Promise<AuthResult> => {
      const { error } = await supabase.auth.updateUser({ password })
      if (error) return { success: false, error: error.message }
      return { success: true }
    },
    [supabase],
  )

  const value = useMemo(
    () => ({
      user: session?.user ?? null,
      session,
      isLoading,
      signUp,
      signIn,
      signOut,
      resetPassword,
      updatePassword,
    }),
    [session, isLoading, signUp, signIn, signOut, resetPassword, updatePassword],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
