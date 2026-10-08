import { Link } from 'react-router-dom'
import { Button } from '../components/ui'

export default function NotFound() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center px-5 text-center">
      <svg viewBox="0 0 120 80" className="mb-6 w-56">
        <rect y="60" width="120" height="6" rx="3" fill="#6D4C41" />
        <path d="M30 60V34" stroke="#2E7D32" strokeWidth="3" strokeLinecap="round" />
        <path d="M30 42c0-8 6-14 14-14 0 8-6 14-14 14z" fill="#81C784" />
        <path d="M90 60V38" stroke="#2E7D32" strokeWidth="3" strokeLinecap="round" />
        <path d="M90 46c0-7-5-12-12-12 0 7 5 12 12 12z" fill="#FFC107" />
        <text x="60" y="30" textAnchor="middle" className="fill-leaf-dark font-display" fontSize="30" fontWeight="700">404</text>
      </svg>
      <h1 className="font-display text-2xl font-bold text-leaf-dark">This field is empty</h1>
      <p className="mt-2 max-w-sm text-soil">The page you asked for does not exist. Head back to your dashboard.</p>
      <Link to="/app" className="mt-6"><Button size="lg">Go to dashboard</Button></Link>
    </div>
  )
}
