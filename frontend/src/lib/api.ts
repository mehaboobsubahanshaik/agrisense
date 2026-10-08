import axios from 'axios'
import { useAuth } from '../store/auth'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api/v1',
  timeout: 60000,
})

api.interceptors.request.use((config) => {
  const token = useAuth.getState().access
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshing: Promise<string | null> | null = null

async function refreshAccess(): Promise<string | null> {
  const { refresh } = useAuth.getState()
  if (!refresh) return null
  try {
    const { data } = await axios.post(
      `${api.defaults.baseURL}/auth/refresh`,
      { refresh_token: refresh },
      { timeout: 20000 }
    )
    useAuth.getState().setSession(data.access_token, data.refresh_token, data.user)
    return data.access_token as string
  } catch {
    useAuth.getState().clear()
    return null
  }
}

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retried) {
      original._retried = true
      refreshing = refreshing ?? refreshAccess().finally(() => { refreshing = null })
      const token = await refreshing
      if (token) {
        original.headers.Authorization = `Bearer ${token}`
        return api(original)
      }
      if (location.pathname !== '/login') location.assign('/login')
    }
    return Promise.reject(error)
  }
)

export const apiError = (e: any, fallback = 'Something went wrong. Try again.') =>
  e?.response?.data?.detail ?? (navigator.onLine ? fallback : 'You are offline. This will work again when you reconnect.')
