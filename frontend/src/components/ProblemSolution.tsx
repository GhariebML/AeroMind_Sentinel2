import { motion } from 'framer-motion';
import { Activity, AlertCircle, AlertTriangle, CameraOff, Clock, Crosshair, ScanEye, ShieldAlert, TrendingUp, Zap } from 'lucide-react';
import { Card } from './ui/Card';
import { SectionHeader } from './ui/SectionHeader';

const problems = [
  ['Highway Accidents', 'Fast-moving incidents escalate into multi-vehicle emergencies rapidly.', AlertTriangle],
  ['Delayed Detection', 'Reliance on calls and fixed cameras creates avoidable reporting delays.', Clock],
  ['Sudden Congestion', 'Blocked lanes create dangerous congestion waves upstream.', Activity],
  ['Limited Coverage', 'Static cameras leave blind spots across desert roads and work zones.', CameraOff],
  ['Slow Response', 'Dispatchers lack exact lane, severity, and access corridor context.', AlertCircle],
  ['Long Segments', 'Expanding networks need mobile, scalable monitoring toward risk.', TrendingUp],
] as const;

const solutions = [
  ['Autonomous Drone Patrols', 'Drones patrol high-risk segments and dynamically reposition to incidents.', ScanEye],
  ['Real-Time AI Vision', 'YOLOv8 + SAHI detects vehicles, pedestrians, and hazards from the air.', Crosshair],
  ['Multi-Object Tracking', 'BoT-SORT + OSNet tracks speeds, stoppages, and incident evolution.', Activity],
  ['Risk Scoring Engine', 'Transforms raw events into severity, action, and response priority.', ShieldAlert],
  ['Emergency Dashboard', 'Surfaces critical alerts with confidence, lane, and speed metrics.', AlertTriangle],
  ['Energy-Aware Navigation', 'PPO RL moves toward risk zones while preserving battery life.', Zap],
] as const;

export function ProblemEgypt() {
  return (
    <section id="problem" className="relative z-10 mx-auto w-full max-w-7xl px-4 py-32 sm:px-6 lg:px-8">
      <SectionHeader 
        eyebrow="The Problem" 
        title="Highway safety needs faster eyes, better context, and mobile coverage." 
        description="AeroMind Sentinel addresses a critical public safety challenge: detecting dangerous highway events early enough to support life-saving emergency response." 
      />
      
      <motion.div initial="hidden" whileInView="show" viewport={{ once: true, margin: '-50px' }} transition={{ staggerChildren: 0.08 }} className="mt-20 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {problems.map(([title, copy, Icon]) => (
          <motion.div key={title} variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } }}>
            <Card hoverEffect className="h-full group bg-slate-900/40 border-white/5">
              <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-red-500/10 text-red-400 transition-colors group-hover:bg-red-500/20 shadow-inner">
                <Icon size={24} />
              </div>
              <h3 className="text-[17px] font-bold text-white mb-3 leading-snug">{title}</h3>
              <p className="text-[14px] leading-[1.85] text-slate-400">{copy}</p>
            </Card>
          </motion.div>
        ))}
      </motion.div>
    </section>
  );
}

export function SentinelSolution() {
  return (
    <section id="solution" className="relative z-10 mx-auto w-full max-w-7xl px-4 py-32 sm:px-6 lg:px-8">
      <div className="rounded-[2.5rem] border border-cyan-500/10 bg-slate-900/40 p-10 md:p-16 backdrop-blur-2xl shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-full h-full bg-[radial-gradient(ellipse_at_top_right,rgba(34,211,238,0.05),transparent_50%)] pointer-events-none" />
        
        <div className="max-w-3xl mb-20 relative z-10">
          <span className="mb-5 inline-flex items-center gap-2 rounded-full border border-cyan-400/25 bg-cyan-400/8 px-4 py-2 font-mono text-[11px] font-black uppercase tracking-[0.22em] text-cyan-300">The Solution</span>
          <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight leading-[1.1] mb-5">Autonomous drone intelligence for highway command centers.</h2>
          <p className="text-[15px] leading-[1.85] text-slate-300">Sentinel converts aerial perception into emergency-ready decisions.</p>
        </div>

        <motion.div initial="hidden" whileInView="show" viewport={{ once: true, margin: '-50px' }} transition={{ staggerChildren: 0.08 }} className="grid gap-x-10 gap-y-12 md:grid-cols-2 lg:grid-cols-3 relative z-10">
          {solutions.map(([title, copy, Icon]) => (
            <motion.div key={title} variants={{ hidden: { opacity: 0, y: 15 }, show: { opacity: 1, y: 0 } }} className="flex flex-col gap-5">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-400/10 border border-cyan-400/20 text-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.1)]">
                <Icon size={24} />
              </div>
              <div>
                <h3 className="text-[17px] font-bold text-white mb-3 leading-snug">{title}</h3>
                <p className="text-[14px] leading-[1.85] text-slate-400">{copy}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>

        <div className="mt-20 pt-10 border-t border-white/10 relative z-10 text-center">
          <p className="text-lg md:text-xl font-bold text-cyan-50 leading-relaxed">Detect, track, score, alert, and navigate toward risk while conserving battery.</p>
        </div>
      </div>
    </section>
  );
}
