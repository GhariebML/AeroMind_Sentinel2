// ─── AeroMind Sentinel · Highway Risk Engine ───────────────────────────────
// Calculates risk scores, classifies severity, generates alerts & timelines.
// Used by sentinelDemo.js for the interactive simulation.

const EVENT_WEIGHTS = {
  accident: 95,
  stopped_vehicle: 72,
  congestion: 58,
  pedestrian_on_highway: 88,
  blocked_lane: 80,
  emergency_vehicle: 45,
};

/** Calculate a 0–100 risk score for a single event. */
export function calculateHighwayRisk(event) {
  const base = EVENT_WEIGHTS[event.type] ?? 50;
  const confidenceBoost = Math.max(0, Math.min(event.confidence, 1)) * 18;
  const speedPenalty = event.type === 'stopped_vehicle' && event.speed < 5 ? 10 : 0;
  const pedestrianPenalty = event.type === 'pedestrian_on_highway' ? 8 : 0;
  const lanePenalty = event.lane?.toLowerCase().includes('shoulder') ? -8 : 4;
  return Math.max(0, Math.min(100,
    Math.round(base + confidenceBoost + speedPenalty + pedestrianPenalty + lanePenalty - 15)
  ));
}

/** Map a 0–100 score to a severity string. */
export function classifySeverity(score) {
  if (score >= 85) return 'critical';
  if (score >= 70) return 'high';
  if (score >= 45) return 'medium';
  return 'low';
}

function titleCase(value) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function recommendationFor(event, severity) {
  const map = {
    accident: 'Dispatch ambulance and traffic police; route drone to hold overhead view.',
    pedestrian_on_highway: 'Alert nearest patrol unit and broadcast driver warning for pedestrian risk.',
    blocked_lane: 'Notify road operator and recommend temporary lane closure guidance.',
    stopped_vehicle: 'Send assistance vehicle and monitor rear-end collision risk.',
    congestion: 'Increase coverage over upstream lanes and recommend traffic diversion.',
    emergency_vehicle: 'Track access corridor and support priority routing.',
  };
  return map[event.type] ?? (severity === 'critical'
    ? 'Escalate to emergency control room immediately.'
    : 'Continue monitoring and log for review.');
}

/** Generate sorted alert objects for a list of normalised events. */
export function generateHighwayAlerts(events) {
  return events
    .map(event => {
      const riskScore = event.riskScore ?? calculateHighwayRisk(event);
      const severity  = event.severity  ?? classifySeverity(riskScore);
      return {
        id: `alert-${event.id}`,
        eventId: event.id,
        title: titleCase(event.type),
        message: `Track ${event.trackId} on ${event.lane} scored ${riskScore}/100 at ${Math.round(event.confidence * 100)}% confidence.`,
        severity,
        riskScore,
        recommendation: recommendationFor(event, severity),
        timestamp: event.timestamp,
      };
    })
    .sort((a, b) => b.riskScore - a.riskScore);
}

/** Build a chronological event log for the bottom timeline strip. */
export function generateTimeline(events) {
  return [...events]
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    .map((event, i) => {
      const riskScore = event.riskScore ?? calculateHighwayRisk(event);
      const severity  = event.severity  ?? classifySeverity(riskScore);
      const ts = new Date(event.timestamp);
      const time = ts.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
      return { index: i + 1, time, title: titleCase(event.type), trackId: event.trackId, severity, riskScore };
    });
}

/** Aggregate mission-level summary across all events. */
export function summarizeMissionRisk(events) {
  if (!events.length) {
    return {
      totalEvents: 0, averageRisk: 0, maxRisk: 0,
      criticalCount: 0, highRiskCount: 0,
      recommendedAction: 'No active incidents. Continue autonomous patrol.',
    };
  }
  const scored    = events.map(e => e.riskScore ?? calculateHighwayRisk(e));
  const severities = scored.map(classifySeverity);
  const maxRisk    = Math.max(...scored);
  const averageRisk = Math.round(scored.reduce((s, v) => s + v, 0) / scored.length);
  const criticalCount  = severities.filter(s => s === 'critical').length;
  const highRiskCount  = severities.filter(s => s === 'high').length;
  return {
    totalEvents: events.length, averageRisk, maxRisk, criticalCount, highRiskCount,
    recommendedAction: criticalCount > 0
      ? 'Escalate mission to emergency mode and notify command center immediately.'
      : highRiskCount > 0
        ? 'Increase drone coverage over high-risk lanes and prepare response teams.'
        : 'Maintain monitoring and continue energy-aware patrol.',
  };
}

// ─── Scenario Event Library ───────────────────────────────────────────────
// Each event carries canvas-ready fields: canvasX/Y (0–1 fractions),
// vx/vy (velocity fractions per frame), w/h (bounding-box size fractions).

const now = () => new Date().toISOString();

export const scenarioEvents = {

  normal: [
    { id: 'n-1', type: 'emergency_vehicle', confidence: 0.72, trackId: 'PATROL-01',
      lane: 'Lane 3', speed: 110, canvasX: 0.15, canvasY: 0.25, vx: 0.0022, vy: 0, w: 0.06, h: 0.04,
      timestamp: now(), source: 'mock' },
    { id: 'n-2', type: 'emergency_vehicle', confidence: 0.68, trackId: 'TRUCK-07',
      lane: 'Lane 1', speed: 90,  canvasX: 0.05, canvasY: 0.55, vx: 0.0018, vy: 0, w: 0.08, h: 0.05,
      timestamp: now(), source: 'mock' },
    { id: 'n-3', type: 'emergency_vehicle', confidence: 0.74, trackId: 'CAR-031',
      lane: 'Lane 2', speed: 120, canvasX: 0.30, canvasY: 0.40, vx: 0.0025, vy: 0, w: 0.055, h: 0.038,
      timestamp: now(), source: 'mock' },
  ],

  stopped: [
    { id: 's-1', type: 'stopped_vehicle', confidence: 0.95, trackId: 'CAR-104',
      lane: 'Lane 2', speed: 0, canvasX: 0.52, canvasY: 0.42, vx: 0, vy: 0, w: 0.06, h: 0.04,
      timestamp: now(), source: 'mock' },
    { id: 's-2', type: 'emergency_vehicle', confidence: 0.71, trackId: 'CAR-072',
      lane: 'Lane 1', speed: 85,  canvasX: 0.12, canvasY: 0.55, vx: 0.002, vy: 0, w: 0.06, h: 0.04,
      timestamp: now(), source: 'mock' },
    { id: 's-3', type: 'emergency_vehicle', confidence: 0.65, trackId: 'TRUCK-12',
      lane: 'Lane 3', speed: 75, canvasX: 0.22, canvasY: 0.26, vx: 0.0018, vy: 0, w: 0.08, h: 0.05,
      timestamp: now(), source: 'mock' },
  ],

  accident: [
    { id: 'a-1', type: 'accident', confidence: 0.93, trackId: 'INC-219',
      lane: 'Lane 3', speed: 0, canvasX: 0.58, canvasY: 0.27, vx: 0, vy: 0, w: 0.09, h: 0.06,
      timestamp: now(), source: 'mock' },
    { id: 'a-2', type: 'blocked_lane', confidence: 0.88, trackId: 'OBJ-510',
      lane: 'Lane 3', speed: 0, canvasX: 0.64, canvasY: 0.28, vx: 0, vy: 0, w: 0.07, h: 0.045,
      timestamp: now(), source: 'mock' },
    { id: 'a-3', type: 'stopped_vehicle', confidence: 0.82, trackId: 'CAR-087',
      lane: 'Lane 2', speed: 0, canvasX: 0.55, canvasY: 0.42, vx: 0, vy: 0, w: 0.06, h: 0.04,
      timestamp: now(), source: 'mock' },
    { id: 'a-4', type: 'congestion', confidence: 0.79, trackId: 'ZONE-03',
      lane: 'Lane 1', speed: 18, canvasX: 0.38, canvasY: 0.57, vx: 0.0005, vy: 0, w: 0.14, h: 0.06,
      timestamp: now(), source: 'mock' },
  ],

  congestion: [
    { id: 'c-1', type: 'congestion', confidence: 0.91, trackId: 'ZONE-07',
      lane: 'All lanes', speed: 14, canvasX: 0.46, canvasY: 0.38, vx: 0.0004, vy: 0, w: 0.18, h: 0.22,
      timestamp: now(), source: 'mock' },
    { id: 'c-2', type: 'stopped_vehicle', confidence: 0.77, trackId: 'CAR-201',
      lane: 'Lane 2', speed: 0, canvasX: 0.48, canvasY: 0.42, vx: 0, vy: 0, w: 0.06, h: 0.04,
      timestamp: now(), source: 'mock' },
    { id: 'c-3', type: 'emergency_vehicle', confidence: 0.60, trackId: 'VAN-015',
      lane: 'Lane 3', speed: 22, canvasX: 0.55, canvasY: 0.27, vx: 0.0005, vy: 0, w: 0.065, h: 0.04,
      timestamp: now(), source: 'mock' },
  ],

  pedestrian: [
    { id: 'p-1', type: 'pedestrian_on_highway', confidence: 0.88, trackId: 'PED-022',
      lane: 'Shoulder / Lane 1', speed: 3, canvasX: 0.46, canvasY: 0.72, vx: 0.0003, vy: -0.0002, w: 0.025, h: 0.045,
      timestamp: now(), source: 'mock' },
    { id: 'p-2', type: 'emergency_vehicle', confidence: 0.73, trackId: 'CAR-119',
      lane: 'Lane 2', speed: 95, canvasX: 0.12, canvasY: 0.42, vx: 0.002, vy: 0, w: 0.06, h: 0.04,
      timestamp: now(), source: 'mock' },
  ],

  blocked: [
    { id: 'b-1', type: 'blocked_lane', confidence: 0.92, trackId: 'OBJ-510',
      lane: 'Lane 1', speed: 0, canvasX: 0.35, canvasY: 0.57, vx: 0, vy: 0, w: 0.10, h: 0.06,
      timestamp: now(), source: 'mock' },
    { id: 'b-2', type: 'stopped_vehicle', confidence: 0.85, trackId: 'TRK-044',
      lane: 'Lane 1', speed: 0, canvasX: 0.28, canvasY: 0.57, vx: 0, vy: 0, w: 0.09, h: 0.055,
      timestamp: now(), source: 'mock' },
    { id: 'b-3', type: 'congestion', confidence: 0.76, trackId: 'ZONE-02',
      lane: 'Lane 1', speed: 8, canvasX: 0.18, canvasY: 0.55, vx: 0.0003, vy: 0, w: 0.14, h: 0.07,
      timestamp: now(), source: 'mock' },
  ],

  emergency: [
    { id: 'e-1', type: 'accident', confidence: 0.97, trackId: 'INC-911',
      lane: 'Lane 2', speed: 0, canvasX: 0.50, canvasY: 0.40, vx: 0, vy: 0, w: 0.10, h: 0.07,
      timestamp: now(), source: 'mock' },
    { id: 'e-2', type: 'pedestrian_on_highway', confidence: 0.94, trackId: 'PED-009',
      lane: 'Lane 1', speed: 2, canvasX: 0.44, canvasY: 0.60, vx: 0.0002, vy: -0.0001, w: 0.025, h: 0.045,
      timestamp: now(), source: 'mock' },
    { id: 'e-3', type: 'blocked_lane', confidence: 0.90, trackId: 'OBJ-901',
      lane: 'Lane 2', speed: 0, canvasX: 0.57, canvasY: 0.38, vx: 0, vy: 0, w: 0.10, h: 0.06,
      timestamp: now(), source: 'mock' },
    { id: 'e-4', type: 'congestion', confidence: 0.88, trackId: 'ZONE-10',
      lane: 'All lanes', speed: 6, canvasX: 0.30, canvasY: 0.45, vx: 0.0003, vy: 0, w: 0.20, h: 0.26,
      timestamp: now(), source: 'mock' },
    { id: 'e-5', type: 'emergency_vehicle', confidence: 0.99, trackId: 'AMB-001',
      lane: 'Shoulder', speed: 140, canvasX: 0.02, canvasY: 0.70, vx: 0.003, vy: 0, w: 0.07, h: 0.045,
      timestamp: now(), source: 'mock' },
  ],
};
