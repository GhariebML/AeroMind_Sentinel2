export const coreMetrics = [
  { label: 'MOTA', value: 83.2, suffix: '%', caption: 'multi-object tracking accuracy' },
  { label: 'IDF1', value: 78.5, suffix: '%', caption: 'identity consistency score' },
  { label: 'ID Switches / 1k', value: 11, suffix: '', caption: 'lower is better' },
  { label: 'Energy Saved', value: 34.8, suffix: '%', caption: 'PPO route optimization' },
  { label: 'Mission Duration', value: 72, suffix: '%', prefix: '+', caption: 'coverage extension' },
  { label: 'Latency', value: 45, suffix: 'ms', prefix: '~', caption: 'near real-time alerts' },
];

export const sentinelKpis = [
  { label: 'Incident Detection Time', value: '<15s', score: 88 },
  { label: 'Alert Generation Latency', value: '~45ms', score: 92 },
  { label: 'High-Risk Zone Coverage', value: '87%', score: 87 },
  { label: 'Congestion Confidence', value: '84%', score: 84 },
  { label: 'Response Support Score', value: '91/100', score: 91 },
  { label: 'Risk Prioritization Accuracy', value: '89%', score: 89 },
];
