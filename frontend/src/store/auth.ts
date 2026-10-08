import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type User = {
  id: string; phone: string; name: string; role: string
  language: string; state: string; district: string; lat: number; lon: number
}

type AuthState = {
  access: string | null
  refresh: string | null
  user: User | null
  setSession: (a: string, r: string, u: User) => void
  setTokens: (a: string, r: string) => void
  setUser: (u: User) => void
  clear: () => void
}

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      access: null,
      refresh: null,
      user: null,
      setSession: (access, refresh, user) => set({ access, refresh, user }),
      setTokens: (access, refresh) => set({ access, refresh }),
      setUser: (user) => set({ user }),
      clear: () => set({ access: null, refresh: null, user: null }),
    }),
    { name: 'agrisense-auth' }
  )
)
