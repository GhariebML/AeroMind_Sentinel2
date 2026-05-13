import { AnimatePresence, motion } from 'framer-motion';
import { Menu, ShieldAlert, X, Code, User, ExternalLink } from 'lucide-react';
import { useEffect, useState, type ReactNode } from 'react';

const NAV_LINKS = [
  { name: 'Problem', href: '#problem' },
  { name: 'Solution', href: '#solution' },
  { name: 'Pipeline', href: '#pipeline' },
  { name: 'Simulation', href: '#simulation' },
  { name: 'Metrics', href: '#metrics' },
  { name: 'Business Model', href: '#business' },
  { name: 'Egypt Impact', href: '#impact' },
  { name: 'Roadmap', href: '#roadmap' },
];

export default function Layout({ children }: { children: ReactNode }) {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 28);
    onScroll();
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const goTo = (href: string) => {
    setOpen(false);
    document.querySelector(href)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950 text-slate-100 font-sans selection:bg-cyan-500/30">
      <header className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${scrolled ? 'border-b border-white/10 bg-slate-950/80 shadow-2xl shadow-black/40 backdrop-blur-xl py-2' : 'bg-transparent py-4'}`}>
        <div className="mx-auto flex h-16 max-w-[90rem] items-center justify-between px-4 sm:px-6 lg:px-8">
          <button onClick={() => goTo('#hero')} className="flex items-center gap-3 text-left group shrink-0">
            <span className="grid h-10 w-10 place-items-center rounded-xl border border-cyan-400/30 bg-cyan-400/10 shadow-[0_0_15px_rgba(34,211,238,0.2)] group-hover:shadow-[0_0_20px_rgba(34,211,238,0.4)] transition-all">
              <ShieldAlert className="text-cyan-300" size={20} />
            </span>
            <span>
              <span className="block text-[10px] font-black uppercase tracking-[0.25em] text-cyan-300">AeroMind</span>
              <span className="block text-base font-black tracking-tight text-white group-hover:text-cyan-50 transition-colors">Sentinel</span>
            </span>
          </button>

          <nav className="hidden items-center gap-5 xl:flex">
            {NAV_LINKS.map((link) => (
              <button key={link.href} onClick={() => goTo(link.href)} className="whitespace-nowrap text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400 transition hover:text-cyan-300">
                {link.name}
              </button>
            ))}
          </nav>

          <div className="hidden items-center gap-5 xl:flex shrink-0 ml-6 pl-6 border-l border-white/[0.06]">
            <a href="/pitch" className="whitespace-nowrap rounded-full border border-cyan-400/20 bg-transparent px-5 py-2 text-[11px] font-bold uppercase tracking-[0.15em] text-cyan-300 transition hover:bg-cyan-400/10">Pitch PDF</a>
            <button onClick={() => goTo('#simulation')} className="whitespace-nowrap rounded-full bg-cyan-400 px-5 py-2 text-[11px] font-bold uppercase tracking-[0.15em] text-slate-950 shadow-[0_0_15px_rgba(34,211,238,0.3)] transition hover:bg-cyan-300 hover:shadow-[0_0_25px_rgba(34,211,238,0.5)]">
              Watch Demo
            </button>
          </div>

          <button onClick={() => setOpen((value) => !value)} className="rounded-lg border border-white/10 bg-white/5 p-2 xl:hidden text-slate-300 hover:text-white transition" aria-label="Toggle navigation">
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
        
        <AnimatePresence>
          {open && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="border-t border-white/10 bg-slate-950/95 backdrop-blur-2xl xl:hidden overflow-hidden">
              <div className="mx-auto grid max-w-7xl gap-1 px-4 py-4 sm:px-6">
                {NAV_LINKS.map((link) => (
                  <button key={link.href} onClick={() => goTo(link.href)} className="rounded-xl px-4 py-3 text-left text-sm font-semibold text-slate-300 hover:bg-cyan-400/10 hover:text-cyan-300 transition-colors">
                    {link.name}
                  </button>
                ))}
                <div className="mt-4 flex flex-col gap-2 px-4 border-t border-white/5 pt-4">
                  <button onClick={() => goTo('#simulation')} className="rounded-xl bg-cyan-400 px-4 py-3 text-center text-sm font-bold text-slate-950">Watch Demo</button>
                  <a href="/pitch" className="rounded-xl border border-cyan-400/20 px-4 py-3 text-center text-sm font-bold text-cyan-300">Pitch PDF</a>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      <main className="relative z-10">{children}</main>

      {/* ═══════════ FOOTER ═══════════ */}
      <footer className="relative z-10 mt-32 border-t border-white/[0.04] bg-gradient-to-b from-slate-950 via-[#01030a] to-[#000204]">
        {/* Glowing top divider */}
        <div className="absolute -top-px inset-x-0 h-px">
          <div className="mx-auto w-2/3 max-w-2xl h-full bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent" />
        </div>
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-40 h-24 bg-cyan-500/5 blur-[80px] pointer-events-none" />

        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-20 pb-10 sm:pt-28">
          {/* ── Main 3-Column Grid ── */}
          <div className="grid grid-cols-1 gap-16 md:grid-cols-3 lg:gap-12">

            {/* Column 1 — Brand & Navigation */}
            <motion.div initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.6 }} className="flex flex-col gap-7">
              <div className="flex items-center gap-3.5 group">
                <div className="grid h-11 w-11 place-items-center rounded-xl bg-cyan-400/10 border border-cyan-400/20 shadow-[0_0_18px_rgba(34,211,238,0.15)] group-hover:shadow-[0_0_28px_rgba(34,211,238,0.3)] transition-shadow duration-500">
                  <ShieldAlert className="text-cyan-400" size={20} />
                </div>
                <div>
                  <span className="block text-[10px] font-black uppercase tracking-[0.25em] text-cyan-400">AeroMind</span>
                  <span className="block text-lg font-black tracking-tight text-white">Sentinel</span>
                </div>
              </div>

              <p className="text-[13px] leading-[1.8] text-slate-400 max-w-[300px]">
                AI-powered smart highway monitoring and autonomous emergency response operations — built for Egypt's roads.
              </p>

              <nav className="grid grid-cols-2 gap-x-6 gap-y-3 mt-1">
                {[
                  { label: 'Problem & Solution', target: '#problem' },
                  { label: 'Live Simulation', target: '#simulation' },
                  { label: 'Business Model', target: '#business' },
                  { label: 'Roadmap & Impact', target: '#roadmap' },
                ].map((link) => (
                  <button
                    key={link.target}
                    onClick={() => goTo(link.target)}
                    className="text-left text-[13px] font-medium text-slate-500 hover:text-cyan-400 hover:translate-x-0.5 transition-all duration-200"
                  >
                    {link.label}
                  </button>
                ))}
              </nav>
            </motion.div>

            {/* Column 2 — Mission Focus */}
            <motion.div initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.6, delay: 0.1 }} className="flex flex-col gap-5 md:items-center text-left md:text-center md:border-x border-white/[0.04] md:px-10">
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/5 px-3.5 py-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-[10px] font-black uppercase tracking-widest text-emerald-400">Hackathon Focus</span>
              </div>

              <h3 className="text-lg font-black text-white tracking-tight leading-snug">AI for Egypt<br className="hidden md:block" /> Real Problems</h3>

              <p className="text-[13px] text-slate-400 max-w-[280px] leading-[1.8]">
                Built to solve critical infrastructure safety challenges aligned with Egypt Vision 2030 and Sustainable Development Goals.
              </p>

              <div className="flex flex-wrap justify-center gap-2 mt-2">
                {['SDG 9', 'SDG 11', 'Vision 2030'].map((tag) => (
                  <span key={tag} className="rounded-md bg-white/[0.03] border border-white/[0.06] px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest text-slate-500">
                    {tag}
                  </span>
                ))}
              </div>
            </motion.div>

            {/* Column 3 — Identity & Social Links */}
            <motion.div initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.6, delay: 0.2 }} className="flex flex-col gap-7 md:items-end text-left md:text-right">
              <div className="flex flex-col gap-1.5">
                <h3 className="text-lg font-black text-white tracking-tight">Mohamed Gharieb</h3>
                <p className="text-[12px] font-bold uppercase tracking-[0.2em] text-cyan-400/80">AI & Data Science Specialist</p>
              </div>

              {/* Social Links — Professional spacing */}
              <div className="flex flex-col gap-3 w-full md:max-w-[220px]">
                <a
                  href="https://github.com/GhariebML"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 rounded-xl bg-white/[0.03] border border-white/[0.07] px-4 py-3 text-[13px] font-semibold text-slate-300 hover:bg-white/[0.07] hover:border-white/[0.12] hover:text-white hover:-translate-y-0.5 transition-all duration-300 group"
                >
                  <Code size={16} className="text-slate-400 group-hover:text-white transition-colors" />
                  <span className="flex-1">GitHub</span>
                  <ExternalLink size={12} className="text-slate-600 group-hover:text-slate-400 transition-colors" />
                </a>
                <a
                  href="https://www.linkedin.com/in/ghariebml/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 rounded-xl bg-white/[0.03] border border-white/[0.07] px-4 py-3 text-[13px] font-semibold text-slate-300 hover:bg-[#0a66c2]/10 hover:border-[#0a66c2]/30 hover:text-[#4d9eea] hover:-translate-y-0.5 transition-all duration-300 group"
                >
                  <User size={16} className="text-slate-400 group-hover:text-[#4d9eea] transition-colors" />
                  <span className="flex-1">LinkedIn</span>
                  <ExternalLink size={12} className="text-slate-600 group-hover:text-slate-400 transition-colors" />
                </a>
                <a
                  href="https://aero-mind-ai-autonomous-surveillanc.vercel.app/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 rounded-xl bg-cyan-500/[0.06] border border-cyan-500/[0.15] px-4 py-3 text-[13px] font-semibold text-cyan-400 hover:bg-cyan-500/[0.12] hover:border-cyan-500/30 hover:text-cyan-300 hover:-translate-y-0.5 transition-all duration-300 group"
                >
                  <ExternalLink size={16} className="text-cyan-500/70 group-hover:text-cyan-300 transition-colors" />
                  <span className="flex-1">Live Prototype</span>
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                </a>
              </div>

              {/* Status Badge */}
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.5 }}
                className="inline-flex items-center gap-2.5 rounded-full border border-emerald-500/10 bg-emerald-500/[0.04] px-4 py-2.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]"
              >
                <div className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                </div>
                <span className="text-[10px] font-black uppercase tracking-[0.18em] text-emerald-400/70">System Ready</span>
              </motion.div>
            </motion.div>
          </div>

          {/* ── Bottom Bar ── */}
          <div className="mt-16 pt-7 border-t border-white/[0.05]">
            <div className="flex flex-col items-center justify-between sm:flex-row gap-4">
              <p className="text-[12px] font-medium text-slate-600">
                &copy; {new Date().getFullYear()} AeroMind Sentinel · All rights reserved.
              </p>
              <div className="flex items-center gap-8">
                <span className="text-[12px] font-medium text-slate-600 hover:text-slate-400 transition-colors cursor-pointer">Privacy Policy</span>
                <span className="text-[12px] font-medium text-slate-600 hover:text-slate-400 transition-colors cursor-pointer">Terms of Service</span>
                <span className="font-mono text-[10px] font-bold text-slate-700 bg-white/[0.02] border border-white/[0.05] px-2.5 py-1 rounded-md tracking-wider">v1.0.0-beta</span>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

