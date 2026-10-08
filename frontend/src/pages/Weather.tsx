import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, CloudRain, Droplets, Wind } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Line, ComposedChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Card, CropLoader, Empty } from '../components/ui'
import { api } from '../lib/api'
import { fmtDate } from '../lib/utils'

export default function Weather() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['weather'],
    queryFn: async () => (await api.get('/weather')).data,
  })

  if (isLoading) return <CropLoader label="Checking the sky…" />
  if (isError || !data) return <Empty title="Weather unavailable" body="We could not reach the forecast service. Your last saved forecast will show when you reconnect." />

  const chart = data.daily.map((d: any) => ({
    day: fmtDate(d.date), rain: d.rain_mm, tmax: d.tmax, tmin: d.tmin, chance: d.rain_chance,
  }))

  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="horizon !border-0 text-white">
          <p className="text-xs font-semibold uppercase tracking-[.18em] text-leaf-light">Right now</p>
          <p className="mt-1 font-display text-5xl font-bold">{Math.round(data.current.temp_c)}°C</p>
          <p className="text-leaf-light">{data.current.condition}</p>
          <div className="mt-4 space-y-1.5 text-sm text-white/85">
            <p className="flex items-center gap-2"><Droplets className="h-4 w-4" />Humidity {data.current.humidity}%</p>
            <p className="flex items-center gap-2"><Wind className="h-4 w-4" />Wind {Math.round(data.current.wind_kph)} km/h</p>
            <p className="flex items-center gap-2"><CloudRain className="h-4 w-4" />Rain {data.current.rain_mm} mm</p>
          </div>
        </Card>

        <Card title="7-day rain and temperature" className="lg:col-span-2">
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chart}>
                <CartesianGrid strokeDasharray="3 3" stroke="#00000010" vertical={false} />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis yAxisId="left" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} unit="mm" />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} unit="°" />
                <Tooltip contentStyle={{ borderRadius: 12, border: 'none' }} />
                <Bar yAxisId="left" dataKey="rain" fill="#81C784" radius={[6, 6, 0, 0]} name="Rain (mm)" />
                <Line yAxisId="right" type="monotone" dataKey="tmax" stroke="#FFC107" strokeWidth={2.5} dot={false} name="Max °C" />
                <Line yAxisId="right" type="monotone" dataKey="tmin" stroke="#6D4C41" strokeWidth={2} dot={false} name="Min °C" />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <Card title="What to do this week">
        {data.advisory.length === 0 ? (
          <p className="text-sm text-soil-light">Nothing urgent. Normal field operations can continue.</p>
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2">
            {data.advisory.map((a: any, i: number) => (
              <li key={i} className="flex gap-3 rounded-xl bg-field/70 p-3">
                <AlertTriangle className={`h-5 w-5 shrink-0 ${a.level === 'high' ? 'text-danger' : 'text-grain-dark'}`} />
                <div>
                  <p className="text-sm font-semibold text-leaf-dark">{a.title}</p>
                  <p className="mt-0.5 text-sm text-soil">{a.text}</p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card title="Day by day">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {data.daily.map((d: any) => (
            <div key={d.date} className="rounded-xl border border-black/5 p-3">
              <p className="text-sm font-semibold text-leaf-dark">{fmtDate(d.date)}</p>
              <p className="text-xs text-soil-light">{d.condition}</p>
              <p className="mt-2 font-display text-xl font-bold text-soil-dark">{Math.round(d.tmax)}° / {Math.round(d.tmin)}°</p>
              <p className="mt-1 text-xs text-soil">{d.rain_mm} mm · {d.rain_chance}% chance</p>
            </div>
          ))}
        </div>
        <p className="mt-3 text-xs text-soil-light">Source: {data.source}</p>
      </Card>
    </div>
  )
}
