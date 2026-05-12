import React from 'react';
import { motion } from 'framer-motion';
import { Camera, BrainCircuit, Target, ShieldAlert, Navigation, MonitorDot, ArrowDown } from 'lucide-react';

const pipelineSteps = [
  { icon: Camera, title: "Drone Camera & Telemetry", desc: "Captures high-res highway video and flight data." },
  { icon: BrainCircuit, title: "YOLOv8 + SAHI Detection", desc: "Identifies small vehicles and pedestrians from high altitudes." },
  { icon: Target, title: "BoT-SORT Tracking", desc: "Assigns persistent IDs to track movements across frames." },
  { icon: ShieldAlert, title: "Highway Risk Engine", desc: "Analyzes tracks to calculate incident severity and risk." },
  { icon: Navigation, title: "PPO Energy-Aware Nav", desc: "Adjusts drone patrol path based on risk and battery level." },
  { icon: MonitorDot, title: "Emergency Dashboard", desc: "Alerts human operators with actionable response recommendations." }
];

export default function HighwayPipeline() {
  return (
    <section id="pipeline" className="section" style={{ background: 'rgba(0,0,0,0.3)' }}>
      <div className="container">
        <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
          <span className="subtitle text-gradient-purple">Technical Architecture</span>
          <h2 className="title">AI Processing Pipeline</h2>
          <p className="description" style={{ margin: '0 auto' }}>
            A continuous loop of detection, tracking, analysis, and autonomous action.
          </p>
        </div>

        <div style={{ maxWidth: '800px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {pipelineSteps.map((step, index) => (
            <React.Fragment key={index}>
              <motion.div 
                className="glass-card" 
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                style={{ 
                  padding: '1.5rem 2rem', 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '1.5rem',
                  position: 'relative',
                  overflow: 'hidden'
                }}
              >
                {/* Neon left border */}
                <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: '4px', background: 'var(--accent-cyan)' }} />
                
                <div style={{ color: 'var(--accent-cyan)' }}>
                  <step.icon size={32} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>{step.title}</h3>
                  <p style={{ color: 'var(--text-muted)' }}>{step.desc}</p>
                </div>
              </motion.div>
              
              {index < pipelineSteps.length - 1 && (
                <div style={{ display: 'flex', justifyContent: 'center', color: 'var(--border-dim)' }}>
                  <ArrowDown size={24} />
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    </section>
  );
}
