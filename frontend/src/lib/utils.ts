import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs))

export const fmtDate = (iso: string) =>
  new Date(iso).toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' })

export const severityTone = (s?: string) =>
  s === 'high' ? 'bg-danger/10 text-danger'
  : s === 'medium' ? 'bg-grain/20 text-soil-dark'
  : 'bg-leaf-mist text-leaf-dark'
