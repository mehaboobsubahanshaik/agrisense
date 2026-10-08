import { ShieldCheck } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Button, ErrorNote } from '../components/ui'
import { api, apiError } from '../lib/api'
import { useAuth } from '../store/auth'

const LENGTH = 6

export default function VerifyOtp() {
  const { state } = useLocation() as { state?: { phone: string; expires_in: number; resend_after: number; dev_otp?: string } }
  const nav = useNavigate()
  const setSession = useAuth((s) => s.setSession)

  const [digits, setDigits] = useState<string[]>(Array(LENGTH).fill(''))
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [expiresIn, setExpiresIn] = useState(state?.expires_in ?? 300)
  const [resendIn, setResendIn] = useState(state?.resend_after ?? 30)
  const inputs = useRef<(HTMLInputElement | null)[]>([])

  useEffect(() => {
    const id = setInterval(() => {
      setExpiresIn((s) => Math.max(0, s - 1))
      setResendIn((s) => Math.max(0, s - 1))
    }, 1000)
    return () => clearInterval(id)
  }, [])

  if (!state?.phone) return <Navigate to="/login" replace />

  const code = digits.join('')
  const mmss = `${String(Math.floor(expiresIn / 60)).padStart(2, '0')}:${String(expiresIn % 60).padStart(2, '0')}`

  const setAt = (i: number, value: string) => {
    const v = value.replace(/\D/g, '')
    if (!v) { setDigits((d) => d.map((x, idx) => (idx === i ? '' : x))); return }
    const next = [...digits]
    v.split('').forEach((ch, k) => { if (i + k < LENGTH) next[i + k] = ch })
    setDigits(next)
    inputs.current[Math.min(LENGTH - 1, i + v.length)]?.focus()
  }

  const verify = async (e?: React.FormEvent) => {
    e?.preventDefault()
    if (code.length !== LENGTH) return setError('Enter all 6 digits.')
    setError(''); setLoading(true)
    try {
      const { data } = await api.post('/auth/verify-otp', {
        phone: state.phone, otp: code, device: navigator.userAgent.slice(0, 120),
      })
      setSession(data.access_token, data.refresh_token, data.user)
      nav('/app', { replace: true })
    } catch (err) {
      setError(apiError(err, 'That code did not work.'))
      setDigits(Array(LENGTH).fill(''))
      inputs.current[0]?.focus()
    } finally {
      setLoading(false)
    }
  }

  const resend = async () => {
    setError('')
    try {
      const { data } = await api.post('/auth/request-otp', { phone: state.phone })
      setExpiresIn(data.expires_in); setResendIn(data.resend_after)
      if (data.dev_otp) setDigits(String(data.dev_otp).split(''))
    } catch (err) {
      setError(apiError(err))
    }
  }

  return (
    <div className="flex min-h-dvh items-center justify-center px-5 py-12">
      <form onSubmit={verify} className="w-full max-w-md">
        <ShieldCheck className="mb-4 h-9 w-9 text-leaf" />
        <h1 className="font-display text-2xl font-bold text-leaf-dark">Enter the code</h1>
        <p className="mb-6 mt-1 text-sm text-soil">
          Sent to +91 {state.phone}. It expires in <span className="font-semibold tabular-nums">{mmss}</span>.
        </p>

        {state.dev_otp && (
          <p className="mb-4 rounded-xl bg-grain/20 px-3 py-2 text-sm text-soil-dark">
            Development mode - your code is <span className="font-mono font-bold">{state.dev_otp}</span>
          </p>
        )}

        <div className="flex gap-2 sm:gap-3">
          {digits.map((d, i) => (
            <input
              key={i}
              ref={(el) => { inputs.current[i] = el }}
              value={d}
              autoFocus={i === 0}
              inputMode="numeric"
              autoComplete={i === 0 ? 'one-time-code' : 'off'}
              maxLength={LENGTH}
              aria-label={`Digit ${i + 1}`}
              onChange={(e) => setAt(i, e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Backspace' && !digits[i] && i > 0) inputs.current[i - 1]?.focus()
              }}
              className="h-14 w-full rounded-xl border border-soil-light/40 bg-white text-center font-mono text-2xl
                         focus:border-leaf focus:ring-2 focus:ring-leaf/25 outline-none"
            />
          ))}
        </div>

        {error && <div className="mt-4"><ErrorNote>{error}</ErrorNote></div>}

        <Button type="submit" size="lg" loading={loading} className="mt-5 w-full">Verify and continue</Button>

        <div className="mt-4 flex items-center justify-between text-sm">
          <button type="button" onClick={() => nav('/login')} className="text-soil-light hover:text-soil">
            Change number
          </button>
          <button
            type="button"
            onClick={resend}
            disabled={resendIn > 0}
            className="font-semibold text-leaf disabled:text-soil-light"
          >
            {resendIn > 0 ? `Resend in ${resendIn}s` : 'Resend code'}
          </button>
        </div>
        <p className="mt-6 text-xs text-soil-light">Five wrong attempts and the code is cancelled for safety.</p>
      </form>
    </div>
  )
}
