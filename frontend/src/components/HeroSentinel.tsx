import { motion, useScroll, useTransform } from 'framer-motion';
import { Activity, Battery, Play, Radio, Satellite, ShieldAlert, Crosshair, AlertTriangle, Zap, FileText } from 'lucide-react';
import { useRef } from 'react';
import { Button } from './ui/Button';
import logo from '../assets/logo.png';

type MetricItem = { label: string; value: string; icon?: undefined };
type CapItem = { label: string; icon: React.ReactNode; value?: undefined };
type TickerItem = MetricItem | CapItem;

const proofMetrics: MetricItem[] = [
  { label: 'MOTA', value: '83.2%' },
  { label: 'IDF1', value: '78.5%' },
  { label: 'Energy Saved', value: '34.8%' },
  { label: 'Mission Duration', value: '+72%' },
];

const capabilities: CapItem[] = [
  { label: 'Accident Detection', icon: <AlertTriangle size={12} /> },
  { label: 'Risk Scoring', icon: <Crosshair size={12} /> },
  { label: 'Emergency Alerts', icon: <ShieldAlert size={12} /> },
  { label: 'Energy-Aware Nav', icon: <Zap size={12} /> },
];

const tickerItems: TickerItem[] = [...proofMetrics, ...capabilities, ...proofMetrics, ...capabilities];

export default function HeroSentinel() {
  const containerRef = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end start"]
  });

  const y1 = useTransform(scrollYProgress, [0, 1], [0, 200]);
  const y2 = useTransform(scrollYProgress, [0, 1], [0, -100]);
  const opacity = useTransform(scrollYProgress, [0, 0.8], [1, 0]);

  const scrollTo = (href: string) => document.querySelector(href)?.scrollIntoView({ behavior: 'smooth' });

  return (
    <section ref={containerRef} id="hero" className="relative min-h-[100dvh] overflow-hidden flex flex-col bg-[#020617]">
      {/* Dynamic Immersive Background */}
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_30%_50%,rgba(34,211,238,0.07),transparent_60%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_20%,rgba(16,185,129,0.06),transparent_40rem)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_80%,rgba(99,102,241,0.04),transparent_30rem)]" />
        <div className="perspective-road pointer-events-none absolute inset-x-0 bottom-0 h-[55vh] opacity-50">
          <div className="road-plane absolute inset-x-[-20%] bottom-[-50%] h-[150%] animate-roadFlow" />
        </div>
        {/* Subtle grid overlay */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:80px_80px]" />
      </div>

      <div className="section-shell relative z-10 grid lg:grid-cols-[1.1fr_.9fr] items-center flex-grow w-full pt-28 pb-24 md:pt-36 md:pb-32 gap-16 lg:gap-12">
        
        {/* LEFT COLUMN: Premium Brand Block */}
        <motion.div style={{ y: y2, opacity }} className="flex flex-col relative z-20">

          {/* ── Brand Lockup: Logo + Name ── */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
            className="flex items-center gap-4 mb-10"
          >
            {/* Live status badge */}
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/[0.07] px-4 py-2 backdrop-blur-md shadow-[0_0_16px_rgba(34,211,238,0.12)]">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex h-2 w-2 rounded-full bg-cyan-400"></span>
              </span>
              <Radio size={11} className="text-cyan-400" />
              <span className="text-[10px] font-black uppercase tracking-[0.18em] text-cyan-300">System Active · Edge Node 04</span>
            </div>

            <div className="h-4 w-px bg-white/10" />

            <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">AI Highway Intelligence</span>
          </motion.div>

          {/* ── Main Headline ── */}
          <h1 className="text-5xl md:text-6xl lg:text-[5rem] xl:text-[5.5rem] font-black leading-[1.04] tracking-tight text-white mb-6">
            <motion.span
              initial={{ opacity: 0, filter: "blur(12px)", y: 24 }}
              animate={{ opacity: 1, filter: "blur(0px)", y: 0 }}
              transition={{ duration: 0.9, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
              className="block"
            >
              Autonomous
            </motion.span>
            <motion.span
              initial={{ opacity: 0, filter: "blur(12px)", y: 24 }}
              animate={{ opacity: 1, filter: "blur(0px)", y: 0 }}
              transition={{ duration: 0.9, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
              className="block bg-gradient-to-r from-cyan-400 via-emerald-300 to-cyan-300 bg-clip-text text-transparent bg-[length:200%_auto] animate-shimmer"
            >
              Drone AI
            </motion.span>
            <motion.span
              initial={{ opacity: 0, filter: "blur(12px)", y: 24 }}
              animate={{ opacity: 1, filter: "blur(0px)", y: 0 }}
              transition={{ duration: 0.9, delay: 0.45, ease: [0.16, 1, 0.3, 1] }}
              className="block text-slate-300"
            >
              for Highways
            </motion.span>
          </h1>

          {/* ── Sub-headline ── */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.55 }}
            className="text-[15px] md:text-base leading-[1.85] text-slate-400 max-w-lg mb-10"
          >
            Real-time highway incident detection, risk scoring, and emergency response routing — powered by autonomous aerial surveillance and edge AI.
          </motion.p>

          {/* ── CTAs ── */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.65 }}
            className="flex flex-col sm:flex-row items-start sm:items-center gap-4 relative z-30"
          >
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500 to-emerald-500 rounded-full blur opacity-30 group-hover:opacity-60 transition duration-500" />
              <Button variant="primary" size="lg" onClick={() => scrollTo('#simulation')} className="relative w-full sm:w-auto bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-black shadow-[0_0_20px_rgba(34,211,238,0.3)]">
                <Play size={17} fill="currentColor" className="mr-2" /> Watch Live Demo
              </Button>
            </div>
            <Button variant="outline" size="lg" onClick={() => scrollTo('#business')} className="w-full sm:w-auto border-white/10 hover:bg-white/5 bg-slate-950/50 backdrop-blur-md">
              <Activity size={17} className="mr-2" /> Business Model
            </Button>
            <a href="/pitch" target="_blank" className="text-[12px] font-bold uppercase tracking-[0.15em] text-slate-500 hover:text-cyan-400 flex items-center gap-2 transition-colors">
              <FileText size={14} /> Pitch PDF
            </a>
          </motion.div>

          {/* ── Proof Stats Row ── */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.8 }}
            className="mt-12 flex items-center gap-6 flex-wrap"
          >
            {proofMetrics.map((m) => (
              <div key={m.label} className="flex flex-col">
                <span className="font-mono text-lg font-black text-white leading-none">{m.value}</span>
                <span className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500 mt-0.5">{m.label}</span>
              </div>
            ))}
          </motion.div>
        </motion.div>

        {/* RIGHT COLUMN: Holographic HUD */}
        <motion.div style={{ y: y1 }} className="relative h-[500px] md:h-[600px] w-full max-w-lg mx-auto lg:ml-auto lg:mr-0 z-10 mt-12 lg:mt-0 perspective-[1000px]">
          
          {/* Main Radar Panel */}
          <motion.div 
            initial={{ opacity: 0, rotateX: 10, rotateY: -10, z: -100 }} 
            animate={{ opacity: 1, rotateX: 0, rotateY: 0, z: 0 }} 
            transition={{ duration: 1.2, ease: "easeOut", delay: 0.2 }}
            className="absolute inset-0 rounded-[2rem] border border-cyan-500/20 bg-slate-900/40 p-6 backdrop-blur-xl shadow-[0_0_60px_rgba(2,6,23,0.9),inset_0_1px_0_rgba(255,255,255,0.05)] overflow-hidden"
          >
            {/* Grid & Scanning effect */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:40px_40px] opacity-20" />
            <div className="absolute top-0 left-0 right-0 h-32 bg-gradient-to-b from-cyan-500/10 to-transparent animate-scan" />
            
            <div className="relative z-10 flex items-center justify-between pb-4 border-b border-white/10">
              <div className="inline-flex items-center gap-1.5 rounded bg-emerald-500/10 px-2 py-1 border border-emerald-500/20">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" /> 
                <span className="font-mono text-[9px] font-black tracking-widest text-emerald-400 uppercase">Live Feed</span>
              </div>
              <div className="font-mono text-[9px] font-black tracking-widest text-cyan-500/50">ALT: 120M | SPD: 24M/S</div>
            </div>

            <div className="relative h-full flex items-center justify-center">
              <div className="absolute left-1/2 top-1/2 h-80 w-80 -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-500/10" />
              <div className="absolute left-1/2 top-1/2 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-500/20 border-dashed animate-spin-slow" style={{ animationDuration: '40s' }} />
              
              <div className="relative grid h-32 w-32 place-items-center rounded-full border border-cyan-400/30 bg-cyan-400/5 shadow-[0_0_40px_rgba(34,211,238,0.2)]">
                <div className="absolute inset-0 rounded-full border border-cyan-300/20 animate-ping" style={{ animationDuration: '3s' }} />
                <div className="grid h-20 w-20 place-items-center rounded-full border border-emerald-400/40 bg-slate-950 shadow-inner">
                  <Satellite className="animate-float text-cyan-400 drop-shadow-[0_0_15px_rgba(34,211,238,0.8)]" size={32} />
                </div>
              </div>
            </div>
          </motion.div>

          {/* Floating HUD Element 1: Battery & Status */}
          <motion.div 
            initial={{ opacity: 0, x: 50, y: 20 }} 
            animate={{ opacity: 1, x: 0, y: [0, -8, 0] }} 
            transition={{ duration: 1, delay: 0.8, y: { duration: 4, repeat: Infinity, ease: "easeInOut" } }}
            className="absolute -right-8 top-16 rounded-xl border border-white/10 bg-slate-950/90 p-4 backdrop-blur-2xl shadow-[0_8px_32px_rgba(0,0,0,0.5)] w-48"
          >
            <div className="flex items-center gap-2 text-emerald-400 mb-1">
              <Battery size={14} />
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Power Level</span>
            </div>
            <div className="text-2xl font-black text-white">92%</div>
            <div className="mt-2 h-1 w-full bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 w-[92%]" />
            </div>
          </motion.div>

          {/* Floating HUD Element 2: Alerts */}
          <motion.div 
            initial={{ opacity: 0, x: -50, y: 20 }} 
            animate={{ opacity: 1, x: 0, y: [0, -10, 0] }} 
            transition={{ duration: 1, delay: 1, y: { duration: 5, repeat: Infinity, ease: "easeInOut" } }}
            className="absolute -left-12 bottom-24 rounded-xl border border-red-500/20 bg-slate-950/90 p-4 backdrop-blur-2xl shadow-[0_0_30px_rgba(239,68,68,0.1)] w-56"
          >
            <div className="flex items-start gap-3">
              <div className="rounded bg-red-500/10 p-1.5 border border-red-500/20 mt-0.5 flex-shrink-0">
                <ShieldAlert size={14} className="text-red-400" />
              </div>
              <div>
                <div className="text-[10px] font-black uppercase tracking-widest text-red-400 mb-0.5">Critical Alert</div>
                <div className="text-sm font-bold text-white leading-tight">Debris detected on Lane 2</div>
                <div className="text-[9px] font-mono text-slate-400 mt-1">CONF: 94% | RISK: HIGH</div>
              </div>
            </div>
          </motion.div>

          {/* Floating HUD Element 3: Latency */}
          <motion.div 
            initial={{ opacity: 0, y: 50 }} 
            animate={{ opacity: 1, y: [0, -6, 0] }} 
            transition={{ duration: 1, delay: 1.2, y: { duration: 3, repeat: Infinity, ease: "easeInOut" } }}
            className="absolute -right-4 bottom-8 rounded-xl border border-cyan-500/20 bg-slate-950/90 p-3 backdrop-blur-2xl shadow-xl flex items-center gap-3"
          >
            <Satellite size={16} className="text-cyan-400" />
            <div>
              <div className="text-[9px] font-black uppercase tracking-widest text-slate-400">Stream Latency</div>
              <div className="text-base font-black text-white">45<span className="text-xs text-cyan-400 ml-0.5">ms</span></div>
            </div>
          </motion.div>

        </motion.div>
      </div>

      {/* BOTTOM TICKER TAPE */}
      <div className="absolute bottom-0 left-0 right-0 h-14 border-t border-white/5 bg-slate-950/60 backdrop-blur-md overflow-hidden flex items-center z-30">
        <div className="absolute left-0 top-0 bottom-0 w-24 bg-gradient-to-r from-[#020617] to-transparent z-10" />
        <div className="absolute right-0 top-0 bottom-0 w-24 bg-gradient-to-l from-[#020617] to-transparent z-10" />
        
        <motion.div 
          animate={{ x: [0, -1920] }} 
          transition={{ repeat: Infinity, ease: "linear", duration: 40 }}
          className="flex items-center gap-12 whitespace-nowrap px-12"
        >
          {tickerItems.map((item, i) => (
            <div key={`${item.label}-${i}`} className="flex items-center gap-3">
              {item.value ? (
                <>
                  <span className="text-[11px] font-black uppercase tracking-widest text-slate-500">{item.label}</span>
                  <span className="font-mono text-sm font-bold text-cyan-300">{item.value}</span>
                </>
              ) : (
                <>
                  <span className="text-emerald-400">{item.icon}</span>
                  <span className="text-xs font-bold tracking-wide text-slate-300">{item.label}</span>
                </>
              )}
              <span className="mx-6 h-1 w-1 rounded-full bg-white/10" />
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
