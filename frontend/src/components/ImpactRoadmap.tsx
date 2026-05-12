import { motion } from 'framer-motion';
import { CheckCircle2, CircleDot, Flag, Rocket, ShieldCheck, Sparkles } from 'lucide-react';

const readiness = [
  ['Functional prototype', 'Premium React interface and interactive highway simulation.'],
  ['Existing AI pipeline', 'YOLOv8 + SAHI, BoT-SORT + OSNet, PPO navigation, and AirSim foundation.'],
  ['Clear business model', 'B2G/B2B SaaS, Drone-as-a-Service, and risk engine licensing.'],
  ['Pitch-ready direction', 'Problem, solution, demo, KPIs, impact, and roadmap are judge-ready.'],
];

const roadmap = [
  ['Real Highway Video Assets', 'Integrate licensed highway drone/video footage for stronger realism.'],
  ['Live Model Output Integration', 'Connect the React simulation to live Python inference events.'],
  ['Pitch Deck Visuals', 'Use product screenshots, architecture graphics, and KPI visuals.'],
  ['Deployment Screenshots', 'Capture final Vercel screens for submission material.'],
  ['TypeScript Build Pipeline', 'Keep strict type checking and production build validation.'],
];

export function EgyptImpact() {
  return (
    <section id="impact" className="section-shell">
      <div className="grid items-center gap-8 lg:grid-cols-[.95fr_1.05fr]">
        <div>
          <span className="eyebrow"><Flag size={14} /> Egypt Impact</span>
          <h2 className="section-title">Aerial monitoring becomes intelligent emergency response.</h2>
          <p className="section-copy">AeroMind Sentinel supports AI for Egypt Real Problems by improving road safety, public safety, emergency response, smart transportation, and sustainable smart infrastructure.</p>
        </div>
        <motion.div initial={{ opacity: 0, scale: 0.96 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }} className="glass-panel p-8 text-center">
          <Sparkles className="mx-auto text-emerald-300" size={44} />
          <h3 className="mt-5 text-3xl font-black tracking-[-0.04em] text-white">AeroMind Sentinel turns aerial monitoring into intelligent emergency response for safer Egyptian highways.</h3>
          <p className="mt-5 leading-8 text-slate-300">Aligned with Egypt Vision 2030, the platform extends monitoring coverage beyond fixed cameras and helps emergency teams act with live, AI-generated context.</p>
        </motion.div>
      </div>

      <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {['AI for Egypt Real Problems', 'Smart transportation', 'Public safety', 'Sustainable infrastructure'].map((item) => <div key={item} className="glass-card"><ShieldCheck className="mb-4 text-cyan-200" /><div className="text-lg font-black text-white">{item}</div></div>)}
      </div>
    </section>
  );
}

export function HackathonReadiness() {
  return (
    <section id="readiness" className="section-shell">
      <div className="mx-auto max-w-4xl text-center">
        <span className="eyebrow"><Rocket size={14} /> Hackathon Readiness</span>
        <h2 className="section-title mx-auto">Built to impress judges in the first 10 seconds.</h2>
        <p className="section-copy mx-auto">The product story connects a real Egyptian problem, working simulation, AI depth, business readiness, and a credible pilot roadmap.</p>
      </div>
      <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-4">
        {readiness.map(([title, copy]) => <div key={title} className="glass-card"><CheckCircle2 className="mb-4 text-emerald-300" /><h3 className="text-xl font-black text-white">{title}</h3><p className="mt-3 text-sm leading-6 text-slate-400">{copy}</p></div>)}
      </div>
    </section>
  );
}

export function RoadmapTodo() {
  return (
    <section id="roadmap" className="section-shell">
      <div className="mx-auto max-w-4xl text-center">
        <span className="eyebrow">Development Roadmap & Next Steps</span>
        <h2 className="section-title mx-auto">Planned milestones toward pilot deployment.</h2>
        <p className="section-copy mx-auto">These are framed as product development milestones, not weaknesses — the prototype is ready for demo, and the next steps move it toward field validation.</p>
      </div>
      <div className="relative mx-auto mt-14 max-w-4xl">
        <div className="timeline-line absolute left-5 top-0 h-full w-1 rounded-full md:left-1/2" />
        <div className="grid gap-6">
          {roadmap.map(([title, copy], index) => (
            <motion.div key={title} initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className={`relative grid gap-4 md:grid-cols-2 ${index % 2 ? 'md:[&>article]:col-start-2' : ''}`}>
              <span className="absolute left-2 top-7 z-10 grid h-7 w-7 place-items-center rounded-full border border-cyan-300 bg-slate-950 text-cyan-200 md:left-1/2 md:-translate-x-1/2"><CircleDot size={15} /></span>
              <article className="glass-card ml-12 md:ml-0">
                <div className="font-mono text-xs font-black text-emerald-300">MILESTONE 0{index + 1}</div>
                <h3 className="mt-2 text-xl font-black text-white">{title}</h3>
                <p className="mt-2 leading-7 text-slate-400">{copy}</p>
              </article>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
