import { motion } from 'framer-motion'
import { Bus, Train, Car, Bike, MapPin, Zap } from 'lucide-react'

const FEATURES = [
  { icon: Bus, label: 'Bus & Transit', desc: 'Routes, schedules, BRT systems' },
  { icon: Train, label: 'Rail & Metro', desc: 'Networks, high-speed rail' },
  { icon: Car, label: 'Road & Traffic', desc: 'Congestion, safety, planning' },
  { icon: Bike, label: 'Micromobility', desc: 'Cycling, e-scooters, walking' },
  { icon: MapPin, label: 'Journey Planning', desc: 'Multi-modal trip building' },
  { icon: Zap, label: 'EV & Clean Transport', desc: 'Charging, sustainability' },
]

export function WelcomeScreen() {
  return (
    <div className="flex-1 flex items-center justify-center px-4 py-8">
      <div className="max-w-lg w-full text-center">
        {/* Logo */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5, ease: [0.32, 0.72, 0, 1] }}
          className="mb-8"
        >
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 mx-auto flex items-center justify-center mb-4 ring-1 ring-primary/10 shadow-lg shadow-primary/5">
            <Bus className="w-8 h-8 text-primary" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground mb-2">
            MOVA
          </h1>
          <p className="text-muted-foreground/70 text-balance leading-relaxed">
            Your intelligent Transport &amp; Mobility assistant.
            Ask about routes, schedules, urban planning, EVs, and more.
          </p>
        </motion.div>

        {/* Feature grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-8"
        >
          {FEATURES.map((f) => (
            <div
              key={f.label}
              className="rounded-xl border bg-card/50 p-3.5 text-left hover:bg-muted/40 transition-all duration-200 hover:border-primary/20 cursor-default group"
            >
              <f.icon className="w-4 h-4 text-primary/70 mb-2 group-hover:text-primary transition-colors" />
              <p className="text-sm font-medium text-foreground/80">
                {f.label}
              </p>
              <p className="text-[11px] text-muted-foreground/50 mt-0.5">
                {f.desc}
              </p>
            </div>
          ))}
        </motion.div>

        {/* Tip */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="text-xs text-muted-foreground/40"
        >
          Ask a question or choose a topic to get started
        </motion.p>
      </div>
    </div>
  )
}
