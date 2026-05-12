import { AnimatePresence, motion } from 'framer-motion';
import { Battery, Pause, Play, Radar, RefreshCw, Satellite, ShieldAlert, Siren, Zap } from 'lucide-react';
import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { usePythonInferenceEvents } from '../hooks/usePythonInferenceEvents';
import { scenarios } from '../data/highwayEvents';
import { calculateHighwayRisk, classifySeverity, generateHighwayAlerts, summarizeMissionRisk } from '../lib/highwayRiskEngine';
import type { DroneTelemetry, HighwayEvent } from '../types/highway';

const severityClasses = {
  low: 'border-emerald-300/40 bg-emerald-300/10 text-emerald-200',
  medium: 'border-cyan-300/40 bg-cyan-300/10 text-cyan-200',
  high: 'border-orange-300/50 bg-orange-400/10 text-orange-200',
  critical: 'border-red-300/60 bg-red-400/10 text-red-200 shadow-redGlow',
};

export default function LiveHighwaySimulation() {
  const [scenarioId, setScenarioId] = useState('accident');
  const [running, setRunning] = useState(true);
  const [tick, setTick] = useState(0);
  const [videoMode, setVideoMode] = useState(false);
  const [pythonMode, setPythonMode] = useState(false);
  const [judgeMode, setJudgeMode] = useState(false);
  const { events: pythonEvents, source: inferenceSource, connected } = usePythonInferenceEvents(pythonMode && running);

  const scenario = scenarios.find((item) => item.id === scenarioId) ?? scenarios[0];
  const events = useMemo(
    () => scoreEvents(pythonMode && pythonEvents?.length ? pythonEvents : scenario.events),
    [pythonMode, pythonEvents, scenario.events],
  );
  const alerts = useMemo(() => generateHighwayAlerts(events), [events]);
  const summary = useMemo(() => summarizeMissionRisk(events), [events]);
  const telemetry: DroneTelemetry = {
    battery: Math.max(48, 92 - tick * 0.13 - summary.maxRisk * 16),
    altitude: 118 + Math.sin(tick / 4) * 8,
    speed: scenarioId === 'emergency' ? 24 : 18 + summary.maxRisk * 12,
    coverage: Math.min(98, 74 + tick * 0.08 + events.length * 4),
    latency: 38 + Math.round(summary.averageRisk * 18),
    mode: scenario.missionMode,
  };

  useEffect(() => {
    if (!running) return undefined;
    const id = window.setInterval(() => setTick((value) => value + 1), 900);
    return () => window.clearInterval(id);
  }, [running]);

  useEffect(() => {
    if (!judgeMode || !running) return undefined;
    const id = window.setInterval(() => {
      setScenarioId((current) => {
        const index = scenarios.findIndex((item) => item.id === current);
        return scenarios[(index + 1) % scenarios.length].id;
      });
      setTick(0);
    }, 6500);
    return () => window.clearInterval(id);
  }, [judgeMode, running]);

  const reset = () => {
    setTick(0);
    setRunning(true);
  };

  return (
    <section id="simulation" className="section-shell">
      <div className="mb-12 flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
        <div>
          <span className="eyebrow"><Radar size={14} /> Live Highway Simulation</span>
          <h2 className="section-title">Mission control demo that judges can understand instantly.</h2>
          <p className="section-copy">The simulation runs fully in-browser with animated vehicles, bounding boxes, drone scan overlays, scenario events, risk scoring, alerts, telemetry, and response recommendations.</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <button onClick={() => setRunning(true)} className="btn-primary"><Play size={16} /> Start</button>
          <button onClick={() => setRunning(false)} className="btn-secondary"><Pause size={16} /> Pause</button>
          <button onClick={reset} className="btn-secondary"><RefreshCw size={16} /> Reset</button>
          <button onClick={() => setJudgeMode((value) => !value)} className={judgeMode ? 'btn-primary' : 'btn-secondary'}><Siren size={16} /> Judge Mode</button>
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.35fr_.65fr]">
        <div className="glass-panel overflow-hidden p-4">
          <div className="mb-4 flex flex-wrap gap-2">
            <button onClick={() => setVideoMode((value) => !value)} className={`rounded-full border px-4 py-2 text-xs font-black uppercase tracking-[0.12em] transition ${videoMode ? 'border-emerald-300 bg-emerald-300 text-slate-950 shadow-greenGlow' : 'border-white/10 bg-white/5 text-slate-300 hover:border-emerald-300/50'}`}>Video BG</button>
            <button onClick={() => setPythonMode((value) => !value)} className={`rounded-full border px-4 py-2 text-xs font-black uppercase tracking-[0.12em] transition ${pythonMode ? 'border-purple-300 bg-purple-300 text-slate-950 shadow-glow' : 'border-white/10 bg-white/5 text-slate-300 hover:border-purple-300/50'}`}>Python Events</button>
            {scenarios.map((item) => (
              <button key={item.id} onClick={() => { setScenarioId(item.id); setTick(0); }} className={`rounded-full border px-4 py-2 text-xs font-black uppercase tracking-[0.12em] transition ${scenarioId === item.id ? 'border-cyan-300 bg-cyan-300 text-slate-950 shadow-glow' : 'border-white/10 bg-white/5 text-slate-300 hover:border-cyan-300/50'}`}>
                {item.label}
              </button>
            ))}
          </div>

          <div className="relative min-h-[620px] overflow-hidden rounded-[1.5rem] border border-cyan-300/20 bg-slate-950 scanline">
            <HighwayCanvas events={events} tick={tick} running={running} videoMode={videoMode} />
            <div className="absolute left-5 top-5 flex flex-wrap gap-3">
              <span className="status-chip border-emerald-300/40 bg-emerald-300/10 text-emerald-200"><span className="h-2 w-2 animate-pulse rounded-full bg-emerald-300" /> {running ? 'Live mission' : 'Paused'}</span>
              <span className="status-chip border-cyan-300/40 bg-cyan-300/10 text-cyan-200">Scenario · {pythonMode && pythonEvents?.length ? 'Python inference' : scenario.label}</span>
              <span className={`status-chip ${connected ? 'border-purple-300/40 bg-purple-300/10 text-purple-200' : 'border-white/10 bg-white/5 text-slate-300'}`}>Source · {pythonMode ? inferenceSource : 'browser_simulation'}</span>
            </div>
            <div className="absolute bottom-5 left-5 right-5 rounded-2xl border border-white/10 bg-slate-950/80 p-4 backdrop-blur-xl">
              <div className="font-bold text-white">{scenario.headline}</div>
              <p className="mt-1 text-sm text-slate-400">{scenario.description}</p>
            </div>
          </div>
        </div>

        <aside className="grid gap-5">
          <div className="glass-card">
            <div className="mb-4 flex items-center justify-between">
              <div><div className="hud-label">Mission mode</div><div className="text-xl font-black text-white">{telemetry.mode}</div></div>
              <Satellite className="text-cyan-200" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <TelemetryCard icon={<Battery size={18} />} label="Battery" value={`${telemetry.battery.toFixed(0)}%`} tone="green" />
              <TelemetryCard icon={<Radar size={18} />} label="Altitude" value={`${telemetry.altitude.toFixed(0)}m`} tone="cyan" />
              <TelemetryCard icon={<Zap size={18} />} label="Speed" value={`${telemetry.speed.toFixed(0)}m/s`} tone="cyan" />
              <TelemetryCard icon={<ActivityIcon />} label="Latency" value={`${telemetry.latency}ms`} tone="purple" />
            </div>
            <div className="mt-5 h-3 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-gradient-to-r from-cyan-300 to-emerald-300" style={{ width: `${telemetry.battery}%` }} /></div>
          </div>

          <div className="glass-card">
            <div className="flex items-start justify-between gap-4">
              <div><div className="hud-label">Mission risk score</div><div className="metric-number">{Math.round(summary.maxRisk * 100)}</div></div>
              <span className={`rounded-full border px-3 py-1 font-mono text-xs font-black uppercase ${severityClasses[classifySeverity(summary.maxRisk)]}`}>{classifySeverity(summary.maxRisk)}</span>
            </div>
            <p className="mt-3 leading-7 text-slate-300">{summary.recommendedAction}</p>
          </div>

          <div className="glass-card max-h-[430px] overflow-auto">
            <div className="mb-4 flex items-center gap-2 text-white"><Siren className="text-red-300" /> <h3 className="text-xl font-black">Alert Panel</h3></div>
            <AnimatePresence mode="popLayout">
              {alerts.map((alert) => (
                <motion.article key={alert.id} initial={{ opacity: 0, x: 18 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }} className={`mb-3 rounded-2xl border p-4 ${severityClasses[alert.severity]}`}>
                  <div className="flex items-center justify-between gap-3"><strong>{alert.title}</strong><span className="font-mono text-xs">{Math.round(alert.riskScore * 100)}/100</span></div>
                  <p className="mt-2 text-sm leading-6 text-slate-200/85">{alert.message}</p>
                  <p className="mt-2 text-xs font-semibold text-white/90">{alert.recommendation}</p>
                </motion.article>
              ))}
            </AnimatePresence>
          </div>
        </aside>
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-4">
        <MiniKpi label="Event timeline" value={`${events.length} active`} />
        <MiniKpi label="Coverage" value={`${telemetry.coverage.toFixed(0)}%`} />
        <MiniKpi label="Critical alerts" value={`${summary.criticalCount}`} />
        <MiniKpi label="System status" value={running ? 'Online' : 'Paused'} />
      </div>
    </section>
  );
}

function HighwayCanvas({ events, tick, running, videoMode }: { events: HighwayEvent[]; tick: number; running: boolean; videoMode: boolean }) {
  const vehicles = Array.from({ length: 16 }, (_, index) => ({
    id: index,
    left: 18 + (index % 4) * 17,
    delay: -(index * 0.48),
    color: index % 5 === 0 ? 'text-emerald-300 bg-emerald-300' : index % 3 === 0 ? 'text-cyan-300 bg-cyan-300' : 'text-blue-300 bg-blue-300',
    speed: 4.8 + (index % 4) * 0.8,
  }));

  return (
    <div className="absolute inset-0 overflow-hidden bg-[radial-gradient(circle_at_center,rgba(34,211,238,.14),transparent_30rem),linear-gradient(90deg,transparent_0_14%,rgba(34,211,238,.16)_14%_15%,transparent_15%_31%,rgba(34,211,238,.12)_31%_32%,transparent_32%_48%,rgba(34,211,238,.12)_48%_49%,transparent_49%_65%,rgba(34,211,238,.16)_65%_66%,transparent_66%)]">
      {videoMode && <video className="absolute inset-0 h-full w-full object-cover opacity-45" src="/videos/highway-demo.mp4" autoPlay muted loop playsInline onError={(event) => { event.currentTarget.style.display = 'none'; }} />}
      <div className="absolute inset-y-0 left-1/2 w-[54%] -translate-x-1/2 bg-slate-900/80 shadow-2xl shadow-cyan-950/50" />
      <div className="absolute inset-y-0 left-[36%] w-px bg-cyan-200/40" /><div className="absolute inset-y-0 left-[50%] w-px bg-cyan-200/30" /><div className="absolute inset-y-0 left-[64%] w-px bg-cyan-200/40" />
      <div className="absolute inset-x-0 top-0 h-full bg-[linear-gradient(to_bottom,transparent_0_28px,rgba(34,211,238,.16)_29px,transparent_31px)] bg-[length:100%_58px]" style={{ transform: `translateY(${running ? tick * 4 : tick}px)` }} />
      <div className="absolute left-1/2 top-1/2 h-72 w-72 -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-300/30 bg-cyan-300/5 shadow-glow" />
      <div className="absolute left-1/2 top-1/2 h-[2px] w-[34rem] origin-left bg-gradient-to-r from-cyan-300 to-transparent" style={{ transform: `rotate(${tick * 18}deg)`, opacity: running ? 0.8 : 0.3 }} />
      {vehicles.map((vehicle) => (
        <div key={vehicle.id} className={`vehicle ${vehicle.color} ${running ? 'animate-drive' : ''}`} style={{ left: `${vehicle.left}%`, animationDelay: `${vehicle.delay}s`, animationDuration: `${vehicle.speed}s`, top: `${(vehicle.id * 43) % 100}%` }} />
      ))}
      {events.map((event) => {
        const severity = event.severity ?? classifySeverity(event.riskScore ?? calculateHighwayRisk(event));
        const color = severity === 'critical' ? 'text-red-300' : severity === 'high' ? 'text-orange-300' : severity === 'medium' ? 'text-cyan-200' : 'text-emerald-300';
        return <div key={event.id} className={`bounding-box ${color}`} style={{ left: `${event.position.x}%`, top: `${event.position.y}%` }}><div>{event.trackId}</div><div className="text-[10px] opacity-80">{event.type.replaceAll('_', ' ')}</div></div>;
      })}
    </div>
  );
}

function scoreEvents(events: HighwayEvent[]): HighwayEvent[] {
  return events.map((event) => {
    const riskScore = calculateHighwayRisk(event);
    return { ...event, timestamp: new Date().toISOString(), riskScore, severity: classifySeverity(riskScore) };
  });
}

function TelemetryCard({ icon, label, value, tone }: { icon: ReactNode; label: string; value: string; tone: 'green' | 'cyan' | 'purple' }) {
  const color = tone === 'green' ? 'text-emerald-300' : tone === 'purple' ? 'text-purple-300' : 'text-cyan-200';
  return <div className="rounded-2xl border border-white/10 bg-white/[.04] p-3"><div className={color}>{icon}</div><div className="hud-label mt-2">{label}</div><div className="text-lg font-black text-white">{value}</div></div>;
}

function ActivityIcon() { return <ShieldAlert size={18} />; }
function MiniKpi({ label, value }: { label: string; value: string }) { return <div className="glass-card"><div className="hud-label">{label}</div><div className="mt-2 text-2xl font-black text-white">{value}</div></div>; }
