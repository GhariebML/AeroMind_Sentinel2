import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, ShieldAlert } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

const NAV_LINKS = [
  { name: 'Problem', href: '#problem' },
  { name: 'Solution', href: '#solution' },
  { name: 'Pipeline', href: '#pipeline' },
  { name: 'Simulation', href: '#simulation' },
  { name: 'Metrics', href: '#metrics' },
  { name: 'Business', href: '#business' },
  { name: 'Impact', href: '#impact' },
  { name: 'Roadmap', href: '#roadmap' },
];

export default function Layout({ children }: LayoutProps) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleNavClick = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    e.preventDefault();
    setIsMobileMenuOpen(false);
    const target = document.querySelector(href);
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div style={{ position: 'relative', zIndex: 10 }}>
      <header
        style={{
          position: 'fixed',
          top: 0,
          width: '100%',
          zIndex: 100,
          transition: 'all 0.3s ease',
          background: isScrolled ? 'rgba(5, 11, 20, 0.85)' : 'transparent',
          backdropFilter: isScrolled ? 'blur(12px)' : 'none',
          borderBottom: isScrolled ? '1px solid var(--border-dim)' : '1px solid transparent',
        }}
      >
        <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: '80px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontWeight: 800, fontSize: '1.25rem', letterSpacing: '-0.02em' }}>
            <ShieldAlert size={28} color="var(--accent-cyan)" />
            <span style={{ color: 'var(--accent-cyan)' }}>AEROMIND</span>
            <span>SENTINEL</span>
          </div>

          {/* Desktop Nav */}
          <nav style={{ display: 'none' }} className="md-flex">
            <ul style={{ display: 'flex', gap: '2rem', listStyle: 'none', margin: 0, padding: 0 }}>
              {NAV_LINKS.map((link) => (
                <li key={link.name}>
                  <a
                    href={link.href}
                    onClick={(e) => handleNavClick(e, link.href)}
                    style={{
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      color: 'var(--text-muted)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      transition: 'color 0.2s'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.color = 'var(--accent-cyan)'}
                    onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
                  >
                    {link.name}
                  </a>
                </li>
              ))}
            </ul>
          </nav>

          <div style={{ display: 'none' }} className="md-flex">
            <button className="btn btn-primary" onClick={(e) => handleNavClick(e as any, '#simulation')}>
              Launch Simulation
            </button>
          </div>

          {/* Mobile Toggle */}
          <button 
            className="md-hidden"
            style={{ background: 'none', border: 'none', color: 'white' }}
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          >
            {isMobileMenuOpen ? <X size={28} /> : <Menu size={28} />}
          </button>
        </div>

        {/* Mobile Menu */}
        <AnimatePresence>
          {isMobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                width: '100%',
                background: 'var(--bg-panel)',
                backdropFilter: 'blur(16px)',
                borderBottom: '1px solid var(--border-dim)',
                padding: '1rem 2rem',
              }}
            >
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {NAV_LINKS.map((link) => (
                  <li key={link.name}>
                    <a
                      href={link.href}
                      onClick={(e) => handleNavClick(e, link.href)}
                      style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-main)' }}
                    >
                      {link.name}
                    </a>
                  </li>
                ))}
              </ul>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      <main>
        {children}
      </main>

      <footer style={{ borderTop: '1px solid var(--border-dim)', padding: '3rem 0', marginTop: '6rem', background: 'rgba(0,0,0,0.5)' }}>
        <div className="container flex-between">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontWeight: 800 }}>
            <ShieldAlert size={24} color="var(--accent-cyan)" />
            <span>AeroMind Sentinel</span>
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            &copy; 2026 AeroMind Technologies. All rights reserved.
          </div>
        </div>
      </footer>

      {/* Basic media query styles injected for md-flex and md-hidden */}
      <style>{`
        .md-flex { display: none; }
        @media (min-width: 992px) {
          .md-flex { display: flex !important; }
          .md-hidden { display: none !important; }
        }
      `}</style>
    </div>
  );
}
