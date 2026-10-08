import { Leaf, Phone } from 'lucide-react'
import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Button, ErrorNote, Field, Input } from '../components/ui'
import { api, apiError } from '../lib/api'
import { useAuth } from '../store/auth'

export default function Login() {
  const [phone, setPhone] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const nav = useNavigate()
  const access = useAuth((s) => s.access)

  if (access) return <Navigate to="/app" replace />

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    const digits = phone.replace(/\D/g, '')
    if (digits.length < 10) return setError('Enter the 10-digit mobile number you use for your bank and land records.')
    setError(''); setLoading(true)
    try {
      const { data } = await api.post('/auth/request-otp', { phone: digits })
      nav('/verify', { state: { phone: digits.slice(-10), ...data } })
    } catch (err) {
      setError(apiError(err, 'Could not send the code. Try again in a moment.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid min-h-dvh lg:grid-cols-2">
      <div className="horizon relative hidden flex-col justify-between p-10 lg:flex">
        <div className="flex items-center gap-2.5">
          <Leaf className="h-7 w-7 text-grain" />
          <span className="font-display text-xl font-bold text-white">AgriSense AI</span>
        </div>
        <div className="max-w-sm">
          <h2 className="font-display text-3xl font-bold leading-tight text-white">
            One number. No password to forget.
          </h2>
          <p className="mt-3 text-leaf-light">
            We send a 6-digit code that works for 5 minutes. Nothing else is stored on your phone.
          </p>
        </div>
        <p className="text-xs text-white/50">Advisory service · not a substitute for a field visit</p>
      </div>

      <div className="flex items-center justify-center px-5 py-12">
        <form onSubmit={submit} className="w-full max-w-sm">
          <Link to="/" className="mb-8 inline-flex items-center gap-2 text-leaf-dark lg:hidden">
            <Leaf className="h-6 w-6 text-leaf" />
            <span className="font-display text-lg font-bold">AgriSense AI</span>
          </Link>
          <h1 className="font-display text-2xl font-bold text-leaf-dark">Sign in</h1>
          <p className="mb-6 mt-1 text-sm text-soil">We will text you a code to confirm it is your number.</p>

          <Field label="Mobile number" hint="Indian mobile number, 10 digits.">
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-soil-light" />
              <Input
                autoFocus
                inputMode="numeric"
                autoComplete="tel"
                placeholder="98765 43210"
                className="pl-9 text-lg tracking-wide"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </div>
          </Field>

          {error && <div className="mt-3"><ErrorNote>{error}</ErrorNote></div>}

          <Button type="submit" size="lg" loading={loading} className="mt-5 w-full">Send code</Button>

          <p className="mt-6 text-xs leading-relaxed text-soil-light">
            By continuing you agree that AgriSense gives advice only. Confirm chemical doses with your
            agriculture officer before spraying.
          </p>
        </form>
      </div>
    </div>
  )
}
