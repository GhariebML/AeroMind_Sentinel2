import { motion } from 'framer-motion';
import { Activity, Battery, FileText, Play, Radio, Route, Satellite, ShieldAlert } from 'lucide-react';
import type { ReactNode } from 'react';

const heroMetrics = [
  { label: 'MOTA', value: '83.2%' },
  { label: 'Energy saved', value: '34.8%' },
  { label: 'Latency', value: '~45ms' },
  { label: 'Mission duration', value: '+72%' },
];

export default function HeroSentinel() {
  const scrollTo = (href: string) => document.querySelector(href)?.scrollIntoView({ behavior: 'smooth' });

  return (
    <section id="hero" className="relative min-h-screen overflow-hidden pt-24">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(34,211,238,.18),transparent_32rem),radial-gradient(circle_at_80%_20%,rgba(168,85,247,.14),transparent_30rem),linear-gradient(180deg,rgba(2,6,23,.15),#020617_92%)]" />
      <div className="perspective-road pointer-events-none absolute inset-x-0 bottom-0 h-[55vh] opacity-70">
        <div className="road-plane absolute inset-x-[-10%] bottom-[-25%] h-[120%] animate-roadFlow" />
      </div>

      <div className="section-shell grid min-h-[calc(100vh-6rem)] items-center gap-10 lg:grid-cols-[1.05fr_.95fr]">
        <motion.div initial={{ opacity: 0, y: 34 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
          <div className="eyebrow"><Radio size={14} /> AI for Egypt Real Problems · System active</div>
          <h1 className="max-w-5xl text-6xl font-black leading-[.9] tracking-[-0.075em] text-white sm:text-7xl lg:text-8xl">
            AeroMind <span className="bg-gradient-to-r from-cyan-200 via-blue-300 to-emerald-300 bg-clip-text text-transparent">Sentinel</span>
          </h1>
          <p className="mt-6 max-w-3xl text-2xl font-semibold text-cyan-100/95">AI-Powered Smart Highway Monitoring & Emergency Response System</p>
          <p className="section-copy text-xl">Autonomous drone intelligence for detecting highway accidents, congestion, stopped vehicles, pedestrians, blocked lanes, and emergency risk zones in real time.</p>
          <div className="mt-9 flex flex-wrap gap-4">
            <button className="btn-primary" onClick={() => scrollTo('#simulation')}><Play size={18} fill="currentColor" /> Watch Live Simulation</button>
            <button className="btn-secondary" onClick={() => scrollTo('#business')}><Activity size={18} /> View Business Model</button>
            <button className="btn-secondary" onClick={() => window.open('/report', '_blank')}><FileText size={18} /> View Technical Report</button>
          </div>
          <div className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {heroMetrics.map((metric) => (
              <motion.div key={metric.label} whileHover={{ y: -4 }} className="rounded-2xl border border-white/10 bg-white/[.055] p-4 backdrop-blur-xl">
                <div className="font-mono text-2xl font-black text-white">{metric.value}</div>
                <div className="mt-1 text-xs font-bold uppercase tracking-[0.14em] text-slate-400">{metric.label}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, x: 44 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.9, delay: 0.2 }} className="glass-panel relative min-h-[540px] overflow-hidden p-5 scanline">
          <div className="absolute left-1/2 top-1/2 h-72 w-72 -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-300/30" />
          <div className="radar-ring left-[18%] top-[16%] h-32 w-32" />
          <div className="radar-ring bottom-[18%] right-[18%] h-44 w-44" />
          <div className="relative z-10 grid h-full content-between gap-5">
            <div className="flex items-center justify-between">
              <span className="status-chip border-emerald-300/30 bg-emerald-300/10 text-emerald-200"><span className="h-2 w-2 animate-pulse rounded-full bg-emerald-300" /> Mission online</span>
              <span className="font-mono text-xs text-slate-400">EG-HWY-07</span>
            </div>
            <div className="mx-auto grid h-64 w-64 place-items-center rounded-full border border-cyan-300/30 bg-cyan-300/5 shadow-glow">
              <div className="grid h-36 w-36 place-items-center rounded-full border border-emerald-300/40 bg-slate-950/70">
                <Satellite className="animate-float text-cyan-200" size={54} />
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <HudCard icon={<Battery />} label="Drone battery" value="92%" tone="green" />
              <HudCard icon={<Route />} label="Risk corridor" value="18.4 km" tone="cyan" />
              <HudCard icon={<ShieldAlert />} label="Active alerts" value="03" tone="red" />
              <HudCard icon={<Radio />} label="Encrypted link" value="45 ms" tone="cyan" />
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function HudCard({ icon, label, value, tone }: { icon: ReactNode; label: string; value: string; tone: 'green' | 'cyan' | 'red' }) {
  const color = tone === 'green' ? 'text-emerald-300' : tone === 'red' ? 'text-red-300' : 'text-cyan-200';
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-4 backdrop-blur-xl">
      <div className={`${color} mb-3`}>{icon}</div>
      <div className="hud-label">{label}</div>
      <div className="mt-1 text-2xl font-black text-white">{value}</div>
    </div>
  );
}
