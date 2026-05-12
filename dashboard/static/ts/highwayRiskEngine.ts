export type HighwayEventType =
  | "accident"
  | "stopped_vehicle"
  | "congestion"
  | "pedestrian_on_highway"
  | "blocked_lane"
  | "emergency_vehicle";

export type Severity = "low" | "medium" | "high" | "critical";

export interface HighwayPosition {
  x: number;
  y: number;
  lat?: number;
  lng?: number;
}

export interface HighwayEvent {
  id: string;
  type: HighwayEventType;
  confidence: number;
  trackId: string;
  position: HighwayPosition;
  speed: number;
  lane: string;
  timestamp: string;
  riskScore?: number;
  severity?: Severity;
  source?: "mock" | "live_model" | "uploaded_asset";
}

export interface HighwayAlert {
  id: string;
  eventId: string;
  title: string;
  message: string;
  severity: Severity;
  riskScore: number;
  recommendation: string;
  timestamp: string;
}

export interface MissionRiskSummary {
  totalEvents: number;
  averageRisk: number;
  maxRisk: number;
  criticalCount: number;
  highRiskCount: number;
  recommendedAction: string;
}

const EVENT_WEIGHTS: Record<HighwayEventType, number> = {
  accident: 95,
  stopped_vehicle: 72,
  congestion: 58,
  pedestrian_on_highway: 88,
  blocked_lane: 80,
  emergency_vehicle: 45,
};

export function calculateHighwayRisk(event: HighwayEvent): number {
  const base = EVENT_WEIGHTS[event.type];
  const confidenceBoost = Math.max(0, Math.min(event.confidence, 1)) * 18;
  const speedPenalty = event.type === "stopped_vehicle" && event.speed < 5 ? 10 : 0;
  const pedestrianPenalty = event.type === "pedestrian_on_highway" ? 8 : 0;
  const lanePenalty = event.lane.toLowerCase().includes("shoulder") ? -8 : 4;
  return Math.max(0, Math.min(100, Math.round(base + confidenceBoost + speedPenalty + pedestrianPenalty + lanePenalty - 15)));
}

export function classifySeverity(score: number): Severity {
  if (score >= 85) return "critical";
  if (score >= 70) return "high";
  if (score >= 45) return "medium";
  return "low";
}

function titleCase(value: string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

function recommendationFor(event: HighwayEvent, severity: Severity): string {
  if (event.type === "accident") return "Dispatch ambulance and traffic police; route drone to hold overhead view.";
  if (event.type === "pedestrian_on_highway") return "Alert nearest patrol unit and broadcast driver warning for pedestrian risk.";
  if (event.type === "blocked_lane") return "Notify road operator and recommend temporary lane closure guidance.";
  if (event.type === "stopped_vehicle") return "Send assistance vehicle and monitor rear-end collision risk.";
  if (event.type === "congestion") return "Increase coverage over upstream lanes and recommend traffic diversion.";
  if (event.type === "emergency_vehicle") return "Track access corridor and support priority routing.";
  return severity === "critical" ? "Escalate to emergency control room." : "Continue monitoring.";
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
        message: `Track ${event.trackId} on ${event.lane} scored ${riskScore}/100 risk at ${Math.round(event.confidence * 100)}% confidence.`,
        severity,
        riskScore,
        recommendation: recommendationFor(event, severity),
        timestamp: event.timestamp,
      };
    })
    .sort((first, second) => second.riskScore - first.riskScore);
}

export const scenarioEvents: Record<string, HighwayEvent[]> = {
  normal: [
    { id: "evt-normal-1", type: "emergency_vehicle", confidence: 0.62, trackId: "PATROL-01", position: { x: 18, y: 50 }, speed: 82, lane: "Lane 3", timestamp: new Date().toISOString(), source: "mock" },
  ],
  stopped: [
    { id: "evt-stop-1", type: "stopped_vehicle", confidence: 0.93, trackId: "CAR-104", position: { x: 34, y: 62 }, speed: 0, lane: "Lane 2", timestamp: new Date().toISOString(), source: "mock" },
  ],
  accident: [
    { id: "evt-acc-1", type: "accident", confidence: 0.9, trackId: "INC-219", position: { x: 58, y: 48 }, speed: 0, lane: "Lane 3", timestamp: new Date().toISOString(), source: "mock" },
    { id: "evt-acc-2", type: "blocked_lane", confidence: 0.86, trackId: "OBJ-510", position: { x: 61, y: 50 }, speed: 0, lane: "Lane 3", timestamp: new Date().toISOString(), source: "mock" },
  ],
  congestion: [
    { id: "evt-con-1", type: "congestion", confidence: 0.87, trackId: "ZONE-07", position: { x: 72, y: 43 }, speed: 12, lane: "All lanes", timestamp: new Date().toISOString(), source: "mock" },
  ],
  pedestrian: [
    { id: "evt-ped-1", type: "pedestrian_on_highway", confidence: 0.82, trackId: "PED-022", position: { x: 46, y: 71 }, speed: 4, lane: "Shoulder / Lane 1", timestamp: new Date().toISOString(), source: "mock" },
  ],
  blocked: [
    { id: "evt-block-1", type: "blocked_lane", confidence: 0.88, trackId: "OBJ-510", position: { x: 25, y: 55 }, speed: 0, lane: "Lane 1", timestamp: new Date().toISOString(), source: "mock" },
  ],
};

export function summarizeMissionRisk(events: HighwayEvent[]): MissionRiskSummary {
  if (!events.length) {
    return {
      totalEvents: 0,
      averageRisk: 0,
      maxRisk: 0,
      criticalCount: 0,
      highRiskCount: 0,
      recommendedAction: "No active incidents. Continue autonomous patrol.",
    };
  }

  const scored = events.map((event) => event.riskScore ?? calculateHighwayRisk(event));
  const severities = scored.map(classifySeverity);
  const maxRisk = Math.max(...scored);
  const averageRisk = Math.round(scored.reduce((sum, score) => sum + score, 0) / scored.length);
  const criticalCount = severities.filter((severity) => severity === "critical").length;
  const highRiskCount = severities.filter((severity) => severity === "high").length;

  return {
    totalEvents: events.length,
    averageRisk,
    maxRisk,
    criticalCount,
    highRiskCount,
    recommendedAction:
      criticalCount > 0
        ? "Escalate mission to emergency mode and notify command center immediately."
        : highRiskCount > 0
          ? "Increase drone coverage over high-risk lanes and prepare response teams."
          : "Maintain monitoring and continue energy-aware patrol.",
  };
}
