import { motion } from 'framer-motion';
import { AlertTriangle, Gauge, LocateFixed, Route, ScanLine, ShieldCheck, Signal, TrafficCone, ArrowRight } from 'lucide-react';
import { Card } from './ui/Card';
import { SectionHeader } from './ui/SectionHeader';

const inputs = [
  ['Event Type', AlertTriangle],
  ['Confidence', Signal],
  ['Speed', Gauge],
  ['Lane', Route],
  ['Traffic Density', TrafficCone],
  ['Tracking Stability', ScanLine],
  ['Emergency Proximity', LocateFixed],
];

const outputs = ['Risk Score', 'Severity Level', 'Emergency Alert', 'Recommended Action'];

export default function HighwayRiskEngineSection() {
  return (
    <section id="risk-engine" className="relative z-10 mx-auto w-full max-w-7xl px-4 py-32 sm:px-6 lg:px-8">
      <div className="grid items-center gap-16 lg:grid-cols-[.9fr_1.1fr]">
        <SectionHeader
          align="left"
          eyebrow="Highway Risk Engine"
          title="Explainable risk scoring for emergency response."
          description="Sentinel turns raw detections into operational decisions by combining event type, confidence, speed, lane, density, tracking stability, and emergency proximity."
        />
        <div className="rounded-[2.5rem] border border-cyan-500/10 bg-slate-900/40 p-8 md:p-12 backdrop-blur-3xl relative overflow-hidden shadow-[0_0_40px_rgba(2,6,23,0.8)]">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(16,185,129,0.05),transparent_70%)] pointer-events-none" />
          
          <div className="grid gap-6 md:grid-cols-[1fr_auto_1fr] md:items-center relative z-10">
            {/* Inputs Column */}
            <div className="flex flex-col gap-3 relative">
              <div className="mb-2 pl-2 border-l-2 border-cyan-500/30">
                <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-cyan-400">Raw Inputs</span>
              </div>
              {inputs.map(([label, Icon], index) => (
                <motion.div key={label as string} initial={{ opacity: 0, x: -16 }} whileInView={{ opacity: 1, x: 0 }} transition={{ delay: index * 0.05 }} viewport={{ once: true }}>
                  <Card hoverEffect className="flex items-center gap-4 py-2.5 px-4 rounded-xl border-white/5 bg-slate-950/80">
                    <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-cyan-400/10 text-cyan-400 shrink-0 shadow-inner"><Icon size={14} /></span>
                    <span className="text-[13px] font-bold text-slate-200">{label as string}</span>
                  </Card>
                </motion.div>
              ))}
            </div>

            {/* Center Engine Node */}
            <div className="hidden md:flex flex-col items-center justify-center py-6 px-4 relative">
              <div className="absolute top-1/2 -left-8 w-8 h-px bg-gradient-to-r from-transparent to-cyan-400/50"></div>
              <div className="absolute top-1/2 -right-8 w-8 h-px bg-gradient-to-l from-transparent to-emerald-400/50"></div>
              <motion.div initial={{ scale: 0.8, opacity: 0 }} whileInView={{ scale: 1, opacity: 1 }} transition={{ delay: 0.3 }} viewport={{ once: true }}>
                <div className="grid h-28 w-28 place-items-center rounded-full border border-emerald-400/30 bg-emerald-400/10 shadow-[0_0_40px_rgba(16,185,129,0.2)] relative z-10 before:absolute before:-inset-2 before:rounded-full before:border before:border-emerald-400/10 before:animate-[spin_6s_linear_infinite]">
                  <ShieldCheck className="text-emerald-400" size={40} />
                </div>
              </motion.div>
            </div>

            <div className="md:hidden flex justify-center py-4 text-emerald-400/50">
              <ArrowRight size={24} className="animate-pulse" />
            </div>

            {/* Outputs Column */}
            <div className="flex flex-col gap-4 relative">
              <div className="mb-1 pl-2 border-l-2 border-emerald-500/30">
                <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-emerald-400">Decisions</span>
              </div>
              {outputs.map((label, index) => (
                <motion.div key={label} initial={{ opacity: 0, x: 16 }} whileInView={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 + index * 0.07 }} viewport={{ once: true }}>
                  <Card hoverEffect className="rounded-xl border-emerald-400/20 bg-emerald-950/40 p-5 shadow-inner relative overflow-hidden group">
                    <div className="absolute top-0 right-0 w-16 h-16 bg-gradient-to-br from-emerald-500/10 to-transparent rounded-bl-full opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <div className="font-mono text-[10px] font-black uppercase tracking-widest text-emerald-500 mb-2">OUTPUT 0{index + 1}</div>
                    <div className="text-[15px] font-bold text-white tracking-tight">{label}</div>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
