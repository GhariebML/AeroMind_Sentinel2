import { motion, useInView, useMotionValue, useSpring } from 'framer-motion';
import { useEffect, useRef, useState } from 'react';
import { businessModel } from '../data/businessModel';
import { coreMetrics, sentinelKpis } from '../data/sentinelMetrics';
import { Users, Target, Share2, Handshake, Wallet, Cpu, Activity, Network, Receipt } from 'lucide-react';
import { Card } from './ui/Card';
import { SectionHeader } from './ui/SectionHeader';

export function SentinelMetrics() {
  return (
    <section id="metrics" className="relative z-10 mx-auto w-full max-w-7xl px-4 py-32 sm:px-6 lg:px-8">
      <SectionHeader
        eyebrow="Metrics & KPIs"
        title="Technical depth plus highway impact indicators."
        description="The demo communicates both the proven AeroMind AI core and the Sentinel highway product layer."
      />
      
      <div className="mt-20 grid gap-14 lg:grid-cols-[1.2fr_.8fr]">
        <div>
          <h3 className="text-[11px] font-black uppercase tracking-[0.2em] text-cyan-400 mb-7 pl-3 border-l-2 border-cyan-400">Core AI Performance</h3>
          <div className="grid gap-5 sm:grid-cols-2">
            {coreMetrics.map((metric, index) => (
              <MetricCard key={metric.label} metric={metric} index={index} />
            ))}
          </div>
        </div>
        
        <div>
          <h3 className="text-[11px] font-black uppercase tracking-[0.2em] text-emerald-400 mb-7 pl-3 border-l-2 border-emerald-400">Sentinel Operational KPIs</h3>
          <div className="grid gap-4">
            {sentinelKpis.map((kpi, index) => (
              <motion.div key={kpi.label} initial={{ opacity: 0, x: 20 }} whileInView={{ opacity: 1, x: 0 }} transition={{ delay: index * 0.1 }} viewport={{ once: true }}>
                <Card className="p-6 bg-slate-900/60 border-white/5">
                  <div className="flex items-end justify-between mb-4">
                    <div className="font-bold text-white text-[15px] leading-snug">{kpi.label}</div>
                    <div className="font-mono text-emerald-300 font-bold text-sm">{kpi.value}</div>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-slate-950 shadow-inner">
                    <motion.div initial={{ width: 0 }} whileInView={{ width: `${kpi.score}%` }} viewport={{ once: true }} transition={{ duration: 1.5, ease: "easeOut" }} className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-emerald-400" />
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

const BMC_ICONS: Record<string, React.ElementType> = {
  'Customer Segments': Users,
  'Value Proposition': Target,
  'Channels': Share2,
  'Customer Relationships': Handshake,
  'Revenue Streams': Wallet,
  'Key Resources': Cpu,
  'Key Activities': Activity,
  'Key Partners': Network,
  'Cost Structure': Receipt,
};

export function BusinessModelCanvas() {
  return (
    <section id="business" className="relative z-10 mx-auto w-full max-w-7xl px-4 py-32 sm:px-6 lg:px-8">
      <SectionHeader
        eyebrow="Business Model Canvas"
        title="Startup-ready path for B2G and B2B deployment."
        description="Sentinel can be sold as SaaS monitoring, Drone-as-a-Service, or licensed AI risk intelligence."
      />
      
      <motion.div 
        initial="hidden" 
        whileInView="show" 
        viewport={{ once: true, margin: '-50px' }} 
        transition={{ staggerChildren: 0.05 }} 
        className="mt-20 grid gap-5 md:grid-cols-2 lg:grid-cols-3"
      >
        {businessModel.map((block) => {
          const Icon = BMC_ICONS[block.title] || Users;
          return (
            <motion.div key={block.title} variants={{ hidden: { opacity: 0, y: 15 }, show: { opacity: 1, y: 0 } }} className="h-full">
              <Card hoverEffect className="h-full flex flex-col p-7 bg-slate-900/40 border-white/5">
                <div className="flex items-center gap-3.5 border-b border-white/5 pb-5 mb-5">
                  <div className="rounded-xl bg-cyan-500/10 p-2.5 border border-cyan-500/20 shadow-[0_0_10px_rgba(34,211,238,0.1)] shrink-0">
                    <Icon className="text-cyan-400" size={18} />
                  </div>
                  <h3 className="text-[15px] font-black text-white tracking-tight leading-snug">{block.title}</h3>
                </div>
                <ul className="flex-grow space-y-3">
                  {block.items.map((item) => (
                    <li key={item} className="flex items-start gap-3 text-[13px] leading-[1.85] text-slate-300">
                      <span className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" /> 
                      {item}
                    </li>
                  ))}
                </ul>
              </Card>
            </motion.div>
          );
        })}
      </motion.div>
    </section>
  );
}

function MetricCard({ metric, index }: { metric: { label: string; value: number; suffix: string; prefix?: string; caption: string }; index: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  const motionValue = useMotionValue(0);
  const spring = useSpring(motionValue, { stiffness: 80, damping: 18 });
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (inView) motionValue.set(metric.value);
    return spring.on('change', (latest) => setDisplay(latest));
  }, [inView, metric.value, motionValue, spring]);

  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} viewport={{ once: true }}>
      <Card hoverEffect className="text-center p-7 bg-slate-900/60 border-white/5 h-full flex flex-col justify-center">
        <div className="text-4xl md:text-5xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-white via-cyan-100 to-cyan-300">
          {metric.prefix ?? ''}{display.toFixed(metric.value % 1 ? 1 : 0)}{metric.suffix}
        </div>
        <div className="mt-3 text-[15px] font-black text-white tracking-tight">{metric.label}</div>
        <p className="mt-2 text-[13px] text-slate-400 leading-[1.85]">{metric.caption}</p>
      </Card>
    </motion.div>
  );
}
