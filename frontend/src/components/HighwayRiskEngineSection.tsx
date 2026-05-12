import { motion } from 'framer-motion';
import { AlertTriangle, Gauge, LocateFixed, Route, ScanLine, ShieldCheck, Signal, TrafficCone } from 'lucide-react';

const inputs = [
  ['Event type', AlertTriangle],
  ['Confidence', Signal],
  ['Speed', Gauge],
  ['Lane', Route],
  ['Traffic density', TrafficCone],
  ['Tracking stability', ScanLine],
  ['Distance to emergency zone', LocateFixed],
];

const outputs = ['Risk score', 'Severity', 'Emergency alert', 'Recommended action'];

export default function HighwayRiskEngineSection() {
  return (
    <section id="risk-engine" className="section-shell">
      <div className="grid items-center gap-10 lg:grid-cols-[.9fr_1.1fr]">
        <div>
          <span className="eyebrow">Highway Risk Engine</span>
          <h2 className="section-title">Explainable risk scoring for emergency response.</h2>
          <p className="section-copy">Sentinel turns raw detections into operational decisions by combining event type, confidence, speed, lane, density, tracking stability, and emergency proximity.</p>
        </div>
        <div className="glass-panel p-5">
          <div className="grid gap-4 md:grid-cols-[1fr_auto_1fr] md:items-center">
            <div className="grid gap-3">
              {inputs.map(([label, Icon], index) => (
                <motion.div key={label as string} initial={{ opacity: 0, x: -16 }} whileInView={{ opacity: 1, x: 0 }} transition={{ delay: index * 0.05 }} viewport={{ once: true }} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[.04] p-3">
                  <span className="text-cyan-200"><Icon /></span><span className="font-semibold text-slate-200">{label as string}</span>
                </motion.div>
              ))}
            </div>
            <div className="grid place-items-center py-6">
              <div className="grid h-32 w-32 place-items-center rounded-full border border-emerald-300/40 bg-emerald-300/10 shadow-greenGlow">
                <ShieldCheck className="text-emerald-200" size={44} />
              </div>
            </div>
            <div className="grid gap-3">
              {outputs.map((label, index) => (
                <motion.div key={label} initial={{ opacity: 0, x: 16 }} whileInView={{ opacity: 1, x: 0 }} transition={{ delay: index * 0.07 }} viewport={{ once: true }} className="rounded-2xl border border-emerald-300/20 bg-emerald-300/10 p-4">
                  <div className="font-mono text-xs font-black text-emerald-300">OUTPUT 0{index + 1}</div>
                  <div className="mt-1 text-lg font-black text-white">{label}</div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
