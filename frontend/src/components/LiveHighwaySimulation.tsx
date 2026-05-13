import { AnimatePresence, motion } from 'framer-motion';
import { Battery, Pause, Play, Radar, RefreshCw, Satellite, Siren, Zap, Info, Activity } from 'lucide-react';
import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { usePythonInferenceEvents } from '../hooks/usePythonInferenceEvents';
import { scenarios } from '../data/highwayEvents';
import { calculateHighwayRisk, classifySeverity, generateHighwayAlerts, summarizeMissionRisk } from '../lib/highwayRiskEngine';
import type { DroneTelemetry, HighwayEvent } from '../types/highway';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { SectionHeader } from './ui/SectionHeader';

const severityClasses = {
  low: 'border-emerald-500/20 bg-emerald-500/10 text-emerald-400',
  medium: 'border-cyan-500/20 bg-cyan-500/10 text-cyan-400',
  high: 'border-orange-500/20 bg-orange-500/10 text-orange-400',
  critical: 'border-red-500/30 bg-red-500/10 text-red-400 shadow-[0_0_15px_rgba(239,68,68,0.2)]',
};

export default function LiveHighwaySimulation() {
  const [scenarioId, setScenarioId] = useState('accident');
  const [running, setRunning] = useState(true);
  const [tick, setTick] = useState(0);
  const [videoMode, setVideoMode] = useState(false);
  const [pythonMode, setPythonMode] = useState(false);
  const [judgeMode, setJudgeMode] = useState(false);
  const { events: pythonEvents } = usePythonInferenceEvents(pythonMode && running);

  const scenario = scenarios.find((item: any) => item.id === scenarioId) ?? scenarios[0];
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
        const index = scenarios.findIndex((item: any) => item.id === current);
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
    <section id="simulation" className="relative z-10 mx-auto w-full max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
      <div className="mb-12 flex flex-col justify-between gap-8 lg:flex-row lg:items-end">
        <div className="max-w-3xl">
          <SectionHeader
            eyebrow="Live Highway Simulation"
            title="Mission control demo."
            align="left"
            className="mb-4"
          />
          <div className="flex items-start gap-3 rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-4 mt-6 shadow-[0_0_20px_rgba(34,211,238,0.1)]">
            <Info className="mt-0.5 shrink-0 text-cyan-400" size={20} />
            <p className="text-[15px] font-medium leading-relaxed text-cyan-50">
              This simulation demonstrates how AeroMind Sentinel detects highway incidents, scores risk, and recommends emergency action using mock real-time events.
            </p>
          </div>
        </div>
        
        <div className="flex flex-col gap-3 shrink-0">
          <div className="flex flex-wrap gap-2 items-center bg-slate-900/60 p-2.5 rounded-xl border border-white/10 backdrop-blur-md">
            <Button variant={running ? 'outline' : 'primary'} size="sm" onClick={() => setRunning(true)}>
              <Play size={14} fill={running ? "none" : "currentColor"} /> Start
            </Button>
            <Button variant={!running ? 'outline' : 'secondary'} size="sm" onClick={() => setRunning(false)}>
              <Pause size={14} fill={!running ? "currentColor" : "none"} /> Pause
            </Button>
            <Button variant="ghost" size="sm" onClick={reset}>
              <RefreshCw size={14} /> Reset
            </Button>
            <div className="w-px h-6 bg-white/10 mx-1"></div>
            <Button variant={judgeMode ? 'primary' : 'outline'} size="sm" onClick={() => setJudgeMode((value) => !value)} className={judgeMode ? "shadow-[0_0_15px_rgba(52,211,153,0.3)]" : ""}>
              <Siren size={14} /> Judge Mode
            </Button>
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.4fr_.6fr]">
        <div className="rounded-[2rem] border border-white/10 bg-slate-900/40 p-4 backdrop-blur-2xl shadow-2xl flex flex-col">
          <div className="mb-4 flex flex-wrap gap-2 items-center justify-between">
            <div className="flex flex-wrap gap-2">
              <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-slate-500 self-center mr-2">Scenarios</span>
              {scenarios.map((item: any) => (
                <button key={item.id} onClick={() => { setScenarioId(item.id); setTick(0); }} className={`rounded-lg border px-3 py-1.5 text-[11px] font-black uppercase tracking-wider transition-all ${scenarioId === item.id ? 'border-cyan-400 bg-cyan-400 text-slate-950 shadow-[0_0_15px_rgba(34,211,238,0.4)]' : 'border-white/10 bg-white/5 text-slate-300 hover:border-cyan-400/50 hover:bg-cyan-400/10'}`}>
                  {item.label}
                </button>
              ))}
            </div>
            <div className="flex gap-2 border-l border-white/10 pl-4">
              <button onClick={() => setVideoMode((value) => !value)} className={`rounded-lg border px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider transition-all ${videoMode ? 'border-emerald-400 text-emerald-400 bg-emerald-400/10' : 'border-white/10 text-slate-400 hover:border-emerald-400/50'}`}>Video BG</button>
              <button onClick={() => setPythonMode((value) => !value)} className={`rounded-lg border px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider transition-all ${pythonMode ? 'border-purple-400 text-purple-400 bg-purple-400/10' : 'border-white/10 text-slate-400 hover:border-purple-400/50'}`}>Python Data</button>
            </div>
          </div>

          <div className="relative flex-grow min-h-[600px] overflow-hidden rounded-[1.5rem] border border-cyan-500/20 bg-slate-950 scanline shadow-inner">
            <HighwayCanvas events={events} tick={tick} running={running} videoMode={videoMode} />
            <div className="absolute left-5 top-5 flex flex-wrap gap-3 z-20">
              <div className="flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 backdrop-blur-md">
                <span className={`h-2 w-2 rounded-full ${running ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
                <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-emerald-300">{running ? 'Live Mission' : 'Paused'}</span>
              </div>
              <div className="flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1.5 backdrop-blur-md">
                <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-cyan-300">SCENARIO: {pythonMode && pythonEvents?.length ? 'Python inference' : scenario.label}</span>
              </div>
            </div>
            <div className="absolute bottom-5 left-5 right-5 rounded-xl border border-white/10 bg-slate-950/80 p-4 backdrop-blur-xl z-20">
              <div className="text-lg font-black text-white">{scenario.headline}</div>
              <p className="mt-1 text-sm leading-relaxed text-slate-300">{scenario.description}</p>
            </div>
          </div>
        </div>

        <aside className="grid gap-6">
          <Card className="p-5 flex flex-col justify-between h-full min-h-[220px]">
            <div className="mb-4 flex items-center justify-between border-b border-white/5 pb-4">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Mission mode</div>
                <div className="text-xl font-black text-white tracking-tight">{telemetry.mode}</div>
              </div>
              <div className="rounded-xl bg-cyan-500/10 border border-cyan-500/20 p-2.5 shadow-[0_0_15px_rgba(34,211,238,0.1)]"><Satellite className="text-cyan-400" size={24} /></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <TelemetryCard icon={<Battery size={16} />} label="Battery" value={`${telemetry.battery.toFixed(0)}%`} tone="green" />
              <TelemetryCard icon={<Radar size={16} />} label="Altitude" value={`${telemetry.altitude.toFixed(0)}m`} tone="cyan" />
              <TelemetryCard icon={<Zap size={16} />} label="Speed" value={`${telemetry.speed.toFixed(0)}m/s`} tone="cyan" />
              <TelemetryCard icon={<Activity size={16} />} label="Latency" value={`${telemetry.latency}ms`} tone="purple" />
            </div>
            <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-slate-900 shadow-inner">
              <div className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-emerald-400 transition-all duration-1000 ease-linear" style={{ width: `${telemetry.battery}%` }} />
            </div>
          </Card>

          <Card className="p-5 bg-slate-900/60 border-white/5">
            <div className="flex items-start justify-between gap-4 border-b border-white/5 pb-4 mb-4">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Mission risk score</div>
                <div className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white to-cyan-300 tracking-tighter">
                  {Math.round(summary.maxRisk * 100)}
                </div>
              </div>
              <span className={`rounded-lg border px-3 py-1.5 font-mono text-[11px] font-black uppercase tracking-widest ${severityClasses[classifySeverity(summary.maxRisk)]}`}>
                {classifySeverity(summary.maxRisk)}
              </span>
            </div>
            <p className="text-sm font-medium leading-relaxed text-slate-300 bg-white/5 rounded-lg p-3 border border-white/5">
              {summary.recommendedAction}
            </p>
          </Card>

          <Card className="max-h-[380px] overflow-auto flex flex-col gap-3 p-4 bg-slate-900/40">
            <div className="mb-2 flex items-center gap-3 text-white sticky top-0 bg-slate-900/95 backdrop-blur-xl p-2 -mx-2 rounded-lg z-10 border border-white/5 shadow-md">
              <div className="rounded-lg bg-red-500/10 p-1.5 border border-red-500/20"><Siren className="text-red-400 animate-pulse" size={18} /></div> 
              <h3 className="text-base font-black tracking-tight">Active Alerts Panel</h3>
              <div className="ml-auto bg-white/10 rounded px-2 py-0.5 text-xs font-mono font-bold">{alerts.length}</div>
            </div>
            <AnimatePresence mode="popLayout">
              {alerts.length === 0 && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-center py-8 text-slate-500 text-sm font-medium">
                  No active alerts. Highway clear.
                </motion.div>
              )}
              {alerts.map((alert) => (
                <motion.article key={alert.id} initial={{ opacity: 0, x: 10, scale: 0.95 }} animate={{ opacity: 1, x: 0, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} transition={{ type: "spring", stiffness: 400, damping: 25 }} className={`rounded-xl border p-3.5 ${severityClasses[alert.severity]} bg-slate-950/80 backdrop-blur-md`}>
                  <div className="flex items-center justify-between gap-3 mb-2">
                    <strong className="text-[13px] font-bold tracking-wide">{alert.title}</strong>
                    <span className="font-mono text-[10px] font-black py-0.5 px-1.5 rounded border border-[currentColor]/30 bg-[currentColor]/10">{Math.round(alert.riskScore * 100)}/100</span>
                  </div>
                  <p className="text-xs leading-relaxed opacity-90">{alert.message}</p>
                  <p className="mt-2.5 pt-2 border-t border-[currentColor]/10 text-[10px] font-black uppercase tracking-widest opacity-100 flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-[currentColor]"></span> {alert.recommendation}
                  </p>
                </motion.article>
              ))}
            </AnimatePresence>
          </Card>
        </aside>
      </div>

      <div className="mt-8 grid gap-4 grid-cols-2 lg:grid-cols-4">
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
    color: index % 5 === 0 ? 'text-emerald-400 bg-emerald-400' : index % 3 === 0 ? 'text-cyan-400 bg-cyan-400' : 'text-blue-400 bg-blue-400',
    speed: 4.8 + (index % 4) * 0.8,
  }));

  return (
    <div className="absolute inset-0 overflow-hidden bg-[radial-gradient(circle_at_center,rgba(34,211,238,.1),transparent_40rem),linear-gradient(90deg,transparent_0_14%,rgba(34,211,238,.1)_14%_15%,transparent_15%_31%,rgba(34,211,238,.08)_31%_32%,transparent_32%_48%,rgba(34,211,238,.08)_48%_49%,transparent_49%_65%,rgba(34,211,238,.1)_65%_66%,transparent_66%)] z-0">
      {videoMode && <video className="absolute inset-0 h-full w-full object-cover opacity-30 mix-blend-screen" src="/videos/highway-demo.mp4" autoPlay muted loop playsInline onError={(event) => { event.currentTarget.style.display = 'none'; }} />}
      <div className="absolute inset-y-0 left-1/2 w-[54%] -translate-x-1/2 bg-slate-900/60 shadow-2xl shadow-cyan-950/30 border-x border-white/5" />
      <div className="absolute inset-y-0 left-[36%] w-px bg-cyan-400/20" /><div className="absolute inset-y-0 left-[50%] w-px bg-cyan-400/10 border-dashed" /><div className="absolute inset-y-0 left-[64%] w-px bg-cyan-400/20" />
      <div className="absolute inset-x-0 top-0 h-full bg-[linear-gradient(to_bottom,transparent_0_28px,rgba(34,211,238,.1)_29px,transparent_31px)] bg-[length:100%_58px]" style={{ transform: `translateY(${running ? tick * 4 : tick}px)` }} />
      <div className="absolute left-1/2 top-1/2 h-80 w-80 -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-400/20 bg-cyan-400/5 shadow-[0_0_50px_rgba(34,211,238,0.1)]" />
      <div className="absolute left-1/2 top-1/2 h-[2px] w-[40rem] origin-left bg-gradient-to-r from-cyan-400 to-transparent" style={{ transform: `rotate(${tick * 15}deg)`, opacity: running ? 0.6 : 0.2 }} />
      
      {vehicles.map((vehicle) => (
        <div key={vehicle.id} className={`vehicle ${vehicle.color} ${running ? 'animate-drive' : ''} shadow-[0_0_15px_currentColor] opacity-80`} style={{ left: `${vehicle.left}%`, animationDelay: `${vehicle.delay}s`, animationDuration: `${vehicle.speed}s`, top: `${(vehicle.id * 43) % 100}%` }} />
      ))}
      
      {events.map((event) => {
        const severity = event.severity ?? classifySeverity(event.riskScore ?? calculateHighwayRisk(event));
        const color = severity === 'critical' ? 'text-red-400 border-red-500 bg-red-950/80 shadow-[0_0_20px_rgba(239,68,68,0.5)]' : severity === 'high' ? 'text-orange-400 border-orange-500 bg-orange-950/80' : severity === 'medium' ? 'text-cyan-300 border-cyan-400 bg-cyan-950/80' : 'text-emerald-400 border-emerald-500 bg-emerald-950/80';
        return (
          <div key={event.id} className={`absolute min-w-[120px] rounded-lg border-2 p-1.5 font-mono text-[10px] font-black z-10 transition-all duration-300 ${color}`} style={{ left: `${event.position.x}%`, top: `${event.position.y}%` }}>
            <div className="flex justify-between items-center border-b border-[currentColor]/30 pb-1 mb-1">
              <span>{event.trackId}</span>
              <span className="opacity-75 text-[9px]">{Math.round((event.riskScore ?? 0) * 100)}</span>
            </div>
            <div className="text-[9px] uppercase tracking-wider">{event.type.replaceAll('_', ' ')}</div>
          </div>
        );
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
  const color = tone === 'green' ? 'text-emerald-400' : tone === 'purple' ? 'text-purple-400' : 'text-cyan-400';
  return (
    <div className="rounded-xl border border-white/5 bg-slate-950/50 p-2.5 relative overflow-hidden">
      <div className="absolute top-0 right-0 w-8 h-8 bg-white/5 rounded-bl-full"></div>
      <div className={`flex items-center gap-1.5 ${color}`}>
        {icon}
        <span className="text-[9px] font-bold uppercase tracking-widest text-slate-400">{label}</span>
      </div>
      <div className="mt-1 text-lg font-black text-white tracking-tight">{value}</div>
    </div>
  );
}

function MiniKpi({ label, value }: { label: string; value: string }) { 
  return (
    <Card hoverEffect className="p-4 flex flex-col justify-center items-center text-center bg-slate-900/60 border-white/5">
      <div className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">{label}</div>
      <div className="text-2xl font-black text-white tracking-tight">{value}</div>
    </Card>
  ); 
}
