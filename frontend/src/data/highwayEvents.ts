import type { ScenarioDefinition } from '../types/highway';

const now = () => new Date().toISOString();

export const scenarios: ScenarioDefinition[] = [
  {
    id: 'normal',
    label: 'Normal Traffic',
    headline: 'Stable patrol over Cairo-Alex highway segment',
    description: 'Traffic is moving normally. Sentinel maintains low-energy coverage and watches for anomalies.',
    missionMode: 'Energy-Aware Patrol',
    events: [
      { id: 'evt-normal-1', type: 'emergency_vehicle', confidence: 0.58, trackId: 'PATROL-01', position: { x: 18, y: 58 }, speed: 84, lane: 'Lane 3', timestamp: now() },
    ],
  },
  {
    id: 'stopped',
    label: 'Stopped Vehicle',
    headline: 'Stopped sedan detected in active lane',
    description: 'A vehicle has stopped with near-zero speed in Lane 2, creating rear-end collision risk.',
    missionMode: 'Risk Patrol',
    events: [
      { id: 'evt-stop-1', type: 'stopped_vehicle', confidence: 0.93, trackId: 'CAR-104', position: { x: 34, y: 62 }, speed: 0, lane: 'Lane 2', timestamp: now() },
    ],
  },
  {
    id: 'accident',
    label: 'Accident Detected',
    headline: 'Critical crash cluster detected',
    description: 'Two vehicles and debris create a blocked lane. Sentinel escalates to emergency response mode.',
    missionMode: 'Emergency Response Mode',
    events: [
      { id: 'evt-acc-1', type: 'accident', confidence: 0.91, trackId: 'INC-219', position: { x: 58, y: 48 }, speed: 0, lane: 'Lane 3', timestamp: now() },
      { id: 'evt-acc-2', type: 'blocked_lane', confidence: 0.86, trackId: 'OBJ-510', position: { x: 63, y: 52 }, speed: 0, lane: 'Lane 3', timestamp: now() },
    ],
  },
  {
    id: 'congestion',
    label: 'Congestion Building',
    headline: 'Traffic density wave forming upstream',
    description: 'Average lane speed has dropped sharply and vehicle density is increasing across all lanes.',
    missionMode: 'Congestion Analysis',
    events: [
      { id: 'evt-con-1', type: 'congestion', confidence: 0.87, trackId: 'ZONE-07', position: { x: 72, y: 43 }, speed: 12, lane: 'All lanes', timestamp: now() },
    ],
  },
  {
    id: 'pedestrian',
    label: 'Pedestrian on Highway',
    headline: 'Pedestrian risk on shoulder and Lane 1 boundary',
    description: 'A pedestrian is detected near active traffic. Sentinel recommends immediate patrol response.',
    missionMode: 'Emergency Response Mode',
    events: [
      { id: 'evt-ped-1', type: 'pedestrian_on_highway', confidence: 0.84, trackId: 'PED-022', position: { x: 46, y: 71 }, speed: 4, lane: 'Shoulder / Lane 1', timestamp: now() },
    ],
  },
  {
    id: 'blocked',
    label: 'Blocked Lane',
    headline: 'Debris object blocking Lane 1',
    description: 'A static object is detected in Lane 1. Road operator notification is recommended.',
    missionMode: 'Risk Patrol',
    events: [
      { id: 'evt-block-1', type: 'blocked_lane', confidence: 0.89, trackId: 'OBJ-510', position: { x: 25, y: 55 }, speed: 0, lane: 'Lane 1', timestamp: now() },
    ],
  },
  {
    id: 'emergency',
    label: 'Emergency Response Mode',
    headline: 'Ambulance corridor support active',
    description: 'Sentinel tracks emergency vehicle access while maintaining overhead incident awareness.',
    missionMode: 'Emergency Response Mode',
    events: [
      { id: 'evt-emg-1', type: 'accident', confidence: 0.89, trackId: 'INC-219', position: { x: 54, y: 47 }, speed: 0, lane: 'Lane 3', timestamp: now() },
      { id: 'evt-emg-2', type: 'emergency_vehicle', confidence: 0.94, trackId: 'AMB-14', position: { x: 22, y: 66 }, speed: 96, lane: 'Lane 1', timestamp: now() },
    ],
  },
];

export const scenarioMap = Object.fromEntries(scenarios.map((scenario) => [scenario.id, scenario]));
