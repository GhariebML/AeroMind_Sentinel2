import { motion } from 'framer-motion';
import { BrainCircuit, Camera, MonitorDot, Navigation, ShieldAlert, Target } from 'lucide-react';

const steps = [
  ['Drone Camera + Telemetry', 'Aerial highway feed, GPS, altitude, speed, and battery state.', Camera],
  ['YOLOv8 + SAHI Detection', 'Small object detection for vehicles, pedestrians, hazards, and blocked lanes.', BrainCircuit],
  ['BoT-SORT + OSNet Tracking', 'Persistent track IDs, speeds, lane movement, and identity stability.', Target],
  ['Highway Risk Analysis Engine', 'Event scoring, severity classification, and emergency recommendations.', ShieldAlert],
  ['PPO Energy-Aware Navigation', 'Drone moves toward risk zones while minimizing battery consumption.', Navigation],
  ['Emergency Dashboard + Alerts', 'Control room UI for alerts, KPIs, telemetry, and response actions.', MonitorDot],
] as const;

export default function HighwayPipeline() {
  return (
    <section id="pipeline" className="section-shell">
      <div className="mx-auto max-w-4xl text-center">
        <span className="eyebrow">How it works</span>
        <h2 className="section-title mx-auto">A continuous AI loop from drone vision to emergency action.</h2>
        <p className="section-copy mx-auto">The product preserves AeroMind AI’s technical core and adds a highway-specific risk and response layer.</p>
      </div>

      <div className="relative mt-14 overflow-hidden rounded-[2rem] border border-white/10 bg-slate-950/55 p-5 backdrop-blur-xl">
        <div className="absolute left-0 top-1/2 h-1 w-full -translate-y-1/2 bg-gradient-to-r from-transparent via-cyan-300/60 to-transparent" />
        <motion.div initial="hidden" whileInView="show" viewport={{ once: true }} transition={{ staggerChildren: 0.12 }} className="relative grid gap-4 lg:grid-cols-6">
          {steps.map(([title, copy, Icon], index) => (
            <motion.article key={title} variants={{ hidden: { opacity: 0, y: 28 }, show: { opacity: 1, y: 0 } }} className="glass-card min-h-[230px] p-5">
              <div className="mb-5 flex items-center justify-between">
                <span className="font-mono text-xs font-black text-emerald-300">0{index + 1}</span>
                <span className="grid h-12 w-12 place-items-center rounded-2xl bg-cyan-300/10 text-cyan-200 shadow-glow"><Icon /></span>
              </div>
              <h3 className="text-lg font-black text-white">{title}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-400">{copy}</p>
            </motion.article>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
