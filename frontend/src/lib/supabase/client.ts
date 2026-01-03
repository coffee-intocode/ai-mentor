import { createClient as createSupabaseClient, type SupabaseClient } from '@supabase/supabase-js'

const envUrl = import.meta.env.VITE_SUPABASE_URL as string | undefined
const envAnonKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string | undefined

if (!envUrl || !envAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

const supabaseUrl: string = envUrl
const supabaseAnonKey: string = envAnonKey

let supabaseInstance: SupabaseClient | null = null

export function getSupabaseClient(): SupabaseClient {
  supabaseInstance ??= createSupabaseClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      flowType: 'pkce',
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
    },
  })
  return supabaseInstance
}

export const createClient = getSupabaseClient
