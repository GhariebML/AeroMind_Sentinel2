import { motion } from 'framer-motion';
import { BrainCircuit, Camera, MonitorDot, Navigation, ShieldAlert, Target, ChevronRight } from 'lucide-react';
import { Card } from './ui/Card';
import { SectionHeader } from './ui/SectionHeader';

const steps = [
  ['Drone Camera & Telemetry', 'Aerial highway feed, GPS, altitude, speed, and battery state.', Camera],
  ['YOLOv8 + SAHI Detection', 'Small object detection for vehicles, pedestrians, hazards, and blocked lanes.', BrainCircuit],
  ['BoT-SORT + OSNet Tracking', 'Persistent track IDs, speeds, lane movement, and identity stability.', Target],
  ['Highway Risk Analysis', 'Event scoring, severity classification, and emergency recommendations.', ShieldAlert],
  ['Energy-Aware Navigation', 'Drone moves toward risk zones while minimizing battery consumption.', Navigation],
  ['Emergency Dashboard', 'Control room UI for alerts, KPIs, telemetry, and response actions.', MonitorDot],
] as const;

export default function HighwayPipeline() {
  return (
    <section id="pipeline" className="relative z-10 mx-auto w-full max-w-7xl px-4 py-32 sm:px-6 lg:px-8">
      <SectionHeader
        eyebrow="The Pipeline"
        title="A continuous AI loop from drone vision to emergency action."
        description="The product preserves AeroMind AI's technical core and adds a highway-specific risk and response layer."
      />

      <div className="relative mt-20 overflow-hidden rounded-[2.5rem] border border-white/5 bg-slate-900/30 p-8 md:p-12 backdrop-blur-3xl shadow-2xl">
        <div className="absolute left-0 top-1/2 h-px w-full -translate-y-1/2 bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent shadow-[0_0_15px_rgba(34,211,238,0.2)] hidden lg:block" />
        
        <motion.div initial="hidden" whileInView="show" viewport={{ once: true, margin: '-50px' }} transition={{ staggerChildren: 0.1 }} className="relative grid gap-6 md:grid-cols-2 lg:grid-cols-6 items-start">
          {steps.map(([title, copy, Icon], index) => (
            <motion.div key={title} variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } }} className="relative group h-full">
              {index < steps.length - 1 && (
                <div className="hidden lg:flex absolute top-1/2 -right-4 -translate-y-1/2 z-20 text-cyan-500/50">
                  <ChevronRight size={24} />
                </div>
              )}
              <Card hoverEffect className="h-full p-7 relative bg-slate-950/80 border-white/5 flex flex-col hover:-translate-y-2 transition-transform duration-300">
                <div className="absolute inset-0 bg-gradient-to-b from-cyan-400/0 to-cyan-400/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-[inherit] pointer-events-none" />
                
                <div className="mb-8 flex items-center justify-between">
                  <span className="font-mono text-xl font-black text-white/20 group-hover:text-cyan-400/40 transition-colors">0{index + 1}</span>
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-400/10 text-cyan-400 border border-cyan-400/20 shadow-[0_0_15px_rgba(34,211,238,0.1)] group-hover:bg-cyan-400/20 group-hover:shadow-[0_0_20px_rgba(34,211,238,0.3)] transition-all">
                    <Icon size={20} />
                  </div>
                </div>
                
                <h3 className="text-[15px] font-bold text-white mb-3 leading-snug">{title}</h3>
                <p className="text-[13px] leading-[1.85] text-slate-400 mt-auto">{copy}</p>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
