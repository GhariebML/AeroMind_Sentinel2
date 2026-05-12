import { motion, useInView, useMotionValue, useSpring } from 'framer-motion';
import { useEffect, useRef, useState } from 'react';
import { businessModel } from '../data/businessModel';
import { coreMetrics, sentinelKpis } from '../data/sentinelMetrics';

export function SentinelMetrics() {
  return (
    <section id="metrics" className="section-shell">
      <div className="mx-auto max-w-4xl text-center">
        <span className="eyebrow">Metrics & KPIs</span>
        <h2 className="section-title mx-auto">Technical depth plus highway impact indicators.</h2>
        <p className="section-copy mx-auto">The demo communicates both the proven AeroMind AI core and the Sentinel highway product layer.</p>
      </div>
      <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {coreMetrics.map((metric, index) => (
          <MetricCard key={metric.label} metric={metric} index={index} />
        ))}
      </div>
      <div className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {sentinelKpis.map((kpi) => (
          <div key={kpi.label} className="glass-card">
            <div className="flex items-center justify-between"><div className="font-bold text-white">{kpi.label}</div><div className="font-mono text-cyan-200">{kpi.value}</div></div>
            <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10"><motion.div initial={{ width: 0 }} whileInView={{ width: `${kpi.score}%` }} viewport={{ once: true }} className="h-full rounded-full bg-gradient-to-r from-cyan-300 to-emerald-300" /></div>
          </div>
        ))}
      </div>
    </section>
  );
}

export function BusinessModelCanvas() {
  return (
    <section id="business" className="section-shell">
      <div className="mx-auto max-w-4xl text-center">
        <span className="eyebrow">Business Model Canvas</span>
        <h2 className="section-title mx-auto">A startup-ready path for B2G and B2B deployment.</h2>
        <p className="section-copy mx-auto">Sentinel can be sold as SaaS monitoring, Drone-as-a-Service, or licensed AI risk intelligence.</p>
      </div>
      <motion.div initial="hidden" whileInView="show" viewport={{ once: true, margin: '-120px' }} transition={{ staggerChildren: 0.06 }} className="mt-12 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {businessModel.map((block) => (
          <motion.article key={block.title} variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } }} className="glass-card">
            <h3 className="border-b border-white/10 pb-3 text-xl font-black text-cyan-100">{block.title}</h3>
            <ul className="mt-4 space-y-3">
              {block.items.map((item) => <li key={item} className="flex gap-3 text-sm leading-6 text-slate-300"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-300 shadow-greenGlow" /> {item}</li>)}
            </ul>
          </motion.article>
        ))}
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
    <motion.div ref={ref} initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }} viewport={{ once: true }} className="glass-card text-center">
      <div className="metric-number">{metric.prefix ?? ''}{display.toFixed(metric.value % 1 ? 1 : 0)}{metric.suffix}</div>
      <div className="mt-2 text-lg font-black text-white">{metric.label}</div>
      <p className="mt-2 text-sm text-slate-400">{metric.caption}</p>
    </motion.div>
  );
}
