import type { HighwayAlert, HighwayEvent, HighwayEventType, MissionRiskSummary, Severity } from '../types/highway';

const EVENT_WEIGHTS: Record<HighwayEventType, number> = {
  accident: 0.92,
  stopped_vehicle: 0.68,
  congestion: 0.52,
  pedestrian_on_highway: 0.86,
  blocked_lane: 0.76,
  emergency_vehicle: 0.42,
};

const ACTIONS: Record<HighwayEventType, string> = {
  accident: 'Dispatch ambulance and traffic police; keep drone locked overhead for live evidence.',
  stopped_vehicle: 'Send roadside assistance and monitor rear-end collision risk in the same lane.',
  congestion: 'Expand scan radius upstream and recommend traffic diversion to control room.',
  pedestrian_on_highway: 'Escalate to patrol unit and broadcast driver warning for pedestrian risk.',
  blocked_lane: 'Notify road operator, mark lane closure, and inspect debris from aerial view.',
  emergency_vehicle: 'Track emergency vehicle corridor and support priority routing.',
};

export function calculateHighwayRisk(event: HighwayEvent): number {
  const base = EVENT_WEIGHTS[event.type];
  const confidence = clamp01(event.confidence);
  const stoppedBoost = event.type === 'stopped_vehicle' && event.speed < 8 ? 0.12 : 0;
  const pedestrianBoost = event.type === 'pedestrian_on_highway' ? 0.09 : 0;
  const laneBoost = event.lane.toLowerCase().includes('shoulder') ? -0.04 : 0.05;
  const speedBoost = event.speed > 90 && event.type !== 'emergency_vehicle' ? 0.04 : 0;
  return clamp01(base * 0.72 + confidence * 0.22 + stoppedBoost + pedestrianBoost + laneBoost + speedBoost);
}

export function classifySeverity(score: number): Severity {
  if (score <= 0.3) return 'low';
  if (score <= 0.6) return 'medium';
  if (score <= 0.85) return 'high';
  return 'critical';
}

export function generateHighwayAlerts(events: HighwayEvent[]): HighwayAlert[] {
  return events
    .map((event) => {
      const riskScore = event.riskScore ?? calculateHighwayRisk(event);
      const severity = event.severity ?? classifySeverity(riskScore);
      return {
        id: `alert-${event.id}`,
        eventId: event.id,
        title: titleCase(event.type),
        message: `${event.trackId} · ${event.lane} · ${(event.confidence * 100).toFixed(0)}% confidence · ${(riskScore * 100).toFixed(0)}/100 risk`,
        severity,
        riskScore,
        recommendation: event.recommendedAction ?? ACTIONS[event.type],
        timestamp: event.timestamp,
      };
    })
    .sort((a, b) => b.riskScore - a.riskScore);
}

export function summarizeMissionRisk(events: HighwayEvent[]): MissionRiskSummary {
  if (!events.length) {
    return { totalEvents: 0, averageRisk: 0, maxRisk: 0, criticalCount: 0, highRiskCount: 0, recommendedAction: 'No active incidents. Continue energy-aware patrol.' };
  }
  const risks = events.map((event) => event.riskScore ?? calculateHighwayRisk(event));
  const severities = risks.map(classifySeverity);
  const maxRisk = Math.max(...risks);
  const averageRisk = risks.reduce((sum, risk) => sum + risk, 0) / risks.length;
  const criticalCount = severities.filter((severity) => severity === 'critical').length;
  const highRiskCount = severities.filter((severity) => severity === 'high').length;
  return {
    totalEvents: events.length,
    averageRisk,
    maxRisk,
    criticalCount,
    highRiskCount,
    recommendedAction: criticalCount > 0
      ? 'Emergency mode: notify command center, dispatch responders, and keep drone centered on the incident.'
      : highRiskCount > 0
        ? 'Risk patrol: increase scan density and prepare responders for escalation.'
        : 'Normal monitoring: continue patrol and preserve battery.',
  };
}

function clamp01(value: number): number {
  return Math.max(0, Math.min(1, value));
}

function titleCase(value: string): string {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}
