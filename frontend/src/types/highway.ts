export type HighwayEventType =
  | 'accident'
  | 'stopped_vehicle'
  | 'congestion'
  | 'pedestrian_on_highway'
  | 'blocked_lane'
  | 'emergency_vehicle';

export type Severity = 'low' | 'medium' | 'high' | 'critical';

export interface HighwayPosition {
  x: number;
  y: number;
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
  recommendedAction?: string;
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

export interface DroneTelemetry {
  battery: number;
  altitude: number;
  speed: number;
  coverage: number;
  latency: number;
  mode: string;
}

export interface ScenarioDefinition {
  id: string;
  label: string;
  headline: string;
  description: string;
  missionMode: string;
  events: HighwayEvent[];
}
