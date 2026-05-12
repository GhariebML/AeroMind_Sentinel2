import { AnimatePresence, motion } from 'framer-motion';
import { Menu, ShieldAlert, X } from 'lucide-react';
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
    <div className="relative min-h-screen overflow-hidden bg-sentinel-bg text-slate-100">
      <header className={`fixed inset-x-0 top-0 z-50 transition ${scrolled ? 'border-b border-white/10 bg-slate-950/75 shadow-2xl shadow-black/40 backdrop-blur-2xl' : 'bg-transparent'}`}>
        <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <button onClick={() => goTo('#hero')} className="flex items-center gap-3 text-left">
            <span className="grid h-11 w-11 place-items-center rounded-2xl border border-cyan-300/30 bg-cyan-300/10 shadow-glow">
              <ShieldAlert className="text-cyan-200" size={24} />
            </span>
            <span>
              <span className="block text-sm font-black uppercase tracking-[0.24em] text-cyan-200">AeroMind</span>
              <span className="block text-lg font-black tracking-[-0.04em] text-white">Sentinel</span>
            </span>
          </button>

          <nav className="hidden items-center gap-6 xl:flex">
            {NAV_LINKS.map((link) => (
              <button key={link.href} onClick={() => goTo(link.href)} className="nav-link">
                {link.name}
              </button>
            ))}
          </nav>

          <div className="hidden items-center gap-3 lg:flex">
            <a href="/pitch" className="rounded-full border border-cyan-300/30 bg-cyan-300/10 px-4 py-2 font-mono text-xs font-bold uppercase tracking-[0.2em] text-cyan-200 transition hover:bg-cyan-300 hover:text-slate-950">Pitch PDF</a>
            <button onClick={() => goTo('#simulation')} className="rounded-full border border-emerald-300/40 bg-emerald-300/10 px-4 py-2 font-mono text-xs font-bold uppercase tracking-[0.2em] text-emerald-200 transition hover:bg-emerald-300 hover:text-slate-950">
              Launch Demo
            </button>
          </div>

          <button onClick={() => setOpen((value) => !value)} className="rounded-xl border border-white/10 bg-white/5 p-2 xl:hidden" aria-label="Toggle navigation">
            {open ? <X /> : <Menu />}
          </button>
        </div>
        <AnimatePresence>
          {open && (
            <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -16 }} className="border-t border-white/10 bg-slate-950/95 px-4 py-5 backdrop-blur-2xl xl:hidden">
              <div className="mx-auto grid max-w-7xl gap-2">
                {NAV_LINKS.map((link) => (
                  <button key={link.href} onClick={() => goTo(link.href)} className="rounded-2xl px-4 py-3 text-left font-bold text-slate-200 hover:bg-cyan-300/10 hover:text-cyan-100">
                    {link.name}
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      <main className="relative z-10">{children}</main>

      <footer className="relative z-10 border-t border-white/10 bg-slate-950/80 py-10 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 text-sm text-slate-400 sm:px-6 md:flex-row md:items-center md:justify-between lg:px-8">
          <div className="flex items-center gap-3 font-bold text-white"><ShieldAlert className="text-cyan-200" /> AeroMind Sentinel</div>
          <div>AI-powered highway monitoring · AeroMind AI core · Hackathon-ready prototype</div>
        </div>
      </footer>
    </div>
  );
}
