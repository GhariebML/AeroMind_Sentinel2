import React from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, Clock, Activity, CameraOff, AlertCircle, TrendingUp, ScanEye, Crosshair, ShieldAlert, Zap } from 'lucide-react';

const problems = [
  { icon: AlertTriangle, title: "Highway Accidents", desc: "Egypt sees thousands of highway incidents annually, requiring faster response." },
  { icon: Clock, title: "Delayed Detection", desc: "Traditional reporting relies on calls, causing critical delays in emergency response." },
  { icon: Activity, title: "Sudden Congestion", desc: "Accidents quickly cascade into massive traffic jams if not identified instantly." },
  { icon: CameraOff, title: "Limited Camera Coverage", desc: "Fixed cameras have blind spots and cannot easily track moving incidents over long stretches." },
  { icon: AlertCircle, title: "Slow Response Times", desc: "Lack of precise incident location delays ambulance and police dispatch." },
  { icon: TrendingUp, title: "Long Road Segments", desc: "New massive highway projects require modern, scalable monitoring solutions." }
];

const solutions = [
  { icon: ScanEye, title: "Autonomous Drone Monitoring", desc: "UAVs continuously patrol high-risk segments, providing dynamic overhead coverage." },
  { icon: Crosshair, title: "Real-Time AI Detection", desc: "YOLOv8 + SAHI identifies vehicles, accidents, and pedestrians instantly." },
  { icon: Activity, title: "Multi-Object Tracking", desc: "BoT-SORT maintains persistent IDs on moving targets even during occlusion." },
  { icon: ShieldAlert, title: "Highway Risk Scoring", desc: "Algorithmic risk engine calculates severity based on speed, lane, and object type." },
  { icon: AlertTriangle, title: "Emergency Alerts", desc: "Automated alert generation dispatches exact coordinates to the control room." },
  { icon: Zap, title: "Energy-Aware Navigation", desc: "Reinforcement Learning optimizes flight paths to maximize battery and coverage." }
];

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
};

export function ProblemEgypt() {
  return (
    <section id="problem" className="section">
      <div className="container">
        <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
          <span className="subtitle">The Challenge</span>
          <h2 className="title">The Reality of Egypt's Highways</h2>
          <p className="description" style={{ margin: '0 auto' }}>
            Despite massive infrastructure expansion, monitoring vast highway networks efficiently remains a critical safety challenge.
          </p>
        </div>

        <motion.div 
          className="grid-3"
          variants={containerVariants}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-100px" }}
        >
          {problems.map((p, i) => (
            <motion.div key={i} className="glass-card" variants={itemVariants} style={{ padding: '2rem' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(255, 59, 59, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.5rem', color: 'var(--accent-red)' }}>
                <p.icon size={24} />
              </div>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '0.75rem' }}>{p.title}</h3>
              <p style={{ color: 'var(--text-muted)' }}>{p.desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

export function SentinelSolution() {
  return (
    <section id="solution" className="section">
      <div className="container">
        <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
          <span className="subtitle text-gradient-emerald">The Solution</span>
          <h2 className="title">Intelligent Aerial Overwatch</h2>
          <p className="description" style={{ margin: '0 auto' }}>
            AeroMind Sentinel deploys autonomous drones equipped with edge-AI to process highway events in real-time, instantly converting visual data into actionable emergency intelligence.
          </p>
        </div>

        <motion.div 
          className="grid-3"
          variants={containerVariants}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-100px" }}
        >
          {solutions.map((s, i) => (
            <motion.div key={i} className="glass-card" variants={itemVariants} style={{ padding: '2rem', borderColor: 'rgba(0, 240, 255, 0.15)' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(0, 240, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.5rem', color: 'var(--accent-cyan)' }}>
                <s.icon size={24} />
              </div>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '0.75rem' }}>{s.title}</h3>
              <p style={{ color: 'var(--text-muted)' }}>{s.desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
