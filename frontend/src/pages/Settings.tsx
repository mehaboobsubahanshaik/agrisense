import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { LogOut, MapPin, Save, Smartphone } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Card, Field, Input } from '../components/ui'
import { api } from '../lib/api'
import { LANGUAGES, useLang } from '../lib/i18n'
import { fmtDate } from '../lib/utils'
import { useAuth } from '../store/auth'

export default function Settings() {
  const { user, setUser, clear } = useAuth()
  const { lang, setLang } = useLang()
  const qc = useQueryClient()
  const nav = useNavigate()
  const [profile, setProfile] = useState({
    name: user?.name ?? '', state: user?.state ?? '', district: user?.district ?? '',
    lat: user?.lat ?? 17.385, lon: user?.lon ?? 78.4867,
  })

  const { data: farms = [] } = useQuery({ queryKey: ['farms'], queryFn: async () => (await api.get('/farms')).data })
  const { data: sessions = [] } = useQuery({ queryKey: ['sessions'], queryFn: async () => (await api.get('/auth/sessions')).data })
  const [farm, setFarm] = useState<any>(null)
  const current = farm ?? farms[0]

  const saveProfile = useMutation({
    mutationFn: async () => (await api.patch('/auth/me', { ...profile, language: lang })).data,
    onSuccess: (u) => setUser(u),
  })

  const saveFarm = useMutation({
    mutationFn: async () => api.patch(`/farms/${current.id}`, {
      name: current.name, area_acres: Number(current.area_acres), soil_type: current.soil_type,
      irrigation: current.irrigation, lat: Number(current.lat), lon: Number(current.lon),
      crops: typeof current.crops === 'string' ? current.crops.split(',').map((c: string) => c.trim()) : current.crops,
    }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['farms'] }),
  })

  const logoutAll = useMutation({
    mutationFn: async () => api.post('/auth/logout-all'),
    onSuccess: () => { clear(); nav('/login') },
  })

  const useMyLocation = () => {
    navigator.geolocation?.getCurrentPosition(
      (pos) => setProfile((p) => ({ ...p, lat: Number(pos.coords.latitude.toFixed(4)), lon: Number(pos.coords.longitude.toFixed(4)) })),
      () => alert('Location permission was refused. Enter the coordinates by hand.')
    )
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <h1 className="font-display text-xl font-bold text-leaf-dark">Settings</h1>

      <Card title="Your details">
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Name"><Input value={profile.name} onChange={(e) => setProfile({ ...profile, name: e.target.value })} /></Field>
          <Field label="Mobile"><Input value={user?.phone ?? ''} disabled /></Field>
          <Field label="State"><Input value={profile.state} onChange={(e) => setProfile({ ...profile, state: e.target.value })} /></Field>
          <Field label="District"><Input value={profile.district} onChange={(e) => setProfile({ ...profile, district: e.target.value })} /></Field>
          <Field label="Latitude"><Input type="number" step="0.0001" value={profile.lat} onChange={(e) => setProfile({ ...profile, lat: Number(e.target.value) })} /></Field>
          <Field label="Longitude"><Input type="number" step="0.0001" value={profile.lon} onChange={(e) => setProfile({ ...profile, lon: Number(e.target.value) })} /></Field>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={useMyLocation}><MapPin className="h-4 w-4" />Use my location</Button>
          <Button size="sm" loading={saveProfile.isPending} onClick={() => saveProfile.mutate()}><Save className="h-4 w-4" />Save</Button>
        </div>
      </Card>

      <Card title="Language">
        <div className="flex flex-wrap gap-2">
          {LANGUAGES.map((l) => (
            <button key={l.code} onClick={() => setLang(l.code)}
              className={`pill ${lang === l.code ? 'bg-leaf text-white' : 'border border-black/5 bg-white text-soil'}`}>
              {l.native}
            </button>
          ))}
        </div>
        <p className="mt-2 text-xs text-soil-light">Chat answers and read-aloud follow this setting.</p>
      </Card>

      {current && (
        <Card title="Your farm">
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Farm name"><Input value={current.name} onChange={(e) => setFarm({ ...current, name: e.target.value })} /></Field>
            <Field label="Area (acres)"><Input type="number" step="0.5" value={current.area_acres} onChange={(e) => setFarm({ ...current, area_acres: e.target.value })} /></Field>
            <Field label="Soil type">
              <select className="input" value={current.soil_type} onChange={(e) => setFarm({ ...current, soil_type: e.target.value })}>
                {['black', 'red', 'loam', 'clay', 'sandy'].map((s) => <option key={s}>{s}</option>)}
              </select>
            </Field>
            <Field label="Irrigation">
              <select className="input" value={current.irrigation} onChange={(e) => setFarm({ ...current, irrigation: e.target.value })}>
                {['borewell', 'canal', 'drip', 'sprinkler', 'rainfed'].map((s) => <option key={s}>{s}</option>)}
              </select>
            </Field>
            <Field label="Crops (comma separated)">
              <Input value={Array.isArray(current.crops) ? current.crops.join(', ') : current.crops}
                     onChange={(e) => setFarm({ ...current, crops: e.target.value })} />
            </Field>
          </div>
          <Button size="sm" className="mt-3" loading={saveFarm.isPending} onClick={() => saveFarm.mutate()}>
            <Save className="h-4 w-4" />Save farm
          </Button>
        </Card>
      )}

      <Card title="Signed-in devices">
        <ul className="divide-y divide-black/5">
          {sessions.map((s: any) => (
            <li key={s.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
              <div className="min-w-0">
                <p className="flex items-center gap-2 font-medium text-soil-dark">
                  <Smartphone className="h-4 w-4 shrink-0" />
                  <span className="truncate">{s.device || 'Unknown device'}</span>
                </p>
                <p className="text-xs text-soil-light">{fmtDate(s.created_at)} · {s.ip}</p>
              </div>
              <span className={`pill shrink-0 ${s.revoked ? 'bg-black/5 text-soil-light' : 'bg-leaf-mist text-leaf-dark'}`}>
                {s.revoked ? 'ended' : 'active'}
              </span>
            </li>
          ))}
        </ul>
        <Button variant="danger" size="sm" className="mt-3" loading={logoutAll.isPending} onClick={() => logoutAll.mutate()}>
          <LogOut className="h-4 w-4" />Sign out everywhere
        </Button>
      </Card>
    </div>
  )
}
