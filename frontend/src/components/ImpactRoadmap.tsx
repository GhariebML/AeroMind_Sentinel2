import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Circle } from 'lucide-react';

export function EgyptImpact() {
  return (
    <section id="impact" className="section">
      <div className="container">
        <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
          <span className="subtitle text-gradient-emerald">Vision 2030</span>
          <h2 className="title">Impact on Egypt</h2>
          <p className="description" style={{ margin: '0 auto' }}>
            Aligned with Egypt's Vision 2030 for smart transportation and sustainable infrastructure.
          </p>
        </div>

        <motion.div 
          className="glass-card" 
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          style={{ padding: '3rem', textAlign: 'center', maxWidth: '800px', margin: '0 auto', background: 'linear-gradient(180deg, rgba(20, 32, 48, 0.6) 0%, rgba(0, 240, 255, 0.05) 100%)' }}
        >
          <h3 style={{ fontSize: '2rem', marginBottom: '1.5rem', fontWeight: 700 }}>
            AeroMind Sentinel turns aerial monitoring into intelligent emergency response for safer Egyptian highways.
          </h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem', lineHeight: 1.8 }}>
            By integrating autonomous drones with edge AI, we bypass the infrastructure limitations of fixed cameras, providing dynamic, instant overwatch across newly developed desert highways, reducing emergency response times, and ultimately saving lives.
          </p>
        </motion.div>
      </div>
    </section>
  );
}

const roadmap = [
  { status: 'done', title: "Core AI Pipeline Setup", desc: "YOLOv8 + SAHI detection and BoT-SORT tracking logic established." },
  { status: 'done', title: "Simulation Environment", desc: "AirSim drone control and data collection framework active." },
  { status: 'done', title: "Interactive Dashboard", desc: "Live simulation, risk engine, and React UI fully deployed." },
  { status: 'pending', title: "Real Highway Video Assets", desc: "Integrate licensed highway drone footage for pitch demo." },
  { status: 'pending', title: "Live Model Output Integration", desc: "Connect the frontend directly to the Python backend inference loop." },
  { status: 'pending', title: "Pilot Deployment", desc: "Initial hardware tests on a closed road segment in New Cairo." }
];

export function RoadmapTodo() {
  return (
    <section id="roadmap" className="section" style={{ background: 'rgba(0,0,0,0.3)' }}>
      <div className="container">
        <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
          <span className="subtitle text-gradient-purple">Next Steps</span>
          <h2 className="title">Development Roadmap</h2>
          <p className="description" style={{ margin: '0 auto' }}>
            Our planned milestones for moving from functional prototype to real-world pilot deployment.
          </p>
        </div>

        <div style={{ maxWidth: '600px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {roadmap.map((item, i) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}
            >
              <div style={{ marginTop: '0.25rem' }}>
                {item.status === 'done' ? (
                  <CheckCircle2 color="var(--accent-emerald)" size={24} />
                ) : (
                  <Circle color="var(--border-dim)" size={24} />
                )}
              </div>
              <div className="glass-card" style={{ padding: '1.5rem', flex: 1, borderColor: item.status === 'done' ? 'rgba(0, 255, 136, 0.2)' : 'var(--border-dim)' }}>
                <h3 style={{ fontSize: '1.1rem', marginBottom: '0.25rem', color: item.status === 'done' ? 'var(--text-main)' : 'var(--text-muted)' }}>
                  {item.title}
                </h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{item.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
