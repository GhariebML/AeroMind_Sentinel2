import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Battery, TriangleAlert, ShieldAlert, AlertCircle } from 'lucide-react';
import { scenarioEvents } from '../data/highwayEvents';
import { calculateHighwayRisk, classifySeverity, generateHighwayAlerts, summarizeMissionRisk } from '../lib/highwayRiskEngine';
import { HighwayEvent, MissionRiskSummary, HighwayAlert } from '../types/highway';

const SCENARIOS = [
  { id: 'normal', label: 'Normal Traffic' },
  { id: 'stopped', label: 'Stopped Vehicle' },
  { id: 'accident', label: 'Accident Detected' },
  { id: 'congestion', label: 'Congestion Building' },
  { id: 'pedestrian', label: 'Pedestrian on Highway' },
  { id: 'blocked', label: 'Blocked Lane' }
];

export default function LiveHighwaySimulation() {
  const [currentScenario, setCurrentScenario] = useState('stopped');
  const [events, setEvents] = useState<HighwayEvent[]>([]);
  const [alerts, setAlerts] = useState<HighwayAlert[]>([]);
  const [summary, setSummary] = useState<MissionRiskSummary | null>(null);
  const [battery, setBattery] = useState(84);

  useEffect(() => {
    // Load events for scenario
    const newEvents = scenarioEvents[currentScenario] || [];
    setEvents(newEvents);
    setAlerts(generateHighwayAlerts(newEvents));
    setSummary(summarizeMissionRisk(newEvents));

    // Slight battery drain simulation
    setBattery(prev => Math.max(20, prev - (Math.random() * 2)));
  }, [currentScenario]);

  return (
    <section id="simulation" className="section">
      <div className="container">
        <div style={{ marginBottom: '2rem' }}>
          <span className="subtitle">04 Live Highway Simulation</span>
          <h2 className="title" style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>Interactive Mission Control.</h2>
          <p className="description">Demonstrates how the AI pipeline reacts to various highway scenarios in real-time.</p>
        </div>

        {/* Scenario Controls */}
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '2rem' }}>
          {SCENARIOS.map(sc => (
            <button 
              key={sc.id}
              className={`btn ${currentScenario === sc.id ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setCurrentScenario(sc.id)}
              style={{ padding: '0.75rem 1.25rem', fontSize: '0.9rem' }}
            >
              {sc.label}
            </button>
          ))}
        </div>

        <div className="grid-2">
          {/* Feed Canvas */}
          <div className="glass-card" style={{ position: 'relative', height: '500px', overflow: 'hidden' }}>
            <img 
              src="/highway_aerial.png" 
              alt="Highway Feed" 
              style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.6, filter: 'brightness(0.7)' }} 
            />
            
            {/* HUD Overlay */}
            <div style={{ position: 'absolute', top: '1rem', left: '1rem', display: 'flex', gap: '1rem' }}>
              <span className="badge medium animate-pulse">Live Feed</span>
              <span className="mono" style={{ color: 'var(--accent-emerald)', fontSize: '0.85rem' }}>Scenario: {currentScenario}</span>
            </div>

            {/* Tracking Boxes */}
            <AnimatePresence>
              {events.map((evt) => (
                <motion.div
                  key={evt.id}
                  initial={{ opacity: 0, scale: 1.5 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0 }}
                  className={`tracking-box ${classifySeverity(evt.riskScore ?? calculateHighwayRisk(evt))}`}
                  style={{
                    left: `${evt.position.x}%`,
                    top: `${evt.position.y}%`,
                    width: '80px',
                    height: '60px'
                  }}
                >
                  <span>{evt.trackId}</span>
                  <strong>{evt.type.replace('_', ' ')}</strong>
                </motion.div>
              ))}
            </AnimatePresence>
            
            {/* Scan line effect */}
            <motion.div
              animate={{ top: ['0%', '100%', '0%'] }}
              transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
              style={{
                position: 'absolute',
                left: 0,
                right: 0,
                height: '2px',
                background: 'rgba(0, 240, 255, 0.5)',
                boxShadow: '0 0 10px rgba(0,240,255,0.8)',
                zIndex: 10
              }}
            />
          </div>

          {/* Mission Control Panel */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            
            {/* Telemetry Grid */}
            <div className="glass-card" style={{ padding: '2rem' }}>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Activity size={20} color="var(--accent-cyan)" /> Mission Control
              </h3>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                <div>
                  <div style={{ fontSize: '3.5rem', fontWeight: 800, lineHeight: 1, color: summary?.maxRisk && summary.maxRisk > 80 ? 'var(--accent-red)' : 'var(--accent-cyan)' }}>
                    {summary?.maxRisk || 0}
                  </div>
                  <div className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>MAX RISK SCORE</div>
                </div>

                <div>
                  <div style={{ display: 'inline-flex', padding: '0.25rem 0.75rem', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: summary?.criticalCount ? 'var(--accent-red)' : 'var(--accent-orange)' }}>
                      {summary?.criticalCount ? 'Critical' : summary?.highRiskCount ? 'High' : 'Normal'} Severity
                    </span>
                  </div>
                  <div className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>CURRENT STATUS</div>
                </div>

                <div>
                  <div style={{ fontSize: '2.5rem', fontWeight: 700, lineHeight: 1 }}>
                    {Math.round(battery)}%
                  </div>
                  <div className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <Battery size={14} /> DRONE BATTERY
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 700, lineHeight: 1, marginTop: '1rem' }}>
                    {summary?.criticalCount ? 'Emergency' : summary?.highRiskCount ? 'Risk Patrol' : 'Normal Patrol'}
                  </div>
                  <div className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>FLIGHT MODE</div>
                </div>
              </div>

              {/* Recommendation Panel */}
              <div style={{ marginTop: '2rem', padding: '1rem', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', border: '1px solid var(--border-dim)' }}>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>{summary?.recommendedAction}</p>
              </div>
            </div>

            {/* Alerts Panel */}
            <div className="glass-card" style={{ padding: '2rem', flex: 1 }}>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <TriangleAlert size={20} color="var(--accent-orange)" /> Active Alerts
              </h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '250px', overflowY: 'auto' }}>
                <AnimatePresence>
                  {alerts.length === 0 ? (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <AlertCircle size={16} /> No active alerts detected.
                    </motion.div>
                  ) : (
                    alerts.map((alert) => (
                      <motion.div
                        key={alert.id}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className={`alert-card ${alert.severity}`}
                      >
                        <header>
                          <strong>{alert.title}</strong>
                          <span className="mono">{alert.severity.toUpperCase()} · {alert.riskScore}/100</span>
                        </header>
                        <p>{alert.message}</p>
                        <small>{alert.recommendation}</small>
                      </motion.div>
                    ))
                  )}
                </AnimatePresence>
              </div>
            </div>

          </div>
        </div>
      </div>
    </section>
  );
}
