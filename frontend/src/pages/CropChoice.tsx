import { useMutation } from '@tanstack/react-query'
import { Sprout } from 'lucide-react'
import { useState } from 'react'
import { Button, Card, CropLoader, Field, Input } from '../components/ui'
import { api } from '../lib/api'

export default function CropChoice() {
  const [form, setForm] = useState({
    n: 250, p: 22, k: 200, ph: 6.9, rainfall_mm: 750, season: 'kharif', irrigation: 'borewell', soil_type: 'black',
  })
  const run = useMutation({ mutationFn: async () => (await api.post('/crop/recommend', form)).data })
  const set = (k: string, v: any) => setForm((f) => ({ ...f, [k]: typeof (f as any)[k] === 'number' ? Number(v) : v }))

  return (
    <div className="grid gap-4 lg:grid-cols-[400px,1fr]">
      <Card>
        <h1 className="font-display text-xl font-bold text-leaf-dark">What should I sow?</h1>
        <p className="mt-1 text-sm text-soil">Ranked on your soil chemistry, water availability and season.</p>
        <div className="mt-4 space-y-3">
          <div className="grid grid-cols-3 gap-3">
            <Field label="N"><Input type="number" value={form.n} onChange={(e) => set('n', e.target.value)} /></Field>
            <Field label="P"><Input type="number" value={form.p} onChange={(e) => set('p', e.target.value)} /></Field>
            <Field label="K"><Input type="number" value={form.k} onChange={(e) => set('k', e.target.value)} /></Field>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Field label="pH"><Input type="number" step="0.1" value={form.ph} onChange={(e) => set('ph', e.target.value)} /></Field>
            <Field label="Seasonal rain (mm)"><Input type="number" value={form.rainfall_mm} onChange={(e) => set('rainfall_mm', e.target.value)} /></Field>
          </div>
          <Field label="Season">
            <select className="input" value={form.season} onChange={(e) => set('season', e.target.value)}>
              {['kharif', 'rabi', 'summer'].map((s) => <option key={s}>{s}</option>)}
            </select>
          </Field>
          <Field label="Irrigation">
            <select className="input" value={form.irrigation} onChange={(e) => set('irrigation', e.target.value)}>
              {['borewell', 'canal', 'drip', 'sprinkler', 'rainfed'].map((s) => <option key={s}>{s}</option>)}
            </select>
          </Field>
          <Field label="Soil type">
            <select className="input" value={form.soil_type} onChange={(e) => set('soil_type', e.target.value)}>
              {['black', 'red', 'loam', 'clay', 'sandy'].map((s) => <option key={s}>{s}</option>)}
            </select>
          </Field>
        </div>
        <Button size="lg" className="mt-4 w-full" loading={run.isPending} onClick={() => run.mutate()}>
          <Sprout className="h-4 w-4" />Rank crops
        </Button>
      </Card>

      <div className="space-y-3">
        {run.isPending && <CropLoader label="Comparing crops…" />}
        {!run.data && !run.isPending && (
          <Card><p className="py-10 text-center text-sm text-soil-light">Your ranked shortlist will appear here, with the reason for each position.</p></Card>
        )}
        {run.data?.recommendations.map((c: any, i: number) => (
          <Card key={c.crop}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[.18em] text-soil-light">Rank {i + 1}</p>
                <h3 className="font-display text-xl font-bold capitalize text-leaf-dark">{c.crop}</h3>
                <ul className="mt-2 space-y-1 text-sm text-soil">{c.reasons.map((r: string) => <li key={r}>• {r}</li>)}</ul>
              </div>
              <div className="text-right">
                <p className="font-display text-3xl font-bold text-leaf">{c.score}</p>
                <p className="text-xs text-soil-light">match score</p>
                <p className="mt-2 text-sm text-soil">~{c.expected_yield_q_per_acre} q/acre</p>
                <span className="pill mt-1 bg-leaf-mist text-leaf-dark">{c.water_need} water</span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
