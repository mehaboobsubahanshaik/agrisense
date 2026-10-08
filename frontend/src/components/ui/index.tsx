import { motion } from 'framer-motion'
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from 'react'
import { cn } from '../../lib/utils'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'ghost' | 'outline' | 'danger' | 'grain'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
}

export function Button({ variant = 'primary', size = 'md', loading, className, children, ...rest }: ButtonProps) {
  const variants = {
    primary: 'bg-leaf text-white hover:bg-leaf-dark shadow-lift disabled:bg-leaf/50',
    grain: 'bg-grain text-soil-dark hover:bg-grain-dark',
    outline: 'border border-leaf/40 text-leaf-dark bg-white hover:bg-leaf-mist',
    ghost: 'text-soil-dark hover:bg-black/5',
    danger: 'bg-danger text-white hover:brightness-95',
  }
  const sizes = { sm: 'h-9 px-3 text-sm', md: 'h-11 px-4 text-[15px]', lg: 'h-13 px-6 text-base py-3.5' }
  return (
    <button
      {...rest}
      disabled={rest.disabled || loading}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition active:scale-[.98]',
        'disabled:cursor-not-allowed disabled:opacity-70',
        variants[variant], sizes[size], className
      )}
    >
      {loading && <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />}
      {children}
    </button>
  )
}

export function Card({ className, children, title, action }: {
  className?: string; children: ReactNode; title?: string; action?: ReactNode
}) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.2, 0.8, 0.2, 1] }}
      className={cn('card', className)}
    >
      {(title || action) && (
        <header className="mb-3 flex items-center justify-between gap-3">
          {title && <h3 className="text-base font-semibold text-leaf-dark">{title}</h3>}
          {action}
        </header>
      )}
      {children}
    </motion.section>
  )
}

export function Input({ className, ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...rest} className={cn('input', className)} />
}

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <div>
      <span className="label">{label}</span>
      {children}
      {hint && <p className="mt-1 text-xs text-soil-light">{hint}</p>}
    </div>
  )
}

export function Pill({ tone = 'leaf', children }: { tone?: string; children: ReactNode }) {
  return <span className={cn('pill', tone)}>{children}</span>
}

/** Growing-seedling loader: the app's loading state, not a generic spinner. */
export function CropLoader({ label = 'Growing your answer…' }: { label?: string }) {
  return (
    <div className="flex flex-col items-center gap-3 py-8 text-soil-light" role="status" aria-live="polite">
      <svg viewBox="0 0 48 48" className="h-12 w-12">
        <path d="M24 44V20" stroke="#2E7D32" strokeWidth="3" strokeLinecap="round"
              className="origin-bottom animate-sprout" />
        <path d="M24 26c0-7 5-12 12-12 0 7-5 12-12 12z" fill="#81C784"
              className="origin-bottom-left animate-sway" />
        <path d="M24 34c0-6-5-10-10-10 0 6 5 10 10 10z" fill="#FFC107"
              className="origin-bottom-right animate-sway" style={{ animationDelay: '.4s' }} />
        <rect x="10" y="43" width="28" height="3" rx="1.5" fill="#6D4C41" />
      </svg>
      <p className="text-sm">{label}</p>
    </div>
  )
}

export function Empty({ title, body, action }: { title: string; body: string; action?: ReactNode }) {
  return (
    <div className="rounded-2xl border border-dashed border-soil-light/40 bg-white/60 p-8 text-center">
      <h4 className="font-display text-lg text-leaf-dark">{title}</h4>
      <p className="mx-auto mt-1 max-w-sm text-sm text-soil-light">{body}</p>
      {action && <div className="mt-4 flex justify-center">{action}</div>}
    </div>
  )
}

export function ErrorNote({ children }: { children: ReactNode }) {
  return (
    <p role="alert" className="rounded-xl bg-danger/10 px-3 py-2 text-sm font-medium text-danger">{children}</p>
  )
}
