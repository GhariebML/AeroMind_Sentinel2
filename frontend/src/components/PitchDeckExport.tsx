import { ExternalLink, Printer } from 'lucide-react';
import { businessModel } from '../data/businessModel';
import { coreMetrics, sentinelKpis } from '../data/sentinelMetrics';

const slides = [
  {
    title: 'AeroMind Sentinel',
    eyebrow: 'AI for Egypt Real Problems Hackathon',
    copy: 'AI-Powered Smart Highway Monitoring & Emergency Response System for safer Egyptian highways.',
    bullets: ['Autonomous drone intelligence', 'Real-time highway risk detection', 'Emergency response support'],
  },
  {
    title: 'The Problem',
    eyebrow: 'Road safety and response delay',
    copy: 'Highway accidents, sudden congestion, limited fixed-camera coverage, and slow incident detection create avoidable risk.',
    bullets: ['Delayed reporting', 'Blind spots on long corridors', 'Limited real-time response context'],
  },
  {
    title: 'The Solution',
    eyebrow: 'Mobile AI monitoring',
    copy: 'Sentinel uses aerial AI, tracking, risk scoring, and energy-aware navigation to move toward the highest-risk zones.',
    bullets: ['YOLOv8 + SAHI detection', 'BoT-SORT + OSNet tracking', 'PPO energy-aware navigation'],
  },
  {
    title: 'Live Simulation',
    eyebrow: 'Demo-ready product workflow',
    copy: 'The website simulation demonstrates normal traffic, stopped vehicles, accidents, congestion, pedestrians, blocked lanes, and emergency response mode.',
    bullets: ['Animated vehicles and bounding boxes', 'Live risk scores and alerts', 'Drone telemetry and mission controls'],
  },
  {
    title: 'Technical Proof',
    eyebrow: 'AeroMind AI core metrics',
    copy: 'The product is built on an existing autonomous aerial surveillance stack.',
    bullets: coreMetrics.map((metric: any) => `${metric.label}: ${metric.prefix ?? ''}${metric.value}${metric.suffix}`),
  },
  {
    title: 'Sentinel KPIs',
    eyebrow: 'Highway product indicators',
    copy: 'A judge/investor-friendly view of operational value.',
    bullets: sentinelKpis.map((kpi: any) => `${kpi.label}: ${kpi.value}`),
  },
  {
    title: 'Business Model',
    eyebrow: 'B2G + B2B deployment',
    copy: 'A scalable model for traffic authorities, smart cities, road operators, logistics fleets, insurance, and security providers.',
    bullets: businessModel.slice(0, 5).map((block: any) => `${block.title}: ${block.items[0]}`),
  },
  {
    title: 'Egypt Impact',
    eyebrow: 'Vision 2030 alignment',
    copy: 'AeroMind Sentinel turns aerial monitoring into intelligent emergency response for safer Egyptian highways.',
    bullets: ['Smart transportation', 'Public safety', 'Sustainable smart infrastructure'],
  },
  {
    title: 'Roadmap',
    eyebrow: 'From prototype to pilot',
    copy: 'The next phase moves from hackathon demo to real-world field validation.',
    bullets: ['Real highway video assets', 'Live model output integration', 'Deployment screenshots', 'Pilot corridor deployment'],
  },
];

export default function PitchDeckExport() {
  return (
    <main className="min-h-screen bg-slate-950 text-white print:bg-white print:text-slate-950">
      <div className="sticky top-0 z-50 border-b border-white/10 bg-slate-950/90 px-6 py-4 backdrop-blur-xl print:hidden">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3">
          <div>
            <div className="font-mono text-xs uppercase tracking-[0.24em] text-cyan-200">Pitch Deck PDF Export</div>
            <h1 className="text-2xl font-black">AeroMind Sentinel</h1>
          </div>
          <div className="flex gap-3">
            <button onClick={() => window.print()} className="btn-primary"><Printer size={16} /> Export PDF</button>
            <a href="/" className="btn-secondary"><ExternalLink size={16} /> Back to site</a>
          </div>
        </div>
      </div>

      <div className="mx-auto grid max-w-6xl gap-8 px-6 py-10 print:max-w-none print:px-0 print:py-0">
        {slides.map((slide, index) => (
          <section key={slide.title} className="pitch-slide glass-panel min-h-[720px] overflow-hidden p-10 print:break-after-page print:rounded-none print:border-0 print:bg-white print:p-14 print:shadow-none">
            <div className="mb-10 flex items-center justify-between border-b border-white/10 pb-6 print:border-slate-200">
              <div className="font-mono text-sm font-black uppercase tracking-[0.24em] text-cyan-200 print:text-slate-500">{slide.eyebrow}</div>
              <div className="font-mono text-sm text-slate-400">{String(index + 1).padStart(2, '0')} / {String(slides.length).padStart(2, '0')}</div>
            </div>
            <div className="grid min-h-[540px] items-center gap-10 lg:grid-cols-[1fr_.75fr] print:grid-cols-[1fr_.75fr]">
              <div>
                <h2 className="text-6xl font-black tracking-[-0.07em] text-white print:text-slate-950">{slide.title}</h2>
                <p className="mt-6 max-w-3xl text-2xl leading-10 text-slate-300 print:text-slate-700">{slide.copy}</p>
              </div>
              <div className="rounded-[2rem] border border-cyan-300/20 bg-cyan-300/10 p-6 print:border-slate-200 print:bg-slate-50">
                <div className="mb-5 text-sm font-black uppercase tracking-[0.18em] text-emerald-300 print:text-slate-500">Key points</div>
                <ul className="space-y-4">
                  {slide.bullets.map((bullet: string) => <li key={bullet} className="flex gap-3 text-lg leading-8 text-slate-100 print:text-slate-800"><span className="mt-3 h-2 w-2 shrink-0 rounded-full bg-emerald-300 print:bg-slate-700" />{bullet}</li>)}
                </ul>
              </div>
            </div>
          </section>
        ))}
      </div>

      <style>{`@media print { @page { size: 16in 9in; margin: 0; } body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } .pitch-slide { min-height: 100vh; } }`}</style>
    </main>
  );
}
