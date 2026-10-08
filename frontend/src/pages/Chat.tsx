import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { FileText, Mic, Paperclip, Send, Trash2, Volume2, X } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Button, Card, CropLoader } from '../components/ui'
import { api, apiError } from '../lib/api'
import { SPEECH_TAG, speak, useLang, useT } from '../lib/i18n'

type Attachment = {
  kind: 'image' | 'file'
  url: string
  name: string
  disease_local?: string
  severity?: string
}

type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
  engine?: string
  attachment?: Attachment | null
  pending?: boolean
}

const ACCEPT = 'image/jpeg,image/png,image/webp,application/pdf,text/plain,text/csv'

/** Minimal markdown: **bold** headings and - bullets are all the backend emits. */
function Rich({ text }: { text: string }) {
  return (
    <>
      {text.split('\n').map((line, i) => {
        if (!line.trim()) return <div key={i} className="h-2" />
        const bold = line.match(/^\*\*(.+?)\*\*(.*)$/)
        if (bold) {
          return (
            <p key={i} className="mt-1 font-semibold">
              {bold[1]}
              <span className="font-normal">{bold[2]}</span>
            </p>
          )
        }
        if (line.startsWith('- ')) {
          return <p key={i} className="ml-3">• {line.slice(2)}</p>
        }
        const italic = line.match(/^_(.+)_$/)
        if (italic) return <p key={i} className="mt-1 text-xs opacity-70">{italic[1]}</p>
        return <p key={i}>{line}</p>
      })}
    </>
  )
}

export default function Chat() {
  const lang = useLang((s) => s.lang)
  const t = useT()
  const qc = useQueryClient()
  const [text, setText] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string>('')
  const [listening, setListening] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)
  const endRef = useRef<HTMLDivElement>(null)

  const starters = useMemo(() => [t('s1'), t('s2'), t('s3'), t('s4')], [lang])

  const { data: history = [], isLoading } = useQuery<Message[]>({
    queryKey: ['chat-history'],
    queryFn: async () => (await api.get('/chat/history')).data,
  })

  /** One mutation for both paths: JSON when there is no file, multipart when there is. */
  const ask = useMutation({
    mutationFn: async ({ message, upload }: { message: string; upload: File | null }) => {
      if (!upload) {
        return (await api.post('/chat', { message, language: lang })).data
      }
      const form = new FormData()
      form.append('file', upload)
      form.append('message', message)
      form.append('language', lang)
      return (await api.post('/chat/attach', form)).data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['chat-history'] }),
  })

  const clear = useMutation({
    mutationFn: async () => api.delete('/chat/history'),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['chat-history'] }),
  })

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history, ask.isPending])

  // Revoke the object URL when the preview changes, or the tab leaks memory
  // every time a farmer swaps photos.
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview) }, [preview])

  const pickFile = (f: File | null) => {
    if (preview) URL.revokeObjectURL(preview)
    setFile(f)
    setPreview(f && f.type.startsWith('image/') ? URL.createObjectURL(f) : '')
  }

  const send = (message: string) => {
    const trimmed = message.trim()
    if (!trimmed && !file) return
    const upload = file
    setText('')
    pickFile(null)
    if (fileRef.current) fileRef.current.value = ''
    ask.mutate({ message: trimmed, upload })
  }

  /** Browser speech recognition keeps voice usable on a slow connection -
   *  no audio upload, no server round trip. */
  const listen = () => {
    const SR = (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition
    if (!SR) return alert(t('voiceUnsupported'))
    const rec = new SR()
    rec.lang = SPEECH_TAG[lang] ?? 'en-IN'
    rec.interimResults = false
    rec.onresult = (e: any) => send(e.results[0][0].transcript)
    rec.onend = () => setListening(false)
    rec.onerror = () => setListening(false)
    setListening(true)
    rec.start()
  }

  const canSend = Boolean(text.trim() || file)

  return (
    <div className="mx-auto flex h-[calc(100dvh-8.5rem)] max-w-3xl flex-col md:h-[calc(100dvh-6rem)]">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-xl font-bold text-leaf-dark">{t('chatTitle')}</h1>
          <p className="text-sm text-soil-light">{t('chatSubtitle')}</p>
        </div>
        {history.length > 0 && (
          <Button variant="ghost" size="sm" onClick={() => clear.mutate()}>
            <Trash2 className="h-4 w-4" />{t('clear')}
          </Button>
        )}
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto pr-1">
        {isLoading && <CropLoader label={t('loadingChat')} />}

        {!isLoading && history.length === 0 && (
          <Card>
            <p className="text-sm text-soil">{t('chatStartersIntro')}</p>
            <div className="mt-3 grid gap-2">
              {starters.map((s) => (
                <button key={s} onClick={() => send(s)}
                  className="rounded-xl border border-leaf/20 bg-leaf-mist/60 px-3.5 py-2.5 text-left text-sm text-leaf-dark transition hover:bg-leaf-mist">
                  {s}
                </button>
              ))}
            </div>
            <p className="mt-3 flex items-center gap-1.5 text-xs text-soil-light">
              <Paperclip className="h-3.5 w-3.5" />{t('attachHint')}
            </p>
          </Card>
        )}

        {history.map((m) => (
          <div key={m.id} className={m.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
            <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-[15px] leading-relaxed shadow-card ${
              m.role === 'user' ? 'bg-leaf text-white' : 'bg-white text-soil-dark'}`}>

              {m.attachment && (
                <div className="mb-2">
                  {m.attachment.kind === 'image' ? (
                    <img src={m.attachment.url} alt={t('attachedPhoto')}
                      className="max-h-52 w-full rounded-xl object-cover" loading="lazy" />
                  ) : (
                    <span className="inline-flex items-center gap-1.5 rounded-lg bg-black/10 px-2.5 py-1.5 text-xs">
                      <FileText className="h-3.5 w-3.5" />{m.attachment.name}
                    </span>
                  )}
                </div>
              )}

              <div className="whitespace-pre-wrap"><Rich text={m.content} /></div>

              {m.role === 'assistant' && (
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <button onClick={() => speak(m.content, lang)}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-leaf">
                    <Volume2 className="h-3.5 w-3.5" />{t('readAloud')}
                  </button>
                  {(m.sources ?? []).map((s) => (
                    <span key={s} className="pill bg-leaf-mist text-leaf-dark">{s}</span>
                  ))}
                  {m.engine === 'offline-rag' && (
                    <span className="pill bg-grain/20 text-soil">{t('offlineAnswer')}</span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {ask.isPending && <CropLoader label={file || preview ? t('analysingPhoto') : t('thinking')} />}
        {ask.isError && <p className="text-sm text-danger">{apiError(ask.error)}</p>}
        <div ref={endRef} />
      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); send(text) }}
        className="mt-3 rounded-2xl border border-black/5 bg-white p-2 shadow-card"
      >
        {file && (
          <div className="mb-2 flex items-center gap-2 rounded-xl bg-leaf-mist/60 p-2">
            {preview ? (
              <img src={preview} alt="" className="h-12 w-12 rounded-lg object-cover" />
            ) : (
              <FileText className="h-8 w-8 text-leaf" />
            )}
            <span className="flex-1 truncate text-xs text-soil">{file.name}</span>
            <button type="button" onClick={() => pickFile(null)} aria-label={t('remove')}
              className="rounded-full p-1 text-soil-light hover:bg-black/5">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        <div className="flex items-end gap-2">
          <input
            ref={fileRef} type="file" accept={ACCEPT} className="hidden"
            onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
          />
          <Button type="button" variant="outline" size="sm" aria-label={t('attach')}
            title={t('attachHint')} onClick={() => fileRef.current?.click()}>
            <Paperclip className="h-4 w-4" />
          </Button>

          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(text) } }}
            rows={1}
            placeholder={t('chatPlaceholder')}
            className="max-h-32 flex-1 resize-none bg-transparent px-2 py-2.5 text-[15px] outline-none"
          />

          <Button type="button" variant={listening ? 'danger' : 'outline'} size="sm"
            onClick={listen} aria-label={t('speakNow')}>
            <Mic className="h-4 w-4" />
          </Button>
          <Button type="submit" size="sm" disabled={!canSend || ask.isPending} aria-label={t('send')}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </form>
    </div>
  )
}
