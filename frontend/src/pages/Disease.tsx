import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Camera, Leaf, Upload, Volume2 } from 'lucide-react'
import { useRef, useState } from 'react'
import { Button, Card, CropLoader, ErrorNote } from '../components/ui'
import { api, apiError } from '../lib/api'
import { speak, useLang } from '../lib/i18n'
import { fmtDate, severityTone } from '../lib/utils'

export default function Disease() {
  const lang = useLang((s) => s.lang)
  const qc = useQueryClient()
  const [preview, setPreview] = useState<string | null>(null)
  const [crop, setCrop] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  const { data: reports = [] } = useQuery({
    queryKey: ['disease-reports'],
    queryFn: async () => (await api.get('/disease/reports')).data,
  })

  const analyse = useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData()
      form.append('file', file)
      form.append('crop_hint', crop)
      return (await api.post('/disease/analyze', form, { headers: { 'Content-Type': 'multipart/form-data' } })).data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['disease-reports'] }),
  })

  const onPick = (file?: File) => {
    if (!file) return
    setPreview(URL.createObjectURL(file))
    analyse.mutate(file)
  }

  const result = analyse.data
  const adv = result?.advisory

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr,1fr]">
      <div className="space-y-4">
        <Card>
          <h1 className="font-display text-xl font-bold text-leaf-dark">Scan a crop photo</h1>
          <p className="mt-1 text-sm text-soil">
            Fill the frame with one affected leaf in daylight, against a plain background. Avoid shadows.
          </p>

          <label className="label mt-4">Crop (optional, improves the advice)</label>
          <input
            list="crops" value={crop} onChange={(e) => setCrop(e.target.value)}
            placeholder="rice, cotton, tomato…" className="input"
          />
          <datalist id="crops">
            {['rice', 'wheat', 'maize', 'cotton', 'tomato', 'chilli', 'groundnut', 'soybean'].map((c) => <option key={c} value={c} />)}
          </datalist>

          <input
            ref={fileRef} type="file" accept="image/*" capture="environment" hidden
            onChange={(e) => onPick(e.target.files?.[0])}
          />
          <div className="mt-4 grid grid-cols-2 gap-3">
            <Button size="lg" onClick={() => fileRef.current?.click()}><Camera className="h-4 w-4" />Take photo</Button>
            <Button size="lg" variant="outline" onClick={() => fileRef.current?.click()}><Upload className="h-4 w-4" />Choose file</Button>
          </div>

          {preview && (
            <img src={result?.annotated_image ?? preview} alt="Uploaded crop"
                 className="mt-4 w-full rounded-xl object-cover" />
          )}
          {analyse.isPending && <CropLoader label="Looking at the leaf…" />}
          {analyse.isError && <div className="mt-3"><ErrorNote>{apiError(analyse.error)}</ErrorNote></div>}
        </Card>

        {reports.length > 0 && (
          <Card title="Past scans">
            <ul className="divide-y divide-black/5">
              {reports.map((r: any) => (
                <li key={r.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                  <div>
                    <p className="font-semibold text-leaf-dark">{r.disease}</p>
                    <p className="text-xs text-soil-light">{fmtDate(r.created_at)} · {Math.round(r.confidence * 100)}% · {r.crop}</p>
                  </div>
                  <span className={`pill ${severityTone(r.severity)}`}>{r.severity}</span>
                </li>
              ))}
            </ul>
          </Card>
        )}
      </div>

      <div className="space-y-4">
        {!result && (
          <Card>
            <div className="py-10 text-center">
              <Leaf className="mx-auto mb-3 h-10 w-10 text-leaf-light" />
              <h3 className="font-display text-lg text-leaf-dark">Your report will appear here</h3>
              <p className="mx-auto mt-1 max-w-xs text-sm text-soil-light">
                You get the likely disease, how far it has spread, and three ways to treat it: chemical, organic and cultural.
              </p>
            </div>
          </Card>
        )}

        {adv && (
          <>
            <Card>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[.18em] text-soil-light">Detected</p>
                  <h2 className="font-display text-2xl font-bold text-leaf-dark">{adv.label}</h2>
                  <p className="mt-1 text-sm text-soil">{adv.symptoms}</p>
                </div>
                <div className="text-right">
                  <span className={`pill ${severityTone(adv.severity)}`}>{adv.severity} severity</span>
                  <p className="mt-1 text-sm text-soil-light">{Math.round((adv.confidence ?? 0) * 100)}% confidence</p>
                </div>
              </div>
              <p className="mt-3 text-xs text-soil-light">Model: {result.model}</p>
              <Button variant="ghost" size="sm" className="mt-2"
                      onClick={() => speak(`${adv.label}. ${adv.symptoms}. ${(adv.remedies?.chemical ?? []).join('. ')}`, lang)}>
                <Volume2 className="h-4 w-4" />Read aloud
              </Button>
            </Card>

            {adv.remedies && (
              <>
                <Card title="Chemical control">
                  <ul className="space-y-1.5 text-sm text-soil">
                    {(adv.remedies.chemical ?? []).map((r: string) => <li key={r}>• {r}</li>)}
                    {(adv.remedies.chemical ?? []).length === 0 && <li>No chemical treatment needed.</li>}
                  </ul>
                  <p className="mt-3 rounded-xl bg-grain/15 px-3 py-2 text-xs text-soil-dark">{adv.safety}</p>
                </Card>
                <Card title="Organic options">
                  <ul className="space-y-1.5 text-sm text-soil">
                    {(adv.remedies.organic ?? []).map((r: string) => <li key={r}>• {r}</li>)}
                  </ul>
                </Card>
                <Card title="Field practice">
                  <ul className="space-y-1.5 text-sm text-soil">
                    {(adv.remedies.cultural ?? []).map((r: string) => <li key={r}>• {r}</li>)}
                  </ul>
                </Card>
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}
