import { useQuery } from '@tanstack/react-query'
import { ExternalLink, FileText, Search } from 'lucide-react'
import { useState } from 'react'
import { Card, CropLoader, Empty, Input } from '../components/ui'
import { api } from '../lib/api'

const CATEGORIES = ['all', 'income', 'insurance', 'credit', 'soil', 'irrigation', 'energy', 'market']

export default function Schemes() {
  const [q, setQ] = useState('')
  const [cat, setCat] = useState('all')

  const { data = [], isLoading } = useQuery({
    queryKey: ['schemes', cat],
    queryFn: async () => (await api.get('/schemes', { params: cat === 'all' ? {} : { category: cat } })).data,
  })

  const filtered = data.filter((s: any) =>
    !q || s.name.toLowerCase().includes(q.toLowerCase()) || s.benefit.toLowerCase().includes(q.toLowerCase()))

  return (
    <div className="space-y-4">
      <div>
        <h1 className="font-display text-xl font-bold text-leaf-dark">Government schemes</h1>
        <p className="text-sm text-soil">What you get, whether you qualify, which papers to carry, and where to apply.</p>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-soil-light" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search insurance, loan, solar pump…" className="pl-9" />
        </div>
        <div className="flex gap-2 overflow-x-auto pb-1">
          {CATEGORIES.map((c) => (
            <button key={c} onClick={() => setCat(c)}
              className={`pill shrink-0 capitalize ${cat === c ? 'bg-leaf text-white' : 'bg-white text-soil border border-black/5'}`}>
              {c}
            </button>
          ))}
        </div>
      </div>

      {isLoading && <CropLoader label="Fetching schemes…" />}
      {!isLoading && filtered.length === 0 && (
        <Empty title="No schemes match" body="Try a different word, or clear the category filter." />
      )}

      <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
        {filtered.map((s: any) => (
          <Card key={s.code}>
            <div className="flex items-start justify-between gap-3">
              <h3 className="font-display text-lg font-bold leading-snug text-leaf-dark">{s.name}</h3>
              <span className="pill shrink-0 bg-leaf-mist capitalize text-leaf-dark">{s.category}</span>
            </div>
            <p className="mt-2 text-sm text-soil">{s.benefit}</p>

            <p className="label mt-4">Who qualifies</p>
            <p className="text-sm text-soil">{s.eligibility}</p>

            <p className="label mt-4">Papers to carry</p>
            <div className="flex flex-wrap gap-1.5">
              {s.documents.map((d: string) => (
                <span key={d} className="pill bg-field text-soil"><FileText className="h-3 w-3" />{d}</span>
              ))}
            </div>

            <p className="label mt-4">How to apply</p>
            <p className="text-sm text-soil">{s.how_to_apply}</p>

            <div className="mt-4 flex flex-wrap items-center gap-3">
              <a href={s.link} target="_blank" rel="noreferrer"
                 className="inline-flex items-center gap-1.5 text-sm font-semibold text-leaf hover:underline">
                Official portal <ExternalLink className="h-3.5 w-3.5" />
              </a>
              {/* Freshness stated outright. Scheme rules change; the official
                  page is the source of truth and we say when we last saw it. */}
              {s.freshness && (
                <span className={`pill ${
                  s.freshness.state === 'ok' ? 'bg-leaf-mist text-leaf-dark'
                  : s.freshness.state === 'broken' ? 'bg-danger/10 text-danger'
                  : 'bg-grain/20 text-soil'}`}>
                  {s.freshness.text}
                </span>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
