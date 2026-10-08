import { AnimatePresence, motion } from 'framer-motion'
import {
  Bell, Bug, CloudSun, Home, Landmark, LayoutGrid, Leaf, LogOut, Menu, MessageSquare,
  Settings, Sprout, TrendingUp, X,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { LANGUAGES, useLang, useT } from '../lib/i18n'
import { cn } from '../lib/utils'
import { useAuth } from '../store/auth'
import { FloatingLeaves } from './Ambient'

const NAV = [
  { to: '/app', icon: Home, key: 'dashboard', end: true },
  { to: '/app/chat', icon: MessageSquare, key: 'chat' },
  { to: '/app/scan', icon: Bug, key: 'disease' },
  { to: '/app/soil', icon: Sprout, key: 'soil' },
  { to: '/app/weather', icon: CloudSun, key: 'weather' },
  { to: '/app/crops', icon: LayoutGrid, key: 'crops' },
  { to: '/app/yield', icon: TrendingUp, key: 'yieldp' },
  { to: '/app/schemes', icon: Landmark, key: 'schemes' },
  { to: '/app/settings', icon: Settings, key: 'settings' },
] as const

const MOBILE_NAV = [NAV[0], NAV[1], NAV[2], NAV[4], NAV[7]]

export default function Layout() {
  const t = useT()
  const { lang, setLang } = useLang()
  const { user, clear } = useAuth()
  const [open, setOpen] = useState(false)
  const [online, setOnline] = useState(navigator.onLine)
  const [unread, setUnread] = useState(0)
  const nav = useNavigate()
  const loc = useLocation()

  useEffect(() => {
    const on = () => setOnline(true)
    const off = () => setOnline(false)
    window.addEventListener('online', on)
    window.addEventListener('offline', off)
    return () => { window.removeEventListener('online', on); window.removeEventListener('offline', off) }
  }, [])

  useEffect(() => { setOpen(false) }, [loc.pathname])

  useEffect(() => {
    api.get('/notifications').then(({ data }) => setUnread(data.filter((n: any) => !n.read).length)).catch(() => {})
  }, [loc.pathname])

  const signOut = async () => {
    try { await api.post('/auth/logout') } catch { /* token may already be gone */ }
    clear()
    nav('/login')
  }

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      'group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition',
      isActive ? 'bg-white text-leaf-dark shadow-card' : 'text-white/80 hover:bg-white/10 hover:text-white'
    )

  return (
    <div className="min-h-dvh lg:flex">
      <FloatingLeaves />

      {/* ---- desktop / tablet sidebar ---- */}
      <aside className="horizon sticky top-0 hidden h-dvh w-60 shrink-0 flex-col p-4 md:flex xl:w-64">
        <div className="mb-6 flex items-center gap-2.5 px-1">
          <Leaf className="h-7 w-7 text-grain" />
          <div>
            <p className="font-display text-lg font-bold leading-none text-white">AgriSense</p>
            <p className="text-[11px] uppercase tracking-[.18em] text-leaf-light">AI advisor</p>
          </div>
        </div>
        <nav className="flex flex-1 flex-col gap-1 overflow-y-auto">
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} end={(item as any).end} className={linkClass}>
              <item.icon className="h-[18px] w-[18px]" />
              <span className="truncate">{t(item.key as any)}</span>
            </NavLink>
          ))}
        </nav>
        <button onClick={signOut} className="mt-3 flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-white/70 transition hover:bg-white/10 hover:text-white">
          <LogOut className="h-[18px] w-[18px]" /> {t('signOut')}
        </button>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        {/* ---- top bar ---- */}
        <header className="sticky top-0 z-30 border-b border-black/5 bg-field/85 backdrop-blur">
          <div className="mx-auto flex h-14 max-w-[1600px] items-center gap-3 px-4">
            <button className="rounded-lg p-2 md:hidden" onClick={() => setOpen(true)} aria-label="Open menu">
              <Menu className="h-5 w-5" />
            </button>
            <div className="min-w-0 flex-1">
              <p className="truncate font-display text-base font-bold text-leaf-dark">
                {user?.name ?? 'Farmer'}
              </p>
              <p className="truncate text-xs text-soil-light">
                {user?.district ? `${user.district}, ` : ''}{user?.state}
              </p>
            </div>

            {!online && (
              <span className="pill bg-soil/10 text-soil-dark">Offline · showing saved data</span>
            )}

            <select
              value={lang}
              onChange={(e) => setLang(e.target.value)}
              aria-label="Language"
              className="h-9 rounded-lg border border-soil-light/40 bg-white px-2 text-sm"
            >
              {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.native}</option>)}
            </select>

            <NavLink to="/app/notifications" className="relative rounded-lg p-2 hover:bg-black/5" aria-label="Alerts">
              <Bell className="h-5 w-5" />
              {unread > 0 && (
                <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-danger px-1 text-[10px] font-bold text-white">
                  {unread}
                </span>
              )}
            </NavLink>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1600px] flex-1 px-4 pb-24 pt-4 md:pb-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={loc.pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.22 }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* ---- mobile bottom navigation ---- */}
      <nav className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-black/5 bg-white/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden">
        {MOBILE_NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={(item as any).end}
            className={({ isActive }) =>
              cn('flex flex-col items-center gap-0.5 py-2.5 text-[11px] font-medium',
                 isActive ? 'text-leaf' : 'text-soil-light')
            }
          >
            <item.icon className="h-5 w-5" />
            {t(item.key as any)}
          </NavLink>
        ))}
      </nav>

      {/* ---- mobile drawer ---- */}
      <AnimatePresence>
        {open && (
          <>
            <motion.div
              className="fixed inset-0 z-40 bg-black/40 md:hidden"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setOpen(false)}
            />
            <motion.aside
              className="horizon fixed inset-y-0 left-0 z-50 flex w-72 flex-col p-4 md:hidden"
              initial={{ x: '-100%' }} animate={{ x: 0 }} exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 26, stiffness: 260 }}
            >
              <div className="mb-6 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <Leaf className="h-7 w-7 text-grain" />
                  <p className="font-display text-lg font-bold text-white">AgriSense</p>
                </div>
                <button onClick={() => setOpen(false)} aria-label="Close menu" className="rounded-lg p-2 text-white">
                  <X className="h-5 w-5" />
                </button>
              </div>
              <nav className="flex flex-1 flex-col gap-1 overflow-y-auto">
                {NAV.map((item) => (
                  <NavLink key={item.to} to={item.to} end={(item as any).end} className={linkClass}>
                    <item.icon className="h-[18px] w-[18px]" /> {t(item.key as any)}
                  </NavLink>
                ))}
              </nav>
              <button onClick={signOut} className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-white/80">
                <LogOut className="h-[18px] w-[18px]" /> {t('signOut')}
              </button>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
