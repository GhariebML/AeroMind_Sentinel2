import { motion } from 'framer-motion';
import { Activity, AlertCircle, AlertTriangle, CameraOff, Clock, Crosshair, ScanEye, ShieldAlert, TrendingUp, Zap } from 'lucide-react';

const problems = [
  ['Highway accidents', 'Fast-moving incidents can escalate into multi-vehicle emergencies before operators receive a reliable report.', AlertTriangle],
  ['Delayed incident detection', 'Emergency teams often depend on phone calls or fixed cameras, creating minutes of avoidable delay.', Clock],
  ['Sudden congestion', 'Blocked lanes and stopped vehicles create congestion waves that threaten drivers upstream.', Activity],
  ['Limited camera coverage', 'Static cameras leave blind spots across long desert roads, ring roads, and temporary work zones.', CameraOff],
  ['Slow emergency response', 'Without live overhead context, dispatchers lack exact lane, severity, and access corridor information.', AlertCircle],
  ['Long road segments', 'Egypt’s expanding highway network needs mobile, scalable monitoring that moves toward risk.', TrendingUp],
] as const;

const solutions = [
  ['Autonomous drone monitoring', 'Drones patrol high-risk segments and dynamically reposition to incidents instead of watching one fixed point.', ScanEye],
  ['Real-time AI detection', 'YOLOv8 + SAHI detects vehicles, pedestrians, stopped vehicles, hazards, and accident patterns from aerial video.', Crosshair],
  ['Multi-object tracking', 'BoT-SORT + OSNet maintains persistent IDs to understand speed, stoppage, lane changes, and incident evolution.', Activity],
  ['Highway risk scoring', 'The risk engine transforms events into explainable severity, recommended actions, and response priority.', ShieldAlert],
  ['Emergency alerts', 'The dashboard surfaces critical events with confidence, lane, speed, and operational recommendations.', AlertTriangle],
  ['Energy-aware navigation', 'PPO reinforcement learning moves toward high-risk zones while preserving battery and mission duration.', Zap],
] as const;

const cardVariants = { hidden: { opacity: 0, y: 24 }, show: { opacity: 1, y: 0 } };

export function ProblemEgypt() {
  return (
    <section id="problem" className="section-shell">
      <Header eyebrow="Problem in Egypt" title="Highway safety needs faster eyes, better context, and mobile coverage." copy="AeroMind Sentinel focuses on a real public safety challenge: detecting dangerous highway events early enough to support faster emergency response." />
      <motion.div initial="hidden" whileInView="show" viewport={{ once: true, margin: '-120px' }} transition={{ staggerChildren: 0.08 }} className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {problems.map(([title, copy, Icon]) => (
          <motion.article key={title} variants={cardVariants} className="glass-card group">
            <div className="mb-5 grid h-12 w-12 place-items-center rounded-2xl border border-red-300/25 bg-red-400/10 text-red-300 transition group-hover:shadow-redGlow"><Icon /></div>
            <h3 className="text-xl font-black text-white">{title}</h3>
            <p className="mt-3 leading-7 text-slate-400">{copy}</p>
          </motion.article>
        ))}
      </motion.div>
    </section>
  );
}

export function SentinelSolution() {
  return (
    <section id="solution" className="section-shell">
      <Header eyebrow="Proposed Solution" title="Autonomous drone intelligence for highway command centers." copy="Sentinel converts aerial perception into emergency-ready decisions: detect, track, score, alert, and navigate toward risk while conserving battery." />
      <motion.div initial="hidden" whileInView="show" viewport={{ once: true, margin: '-120px' }} transition={{ staggerChildren: 0.08 }} className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {solutions.map(([title, copy, Icon]) => (
          <motion.article key={title} variants={cardVariants} className="glass-card group">
            <div className="mb-5 grid h-12 w-12 place-items-center rounded-2xl border border-cyan-300/25 bg-cyan-300/10 text-cyan-200 transition group-hover:shadow-glow"><Icon /></div>
            <h3 className="text-xl font-black text-white">{title}</h3>
            <p className="mt-3 leading-7 text-slate-400">{copy}</p>
          </motion.article>
        ))}
      </motion.div>
    </section>
  );
}

function Header({ eyebrow, title, copy }: { eyebrow: string; title: string; copy: string }) {
  return (
    <div className="mx-auto max-w-4xl text-center">
      <span className="eyebrow">{eyebrow}</span>
      <h2 className="section-title mx-auto">{title}</h2>
      <p className="section-copy mx-auto">{copy}</p>
    </div>
  );
}
