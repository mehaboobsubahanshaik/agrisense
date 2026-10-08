import { motion } from 'framer-motion'
import { Bug, CloudSun, Landmark, Leaf, MessageSquare, Sprout, WifiOff } from 'lucide-react'
import { Link } from 'react-router-dom'
import { FloatingLeaves } from '../components/Ambient'
import { Button } from '../components/ui'

const FEATURES = [
  { icon: Bug, title: 'Photograph the problem', body: 'Upload a leaf and get the likely disease, its severity, and the exact spray dose per litre.' },
  { icon: MessageSquare, title: 'Ask in your language', body: 'Type or speak a question. Answers are grounded in ICAR practice notes, not guesswork.' },
  { icon: Sprout, title: 'Fertiliser by the bag', body: 'Enter your soil card values and get urea, DAP and MOP quantities for your acreage, split by stage.' },
  { icon: CloudSun, title: 'Weather that says what to do', body: 'Not just rainfall: whether to spray today, hold the urea, or start sowing.' },
  { icon: Landmark, title: 'Schemes you qualify for', body: 'PM-KISAN, PMFBY, KCC and state schemes with documents and where to apply.' },
  { icon: WifiOff, title: 'Works on a weak signal', body: 'Installs as an app and keeps your last dashboard, reports and advice available offline.' },
]

export default function Landing() {
  return (
    <div className="min-h-dvh">
      <FloatingLeaves count={20} />

      <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
        <div className="flex items-center gap-2.5">
          <Leaf className="h-7 w-7 text-leaf" />
          <span className="font-display text-xl font-bold text-leaf-dark">AgriSense AI</span>
        </div>
        <Link to="/login"><Button size="sm">Farmer sign in</Button></Link>
      </header>

      {/* hero: the horizon band is the thesis - crop rows growing out of soil */}
      <section className="mx-auto max-w-6xl px-5 pb-10 pt-6 sm:pt-12">
        <div className="grid items-center gap-10 lg:grid-cols-[1.1fr,.9fr]">
          <div>
            <p className="mb-3 text-xs font-bold uppercase tracking-[.2em] text-soil-light">
              For smallholder farms in India
            </p>
            <h1 className="font-display text-4xl font-bold leading-[1.05] text-leaf-dark sm:text-5xl lg:text-6xl">
              The advisor your field
              <span className="block text-leaf">has been missing.</span>
            </h1>
            <p className="mt-5 max-w-lg text-lg leading-relaxed text-soil">
              Photograph a sick leaf, ask a question out loud, or type in your soil test.
              AgriSense answers with the dose, the timing and the reason - in Telugu, Hindi or English.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link to="/login"><Button size="lg">Start with your mobile number</Button></Link>
              <a href="#features"><Button size="lg" variant="outline">See what it does</Button></a>
            </div>
            <p className="mt-4 text-sm text-soil-light">No password. A 6-digit code on your phone is all it takes.</p>
          </div>

          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, ease: [0.2, 0.8, 0.2, 1] }}
            className="horizon relative aspect-[4/3] overflow-hidden rounded-3xl shadow-lift"
          >
            <div className="absolute inset-x-0 bottom-0 flex h-2/3 items-end justify-around px-6 pb-7">
              {[0, 1, 2, 3, 4, 5, 6].map((i) => (
                <motion.svg
                  key={i}
                  viewBox="0 0 24 48"
                  className="h-[55%] w-8 origin-bottom text-leaf-light"
                  initial={{ scaleY: 0.1, opacity: 0 }}
                  animate={{ scaleY: 1, opacity: 1 }}
                  transition={{ delay: 0.25 + i * 0.09, duration: 0.8, ease: [0.2, 0.8, 0.2, 1] }}
                >
                  <path d="M12 48V16" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
                  <path d="M12 24c0-6 4-10 10-10 0 6-4 10-10 10z" fill="currentColor" opacity=".85" />
                  <path d="M12 32c0-5-4-9-9-9 0 5 4 9 9 9z" fill="#FFC107" opacity=".9" />
                </motion.svg>
              ))}
            </div>
            <div className="absolute left-5 top-5 rounded-2xl bg-white/95 p-3 shadow-card">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-soil-light">Detected</p>
              <p className="font-display text-lg font-bold text-leaf-dark">Rice blast</p>
              <p className="text-xs text-soil">Tricyclazole 0.6 g/litre · spray at first light</p>
            </div>
          </motion.div>
        </div>
      </section>

      <section id="features" className="mx-auto max-w-6xl px-5 py-12">
        <h2 className="font-display text-2xl font-bold text-leaf-dark sm:text-3xl">Six things it does well</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <div key={f.title} className="card transition hover:shadow-lift">
              <f.icon className="mb-3 h-6 w-6 text-leaf" />
              <h3 className="text-base font-semibold text-leaf-dark">{f.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-soil">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-black/5 py-8 text-center text-sm text-soil-light">
        <p>AgriSense AI · Advisory only. Confirm chemical doses with your local agriculture officer before spraying.</p>
      </footer>
    </div>
  )
}
