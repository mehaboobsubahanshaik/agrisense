import { useMutation } from '@tanstack/react-query'
import { TrendingUp } from 'lucide-react'
import { useState } from 'react'
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { Button, Card, CropLoader, Field, Input } from '../components/ui'
import { api } from '../lib/api'

const COLORS = ['#2E7D32', '#81C784', '#FFC107', '#6D4C41']

export default function YieldPage() {
  const [form, setForm] = useState({
    crop: 'rice', area_acres: 2, soil_score: 68, rainfall_mm: 850,
    irrigation: 'borewell', disease_pressure: 'low', fertilizer_applied: true,
  })
  const run = useMutation({ mutationFn: async () => (await api.post('/yield/predict', form)).data })
  const r = run.data
  const set = (k: string, v: any) => setForm((f) => ({ ...f, [k]: v }))

  const factorData = r ? Object.entries(r.factors)
    .filter(([k]) => k.endsWith('_factor'))
    .map(([k, v]: any) => ({ name: k.replace('_factor', ''), value: Number(v) })) : []

  return (
    <div className="grid gap-4 lg:grid-cols-[400px,1fr]">
      <Card>
        <h1 className="font-display text-xl font-bold text-leaf-dark">Yield prediction</h1>
        <p className="mt-1 text-sm text-soil">An explainable estimate - you can see exactly which factor costs you how much.</p>
        <div className="mt-4 space-y-3">
          <Field label="Crop">
            <select className="input" value={form.crop} onChange={(e) => set('crop', e.target.value)}>
              {['rice', 'wheat', 'maize', 'cotton', 'groundnut', 'soybean', 'chickpea', 'sugarcane', 'chilli'].map((c) => <option key={c}>{c}</option>)}
            </select>
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Area (acres)"><Input type="number" step="0.5" value={form.area_acres} onChange={(e) => set('area_acres', Number(e.target.value))} /></Field>
            <Field label="Soil score"><Input type="number" value={form.soil_score} onChange={(e) => set('soil_score', Number(e.target.value))} /></Field>
          </div>
          <Field label="Seasonal rain (mm)"><Input type="number" value={form.rainfall_mm} onChange={(e) => set('rainfall_mm', Number(e.target.value))} /></Field>
          <Field label="Irrigation">
            <select className="input" value={form.irrigation} onChange={(e) => set('irrigation', e.target.value)}>
              {['borewell', 'canal', 'drip', 'sprinkler', 'rainfed'].map((s) => <option key={s}>{s}</option>)}
            </select>
          </Field>
          <Field label="Disease pressure">
            <select className="input" value={form.disease_pressure} onChange={(e) => set('disease_pressure', e.target.value)}>
              {['low', 'medium', 'high'].map((s) => <option key={s}>{s}</option>)}
            </select>
          </Field>
          <label className="flex items-center gap-2 text-sm text-soil">
            <input type="checkbox" checked={form.fertilizer_applied}
                   onChange={(e) => set('fertilizer_applied', e.target.checked)}
                   className="h-4 w-4 rounded border-soil-light text-leaf" />
            Recommended fertiliser dose applied
          </label>
        </div>
        <Button size="lg" className="mt-4 w-full" loading={run.isPending} onClick={() => run.mutate()}>
          <TrendingUp className="h-4 w-4" />Predict
        </Button>
      </Card>

      <div className="space-y-4">
        {run.isPending && <CropLoader label="Running the model…" />}
        {!r && !run.isPending && (
          <Card><p className="py-10 text-center text-sm text-soil-light">Your estimate and the levers that change it will appear here.</p></Card>
        )}
        {r && (
          <>
            <Card>
              <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[.18em] text-soil-light">Expected harvest</p>
                  <p className="font-display text-5xl font-bold text-leaf-dark">{r.total_quintals}<span className="ml-2 text-xl text-soil-light">quintals</span></p>
                  <p className="mt-1 text-sm text-soil">{r.per_acre_quintals} q/acre across {r.area_acres} acres · confidence {Math.round(r.confidence * 100)}%</p>
                </div>
                <div className="h-36 w-36">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={factorData} dataKey="value" innerRadius={34} outerRadius={62} paddingAngle={3}>
                        {factorData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                      </Pie>
                      <Tooltip contentStyle={{ borderRadius: 12, border: 'none' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </Card>

            {r.levers.length > 0 && (
              <Card title="How to raise it">
                <ul className="space-y-2 text-sm text-soil">{r.levers.map((l: string) => <li key={l}>• {l}</li>)}</ul>
              </Card>
            )}

            <Card title="Factors used">
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {Object.entries(r.factors).map(([k, v]: any) => (
                  <div key={k} className="rounded-xl bg-leaf-mist p-3 text-center">
                    <p className="font-display text-xl font-bold text-leaf-dark">{v}</p>
                    <p className="text-xs capitalize text-soil">{k.replace(/_/g, ' ')}</p>
                  </div>
                ))}
              </div>
              <p className="mt-3 text-xs text-soil-light">{r.note}</p>
            </Card>
          </>
        )}
      </div>
    </div>
  )
}
