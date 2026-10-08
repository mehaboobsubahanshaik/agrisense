import { useMutation } from '@tanstack/react-query'
import { FlaskConical } from 'lucide-react'
import { useState } from 'react'
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Button, Card, CropLoader, ErrorNote, Field, Input } from '../components/ui'
import { api, apiError } from '../lib/api'

const CROPS = ['rice', 'wheat', 'maize', 'cotton', 'groundnut', 'soybean', 'chickpea', 'tomato', 'chilli', 'onion', 'sugarcane', 'turmeric']

export default function Soil() {
  const [form, setForm] = useState({ crop: 'rice', n: 240, p: 12, k: 180, ph: 6.8, oc: 0.45, moisture: 22, area_acres: 2 })
  const analyse = useMutation({
    mutationFn: async () => (await api.post('/soil/analyze', form)).data,
  })
  const r = analyse.data

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: k === 'crop' ? v : Number(v) }))

  const chart = r ? [
    { nutrient: 'N', value: r.dose_per_acre.N, rating: r.ratings.n },
    { nutrient: 'P₂O₅', value: r.dose_per_acre.P2O5, rating: r.ratings.p },
    { nutrient: 'K₂O', value: r.dose_per_acre.K2O, rating: r.ratings.k },
  ] : []

  return (
    <div className="grid gap-4 lg:grid-cols-[420px,1fr]">
      <Card>
        <h1 className="font-display text-xl font-bold text-leaf-dark">Soil health & fertiliser plan</h1>
        <p className="mt-1 text-sm text-soil">
          Copy the values from your Soil Health Card. We convert them into bags of urea, DAP and MOP for your acreage.
        </p>

        <div className="mt-4 space-y-3">
          <Field label="Crop">
            <select value={form.crop} onChange={(e) => set('crop', e.target.value)} className="input">
              {CROPS.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </Field>
          <div className="grid grid-cols-3 gap-3">
            <Field label="N (kg/ha)"><Input type="number" value={form.n} onChange={(e) => set('n', e.target.value)} /></Field>
            <Field label="P (kg/ha)"><Input type="number" value={form.p} onChange={(e) => set('p', e.target.value)} /></Field>
            <Field label="K (kg/ha)"><Input type="number" value={form.k} onChange={(e) => set('k', e.target.value)} /></Field>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <Field label="pH"><Input type="number" step="0.1" value={form.ph} onChange={(e) => set('ph', e.target.value)} /></Field>
            <Field label="Org. carbon %"><Input type="number" step="0.05" value={form.oc} onChange={(e) => set('oc', e.target.value)} /></Field>
            <Field label="Moisture %"><Input type="number" value={form.moisture} onChange={(e) => set('moisture', e.target.value)} /></Field>
          </div>
          <Field label="Area (acres)"><Input type="number" step="0.5" value={form.area_acres} onChange={(e) => set('area_acres', e.target.value)} /></Field>
        </div>

        <Button size="lg" className="mt-4 w-full" loading={analyse.isPending} onClick={() => analyse.mutate()}>
          <FlaskConical className="h-4 w-4" />Build my plan
        </Button>
        {analyse.isError && <div className="mt-3"><ErrorNote>{apiError(analyse.error)}</ErrorNote></div>}
      </Card>

      <div className="space-y-4">
        {analyse.isPending && <CropLoader label="Working out the dose…" />}
        {!r && !analyse.isPending && (
          <Card>
            <p className="py-10 text-center text-sm text-soil-light">
              Fill in the values on the left. Nothing here is guessed - the doses come from the ICAR recommended
              dose for your crop, corrected up or down 25% by your soil rating.
            </p>
          </Card>
        )}

        {r && (
          <>
            <Card>
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[.18em] text-soil-light">Soil score</p>
                  <p className="font-display text-4xl font-bold text-leaf-dark">{r.score}<span className="text-xl text-soil-light">/100</span></p>
                  <p className="text-sm text-soil">{r.grade} · pH {r.ph_status} · organic carbon {r.oc_status}</p>
                </div>
                <div className="flex gap-2">
                  {Object.entries(r.ratings).map(([k, v]: any) => (
                    <span key={k} className={`pill ${v === 'low' ? 'bg-danger/10 text-danger' : v === 'medium' ? 'bg-grain/20 text-soil-dark' : 'bg-leaf-mist text-leaf-dark'}`}>
                      {k.toUpperCase()} {v}
                    </span>
                  ))}
                </div>
              </div>
              <div className="mt-4 h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chart}>
                    <XAxis dataKey="nutrient" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} unit=" kg" />
                    <Tooltip formatter={(v: any) => [`${v} kg/acre`, 'Dose']} contentStyle={{ borderRadius: 12, border: 'none' }} />
                    <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                      {chart.map((c, i) => (
                        <Cell key={i} fill={c.rating === 'low' ? '#D32F2F' : c.rating === 'medium' ? '#FFC107' : '#2E7D32'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>

            <Card title={`Buy this for ${r.total_for_field.area_acres} acre(s)`}>
              <div className="grid grid-cols-3 gap-3 text-center">
                {[['Urea', r.total_for_field.urea_kg], ['DAP', r.total_for_field.dap_kg], ['MOP', r.total_for_field.mop_kg]].map(([label, kg]: any) => (
                  <div key={label} className="rounded-xl bg-leaf-mist p-3">
                    <p className="font-display text-2xl font-bold text-leaf-dark">{kg}</p>
                    <p className="text-xs font-semibold text-soil">kg {label}</p>
                  </div>
                ))}
              </div>
              <p className="mt-3 text-sm text-soil">That is about {r.total_for_field.urea_bags_45kg} bags of urea (45 kg).</p>
            </Card>

            <Card title="When to apply">
              <ol className="space-y-2.5">
                {r.schedule.map((s: any, i: number) => (
                  <li key={i} className="flex gap-3">
                    <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-leaf text-xs font-bold text-white">{i + 1}</span>
                    <div>
                      <p className="text-sm font-semibold text-leaf-dark">{s.stage}</p>
                      <p className="text-sm text-soil">{s.detail}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </Card>

            {r.corrections.length > 0 && (
              <Card title="Fix these first">
                <ul className="space-y-1.5 text-sm text-soil">{r.corrections.map((c: string) => <li key={c}>• {c}</li>)}</ul>
              </Card>
            )}

            <Card title="Organic route">
              <ul className="space-y-1.5 text-sm text-soil">{r.organic_options.map((c: string) => <li key={c}>• {c}</li>)}</ul>
            </Card>
          </>
        )}
      </div>
    </div>
  )
}
