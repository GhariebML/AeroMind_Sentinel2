import { motion } from 'framer-motion';
import { CheckCircle2, CircleDot, Flag, ShieldCheck, Sparkles } from 'lucide-react';
import { Card } from './ui/Card';
import { SectionHeader } from './ui/SectionHeader';

const readiness = [
  ['Functional Prototype', 'Premium React interface combined with interactive, live-feeling highway simulation.'],
  ['Existing AI Pipeline', 'YOLOv8 + SAHI, BoT-SORT + OSNet, and PPO navigation foundation.'],
  ['Clear Business Model', 'Defined B2G/B2B SaaS, Drone-as-a-Service, and risk engine licensing models.'],
  ['Pitch-Ready Narrative', 'Problem, solution, demo, KPIs, and Egypt impact are cleanly structured.'],
];

const roadmap = [
  ['Real Highway Video Assets', 'Integrate licensed highway drone/video footage for stronger realism.'],
  ['Live Model Output Integration', 'Connect the React simulation to live Python inference events.'],
  ['Pitch Deck Visuals', 'Extract product screenshots, architecture graphics, and KPI visuals.'],
  ['Deployment Verification', 'Ensure Vercel deployment performance, responsive checks, and caching.'],
  ['Pilot Readiness', 'Validate system requirements for a small-scale real-world test corridor.'],
];

export function EgyptImpact() {
  return (
    <section id="impact" className="relative z-10 mx-auto w-full max-w-7xl px-4 py-32 sm:px-6 lg:px-8">
      <div className="grid items-center gap-12 lg:grid-cols-[.9fr_1.1fr]">
        <div>
          <div className="inline-flex items-center gap-2.5 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-4 py-2 mb-8 shadow-[0_0_20px_rgba(34,211,238,0.15)]">
            <Flag size={14} className="text-cyan-400" />
            <span className="text-[11px] font-black uppercase tracking-[0.2em] text-cyan-400">Egypt Impact</span>
          </div>
          <h2 className="text-4xl font-black tracking-tight text-white sm:text-5xl lg:text-6xl mb-6 leading-[1.1]">
            Aerial monitoring becomes intelligent emergency response.
          </h2>
          <p className="text-lg leading-relaxed text-slate-300">
            AeroMind Sentinel supports <span className="font-bold text-white">AI for Egypt Real Problems</span> by improving road safety, public safety, emergency response, smart transportation, and sustainable infrastructure.
          </p>
        </div>
        
        <motion.div initial={{ opacity: 0, scale: 0.96 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }} className="rounded-[2.5rem] border border-emerald-500/20 bg-slate-900/80 p-10 md:p-14 text-center shadow-[0_0_50px_rgba(16,185,129,0.15)] backdrop-blur-3xl relative overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(16,185,129,0.1),transparent_70%)] pointer-events-none" />
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-400/50 to-transparent"></div>
          
          <Sparkles className="mx-auto text-emerald-400 mb-8 drop-shadow-[0_0_15px_rgba(52,211,153,0.5)]" size={56} />
          <h3 className="relative text-2xl font-black tracking-tight text-white sm:text-3xl leading-snug">
            AeroMind Sentinel turns aerial monitoring into intelligent emergency response for safer Egyptian highways.
          </h3>
          <p className="relative mt-6 text-[15px] font-medium leading-relaxed text-slate-300">
            Aligned with Egypt Vision 2030, the platform extends monitoring coverage beyond fixed cameras and helps emergency teams act with live, AI-generated context.
          </p>
        </motion.div>
      </div>

      <div className="mt-20 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {['AI for Egypt Real Problems', 'Smart Transportation', 'Public Safety', 'Sustainable Infrastructure'].map((item, i) => (
          <motion.div key={item} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}>
            <Card hoverEffect className="text-center py-8 px-6 bg-slate-900/40 border-white/5 h-full">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 mb-5 shadow-[0_0_15px_rgba(34,211,238,0.1)]">
                <ShieldCheck size={28} />
              </div>
              <div className="text-[15px] font-bold text-white leading-tight">{item}</div>
            </Card>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

export function HackathonReadiness() {
  return (
    <section id="readiness" className="relative z-10 mx-auto w-full max-w-7xl px-4 py-32 sm:px-6 lg:px-8">
      <SectionHeader
        eyebrow="Hackathon Readiness"
        title="Built to impress judges in the first 10 seconds."
        description="The product story connects a real Egyptian problem, working simulation, AI depth, business readiness, and a credible pilot roadmap."
      />
      <div className="mt-20 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {readiness.map(([title, copy], i) => (
          <motion.div key={title} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }} className="h-full">
            <Card hoverEffect className="h-full p-6 bg-slate-900/60 border-emerald-500/10 hover:border-emerald-500/30">
              <div className="flex items-center justify-between mb-4">
                <div className="rounded-full bg-emerald-500/10 p-2 border border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.15)]">
                  <CheckCircle2 className="text-emerald-400" size={20} />
                </div>
                <div className="font-mono text-[10px] font-black tracking-widest text-emerald-500/50">READY</div>
              </div>
              <h3 className="text-base font-bold text-white mb-2 tracking-tight">{title}</h3>
              <p className="text-[13px] leading-relaxed text-slate-400">{copy}</p>
            </Card>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

export function RoadmapTodo() {
  return (
    <section id="roadmap" className="relative z-10 mx-auto w-full max-w-7xl px-4 py-32 sm:px-6 lg:px-8">
      <SectionHeader
        eyebrow="Development Roadmap"
        title="Planned milestones toward pilot deployment."
        description="These are framed as product development milestones, not weaknesses — the prototype is ready for demo, and the next steps move it toward field validation."
      />
      <div className="relative mx-auto mt-24 max-w-4xl">
        <div className="absolute left-6 top-0 bottom-0 w-px bg-gradient-to-b from-cyan-500/50 via-emerald-500/50 to-transparent md:left-1/2" />
        <div className="grid gap-12">
          {roadmap.map(([title, copy], index) => (
            <motion.div key={title} initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: index * 0.1 }} className={`relative grid gap-8 md:grid-cols-2 ${index % 2 ? 'md:[&>div]:col-start-2' : ''}`}>
              <div className="absolute left-6 top-6 z-10 -translate-x-1/2 md:left-1/2 flex h-8 w-8 items-center justify-center rounded-full border-[3px] border-slate-950 bg-cyan-400 text-slate-950 shadow-[0_0_15px_rgba(34,211,238,0.5)]">
                <CircleDot size={14} className="text-slate-950" />
              </div>
              <div className={`ml-16 md:ml-0 group ${index % 2 ? 'md:-ml-12' : 'md:-mr-12'}`}>
                <Card className="relative p-6 transition-all duration-300 hover:-translate-y-1 hover:border-cyan-400/40 hover:shadow-[0_0_30px_rgba(34,211,238,0.15)] bg-slate-900/60 border-white/5">
                  <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 font-mono text-[10px] font-black tracking-widest text-emerald-400 shadow-inner">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
                    MILESTONE 0{index + 1}
                  </div>
                  <h3 className="text-lg font-black text-white mb-2 tracking-tight group-hover:text-cyan-300 transition-colors">{title}</h3>
                  <p className="text-sm leading-relaxed text-slate-400">{copy}</p>
                </Card>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
