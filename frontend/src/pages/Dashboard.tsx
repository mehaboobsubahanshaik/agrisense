import { useQuery } from '@tanstack/react-query'
import {
  AlertTriangle, Bug, CloudRain, Droplets, Landmark, MessageSquare, Sprout, Sun, TrendingUp,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis } from 'recharts'
import { RainOverlay } from '../components/Ambient'
import { Card, CropLoader, Empty } from '../components/ui'
import { api } from '../lib/api'
import { fmtDate, severityTone } from '../lib/utils'

function Gauge({ value }: { value: number }) {
  const r = 46
  const c = Math.PI * r
  return (
    <div className="relative">
      <svg viewBox="0 0 120 70" className="w-full max-w-[190px]">
        <path d={`M14 62 A ${r} ${r} 0 0 1 106 62`} fill="none" stroke="#E8F5E9" strokeWidth="11" strokeLinecap="round" />
        <path
          d={`M14 62 A ${r} ${r} 0 0 1 106 62`} fill="none" stroke="#2E7D32" strokeWidth="11" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c - (c * Math.min(100, value)) / 100}
          style={{ transition: 'stroke-dashoffset 1s cubic-bezier(.2,.8,.2,1)' }}
        />
        <text x="60" y="58" textAnchor="middle" className="fill-leaf-dark font-display" fontSize="26" fontWeight="700">
          {Math.round(value)}
        </text>
      </svg>
    </div>
  )
}

export default function Dashboard() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => (await api.get('/dashboard/summary')).data,
  })

  if (isLoading) return <CropLoader label="Reading your field…" />
  if (isError || !data) return <Empty title="Dashboard unavailable" body="We could not reach the server. Check your connection and pull to refresh." />

  const w = data.weather
  const raining = (w.current.rain_mm ?? 0) > 0.2 || w.daily[0]?.rain_chance > 60
  const chart = w.daily.map((d: any) => ({ day: fmtDate(d.date).split(' ')[0], rain: d.rain_mm, tmax: d.tmax }))

  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-3">
        {/* today's weather - hero card */}
        <Card className="horizon relative overflow-hidden !border-0 text-white lg:col-span-2">
          {raining && <RainOverlay />}
          <div className="relative flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[.18em] text-leaf-light">Today at your farm</p>
              <p className="mt-1 font-display text-5xl font-bold">{Math.round(w.current.temp_c)}°C</p>
              <p className="text-leaf-light">{w.current.condition}</p>
              <div className="mt-3 flex flex-wrap gap-4 text-sm text-white/85">
                <span className="inline-flex items-center gap-1.5"><Droplets className="h-4 w-4" />{w.current.humidity}% humidity</span>
                <span className="inline-flex items-center gap-1.5"><CloudRain className="h-4 w-4" />{data.water.next_3_day_rain_mm} mm in 3 days</span>
                <span className="inline-flex items-center gap-1.5"><Sun className="h-4 w-4" />wind {Math.round(w.current.wind_kph)} km/h</span>
              </div>
            </div>
            <div className="h-24 w-full max-w-[240px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chart}>
                  <defs>
                    <linearGradient id="rainfill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#FFC107" stopOpacity={0.8} />
                      <stop offset="100%" stopColor="#FFC107" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="day" tick={{ fill: '#C8E6C9', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ borderRadius: 12, border: 'none', fontSize: 12 }} formatter={(v: any) => [`${v} mm`, 'Rain']} />
                  <Area type="monotone" dataKey="rain" stroke="#FFC107" fill="url(#rainfill)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
          <p className="relative mt-3 text-xs text-white/50">Source: {w.source}</p>
        </Card>

        {/* farm score */}
        <Card title="Farm score">
          <div className="flex items-center gap-4">
            <Gauge value={data.farm.score} />
            <div className="text-sm text-soil">
              <p><span className="font-semibold text-leaf-dark">{data.farm.name}</span> · {data.farm.area_acres} acres</p>
              <p className="mt-1">Soil {data.soil.score || '—'} · Crop health {data.crop_health}</p>
              <p className="mt-1 text-xs text-soil-light">Weighted from your soil test, disease reports and open alerts.</p>
            </div>
          </div>
        </Card>
      </div>

      {/* advisory strip */}
      {w.advisory?.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {w.advisory.map((a: any, i: number) => (
            <div key={i} className="card flex gap-3 !p-4">
              <AlertTriangle className={`h-5 w-5 shrink-0 ${a.level === 'high' ? 'text-danger' : 'text-grain-dark'}`} />
              <div>
                <p className="text-sm font-semibold text-leaf-dark">{a.title}</p>
                <p className="mt-0.5 text-sm text-soil">{a.text}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Card title="Water requirement">
          <p className="font-display text-3xl font-bold text-leaf-dark">{data.water.irrigation_need_mm} mm</p>
          <p className="mt-1 text-sm text-soil">{data.water.advice}</p>
          <p className="mt-2 text-xs text-soil-light">Crop coefficient × reference ET, minus forecast rain.</p>
        </Card>

        <Card title="Disease alerts" action={<Link to="/app/scan" className="text-sm font-semibold text-leaf">Scan a leaf</Link>}>
          {data.disease_alerts.length === 0 ? (
            <p className="py-3 text-sm text-soil-light">No scans yet. Photograph a leaf to start a health record for this field.</p>
          ) : (
            <ul className="space-y-2">
              {data.disease_alerts.slice(0, 4).map((d: any) => (
                <li key={d.id} className="flex items-center justify-between gap-3 text-sm">
                  <span className="flex items-center gap-2"><Bug className="h-4 w-4 text-soil-light" />{d.disease}</span>
                  <span className={`pill ${severityTone(d.severity)}`}>{d.severity}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card title="Soil health" action={<Link to="/app/soil" className="text-sm font-semibold text-leaf">Analyse</Link>}>
          {data.soil.score ? (
            <>
              <p className="font-display text-3xl font-bold text-leaf-dark">{data.soil.score}<span className="text-lg text-soil-light">/100</span></p>
              <p className="mt-1 text-sm text-soil">{data.soil.grade} for {data.soil.crop}</p>
            </>
          ) : (
            <p className="py-3 text-sm text-soil-light">Enter your soil health card values to get a fertiliser plan in bags per acre.</p>
          )}
        </Card>

        <Card title="Yield prediction" action={<Link to="/app/yield" className="text-sm font-semibold text-leaf">Update</Link>}>
          {data.yield ? (
            <>
              <p className="font-display text-3xl font-bold text-leaf-dark">
                {data.yield.total_quintals} <span className="text-lg text-soil-light">quintals</span>
              </p>
              <p className="mt-1 text-sm text-soil">{data.yield.crop} · confidence {Math.round(data.yield.confidence * 100)}%</p>
            </>
          ) : (
            <p className="py-3 flex items-center gap-2 text-sm text-soil-light"><TrendingUp className="h-4 w-4" />Run a prediction to plan storage and sale.</p>
          )}
        </Card>

        <Card title="Latest advice" action={<Link to="/app/chat" className="text-sm font-semibold text-leaf">Ask</Link>}>
          {data.latest_chat ? (
            <p className="text-sm leading-relaxed text-soil line-clamp-5">{data.latest_chat.content}</p>
          ) : (
            <p className="py-3 flex items-center gap-2 text-sm text-soil-light"><MessageSquare className="h-4 w-4" />Ask anything about your crop, in your language.</p>
          )}
        </Card>

        <Card title="Schemes for you" action={<Link to="/app/schemes" className="text-sm font-semibold text-leaf">All</Link>}>
          <ul className="space-y-2.5">
            {data.schemes.map((s: any) => (
              <li key={s.code} className="text-sm">
                <p className="flex items-center gap-2 font-semibold text-leaf-dark"><Landmark className="h-4 w-4" />{s.name}</p>
                <p className="mt-0.5 line-clamp-2 text-soil">{s.benefit}</p>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      {data.recent_uploads.length > 0 && (
        <Card title="Recent uploads">
          <div className="flex gap-3 overflow-x-auto pb-1">
            {data.recent_uploads.map((u: any, i: number) => (
              <img key={i} src={u.url} alt="" className="h-24 w-24 shrink-0 rounded-xl object-cover" loading="lazy" />
            ))}
          </div>
        </Card>
      )}

      <p className="flex items-center gap-2 pt-2 text-xs text-soil-light">
        <Sprout className="h-4 w-4" />
        Advisory only. Confirm chemical doses with your local agriculture officer before spraying.
      </p>
    </div>
  )
}
