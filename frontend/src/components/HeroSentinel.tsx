import React from 'react';
import { motion } from 'framer-motion';
import { Play, FileText, ChevronRight, Activity, Battery, Radio } from 'lucide-react';

export default function HeroSentinel() {
  const handleScroll = (href: string) => {
    document.querySelector(href)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section id="hero" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', paddingTop: '80px', position: 'relative' }}>
      <div className="container">
        <div style={{ maxWidth: '800px' }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
              <span className="badge medium animate-pulse">
                <Radio size={14} style={{ marginRight: '0.25rem' }} /> System Active
              </span>
              <span className="badge low">v2.1.0</span>
            </div>

            <h1 className="title" style={{ margin: 0 }}>
              AeroMind Sentinel
            </h1>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 500, color: 'var(--accent-cyan)', marginBottom: '1.5rem' }}>
              AI-Powered Smart Highway Monitoring & Emergency Response
            </h2>
            
            <p className="description" style={{ fontSize: '1.25rem', maxWidth: '700px' }}>
              Autonomous drone intelligence for detecting highway accidents, congestion, stopped vehicles, pedestrians, blocked lanes, and emergency risk zones in real time.
            </p>

            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginTop: '3rem' }}>
              <button className="btn btn-primary" onClick={() => handleScroll('#simulation')}>
                <Play size={20} fill="currentColor" /> Watch Live Simulation
              </button>
              <button className="btn btn-secondary" onClick={() => handleScroll('#business')}>
                <Activity size={20} /> View Business Model
              </button>
              <button className="btn btn-secondary" onClick={() => window.open('https://github.com/your-repo', '_blank')}>
                <FileText size={20} /> View Technical Report
              </button>
            </div>
          </motion.div>
        </div>

        {/* HUD Elements (Right Side) */}
        <motion.div 
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 1, delay: 0.5 }}
          style={{ position: 'absolute', right: '5%', top: '30%', display: 'flex', flexDirection: 'column', gap: '1rem', display: 'none' }}
          className="md-flex-col"
        >
          <div className="glass-card" style={{ padding: '1rem', minWidth: '200px' }}>
            <div className="subtitle">Drone Status</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <Battery color="var(--accent-emerald)" size={24} />
              <div>
                <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>92%</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>3h 12m remaining</div>
              </div>
            </div>
          </div>
          
          <div className="glass-card" style={{ padding: '1rem', minWidth: '200px' }}>
            <div className="subtitle">Network Link</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <Radio color="var(--accent-cyan)" size={24} />
              <div>
                <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>45ms</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Latency (Encrypted)</div>
              </div>
            </div>
          </div>
        </motion.div>

      </div>

      <style>{`
        .md-flex-col { display: none; }
        @media (min-width: 1024px) {
          .md-flex-col { display: flex !important; }
        }
      `}</style>
    </section>
  );
}
