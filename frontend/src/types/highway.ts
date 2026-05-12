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
