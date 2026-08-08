import { createContext, useContext, useState, type ReactNode } from 'react'
import { authApi } from './api'
import type { AuthResponse, User } from './types'

type Auth = { user: User | null; login: (email: string, password: string) => Promise<void>; register: (name: string, email: string, password: string) => Promise<void>; logout: () => Promise<void> }
const Context = createContext<Auth | null>(null)
const store = (data: AuthResponse) => { localStorage.setItem('access_token', data.access_token); localStorage.setItem('refresh_token', data.refresh_token) }
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => { const raw = localStorage.getItem('user'); return raw ? JSON.parse(raw) : null })
  const save = (data: AuthResponse) => { store(data); localStorage.setItem('user', JSON.stringify(data.user)); setUser(data.user) }
  const logout = async () => { const refresh_token = localStorage.getItem('refresh_token'); try { if (refresh_token) await authApi.logout(refresh_token) } finally { localStorage.clear(); setUser(null) } }
  return <Context.Provider value={{ user, login: async (email, password) => save((await authApi.login(email, password)).data), register: async (name, email, password) => save((await authApi.register(name, email, password)).data), logout }}>{children}</Context.Provider>
}
export const useAuth = () => { const value = useContext(Context); if (!value) throw new Error('useAuth must be used inside AuthProvider'); return value }
