import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bell, Bug, CloudSun, Info, Landmark } from 'lucide-react'
import { Button, Card, CropLoader, Empty } from '../components/ui'
import { api } from '../lib/api'
import { fmtDate } from '../lib/utils'

const ICONS: Record<string, any> = { weather: CloudSun, disease: Bug, scheme: Landmark, info: Info }

export default function Notifications() {
  const qc = useQueryClient()
  const { data = [], isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: async () => (await api.get('/notifications')).data,
  })
  const readAll = useMutation({
    mutationFn: async () => api.post('/notifications/read-all'),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  })

  if (isLoading) return <CropLoader label="Loading alerts…" />

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-xl font-bold text-leaf-dark">Alerts</h1>
        {data.some((n: any) => !n.read) && (
          <Button variant="ghost" size="sm" onClick={() => readAll.mutate()}>Mark all read</Button>
        )}
      </div>

      {data.length === 0 ? (
        <Empty title="Nothing yet" body="Weather warnings, disease alerts and scheme deadlines will land here." />
      ) : (
        data.map((n: any) => {
          const Icon = ICONS[n.kind] ?? Bell
          return (
            <Card key={n.id} className={n.read ? 'opacity-70' : ''}>
              <div className="flex gap-3">
                <Icon className="mt-0.5 h-5 w-5 shrink-0 text-leaf" />
                <div>
                  <p className="font-semibold text-leaf-dark">{n.title}</p>
                  <p className="mt-0.5 text-sm text-soil">{n.body}</p>
                  <p className="mt-1.5 text-xs text-soil-light">{fmtDate(n.created_at)}</p>
                </div>
              </div>
            </Card>
          )
        })
      )}
    </div>
  )
}
