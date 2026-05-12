import React from 'react';
import { motion } from 'framer-motion';

const metrics = [
  { label: "MOTA (Tracking Accuracy)", value: "83.2%", trend: "+2.1%" },
  { label: "IDF1 Score", value: "78.5%", trend: "+1.4%" },
  { label: "ID Switches / 1k", value: "11", trend: "-4" },
  { label: "Energy Saved (PPO)", value: "34.8%", trend: "+5.2%" },
  { label: "Mission Duration Inc.", value: "72%", trend: "+12%" },
  { label: "Processing Latency", value: "~45ms", trend: "-5ms" },
];

const businessModel = [
  { title: "Customer Segments", items: ["National Road Authorities", "Smart City Planners", "Emergency Response Units", "Toll Road Operators"] },
  { title: "Value Proposition", items: ["Real-time incident detection", "Reduced accident response time", "Scalable autonomous coverage", "Optimized drone battery life"] },
  { title: "Revenue Streams", items: ["SaaS Subscription per highway km", "Hardware integration fees", "Custom AI retraining", "Data analytics reports"] },
  { title: "Key Resources", items: ["YOLOv8/SAHI AI Pipeline", "PPO Energy-Aware Nav", "Edge Compute Units", "Cloud Dashboard"] },
  { title: "Cost Structure", items: ["Cloud Infrastructure", "Drone Maintenance", "Model Training", "R&D"] },
  { title: "Key Partners", items: ["Drone Manufacturers", "Telecom Providers (5G)", "Government Transport Ministries"] }
];

export function SentinelMetrics() {
  return (
    <section id="metrics" className="section">
      <div className="container">
        <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
          <span className="subtitle text-gradient-emerald">Performance Indicators</span>
          <h2 className="title">System Metrics & KPIs</h2>
          <p className="description" style={{ margin: '0 auto' }}>
            Benchmarked against state-of-the-art multi-object tracking and autonomous navigation standards.
          </p>
        </div>

        <div className="grid-3">
          {metrics.map((m, i) => (
            <motion.div 
              key={i} 
              className="glass-card" 
              style={{ padding: '2rem', textAlign: 'center' }}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
            >
              <div style={{ fontSize: '3rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '0.5rem', lineHeight: 1 }}>
                {m.value}
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: '1rem', fontWeight: 500 }}>
                {m.label}
              </div>
              <div style={{ color: m.trend.startsWith('+') ? 'var(--accent-emerald)' : 'var(--accent-cyan)', fontSize: '0.85rem', marginTop: '0.5rem', fontWeight: 600 }}>
                {m.trend} vs baseline
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function BusinessModelCanvas() {
  return (
    <section id="business" className="section" style={{ background: 'rgba(0,0,0,0.3)' }}>
      <div className="container">
        <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
          <span className="subtitle text-gradient-purple">Go-To-Market</span>
          <h2 className="title">Business Model Canvas</h2>
          <p className="description" style={{ margin: '0 auto' }}>
            A scalable, B2B / B2G business model designed for national infrastructure integration.
          </p>
        </div>

        <div className="grid-3">
          {businessModel.map((bm, i) => (
            <motion.div 
              key={i} 
              className="glass-card" 
              style={{ padding: '1.5rem' }}
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
            >
              <h3 style={{ fontSize: '1.1rem', color: 'var(--accent-cyan)', marginBottom: '1rem', borderBottom: '1px solid var(--border-dim)', paddingBottom: '0.5rem' }}>{bm.title}</h3>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {bm.items.map((item, j) => (
                  <li key={j} style={{ color: 'var(--text-muted)', fontSize: '0.9rem', display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                    <span style={{ color: 'var(--accent-cyan)' }}>•</span>
                    {item}
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
