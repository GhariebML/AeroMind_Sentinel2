import { calculateHighwayRisk, classifySeverity, generateHighwayAlerts, summarizeMissionRisk, scenarioEvents, HighwayEvent } from './highwayRiskEngine.js';

const scenarioButtons = document.querySelectorAll<HTMLButtonElement>('[data-scenario]');
const alertPanel = document.getElementById('alert-panel');
const riskScore = document.getElementById('risk-score');
const riskSeverity = document.getElementById('risk-severity');
const recommendation = document.getElementById('response-recommendation');
const battery = document.getElementById('battery-level');
const missionMode = document.getElementById('mission-mode');
const liveFeed = document.getElementById('live-feed');
const missionSummary = document.getElementById('mission-summary');
const feedSource = document.getElementById('feed-source');
const highwayVideo = document.getElementById('highway-video') as HTMLImageElement | null;

function createBox(event: HighwayEvent): HTMLDivElement {
  const box = document.createElement('div');
  const score = event.riskScore ?? calculateHighwayRisk(event);
  const severity = event.severity ?? classifySeverity(score);
  box.className = `tracking-box ${severity}`;
  box.style.left = `${event.position.x}%`;
  box.style.top = `${event.position.y}%`;
  box.innerHTML = `<span>${event.trackId}</span><strong>${event.type.replaceAll('_', ' ')}</strong>`;
  return box;
}

function normalizeEvents(events: HighwayEvent[]): HighwayEvent[] {
  return events.map((event) => {
    const riskScore = event.riskScore ?? calculateHighwayRisk(event);
    return { ...event, timestamp: event.timestamp ?? new Date().toISOString(), riskScore, severity: event.severity ?? classifySeverity(riskScore) };
  });
}

function renderEvents(events: HighwayEvent[], sourceLabel = 'Scenario simulation') {
  if (!liveFeed || !riskScore || !riskSeverity || !recommendation || !missionMode || !battery || !missionSummary || !alertPanel) return;
  const normalized = normalizeEvents(events);
  const alerts = generateHighwayAlerts(normalized);
  const summary = summarizeMissionRisk(normalized);

  liveFeed.querySelectorAll('.tracking-box').forEach((box) => box.remove());
  normalized.forEach((event) => liveFeed.appendChild(createBox(event)));

  riskScore.textContent = `${(summary.maxRisk).toFixed(0)}`;
  const topSeverity = classifySeverity(summary.maxRisk);
  riskSeverity.textContent = topSeverity.toUpperCase();
  riskSeverity.className = `severity-pill ${topSeverity}`;
  recommendation.textContent = alerts[0]?.recommendation ?? summary.recommendedAction;
  missionMode.textContent = summary.criticalCount > 0 ? 'Emergency Response' : summary.highRiskCount > 0 ? 'Risk Patrol' : 'Energy-Aware Patrol';
  battery.textContent = `${Math.max(54, 91 - (summary.maxRisk) / 3).toFixed(0)}%`;
  missionSummary.textContent = `${summary.totalEvents} event(s), avg risk ${(summary.averageRisk).toFixed(0)}/100. ${summary.recommendedAction}`;
  if (feedSource) feedSource.textContent = sourceLabel;

  alertPanel.innerHTML = alerts.map((alert) => `
    <article class="alert-card ${alert.severity}">
      <div><strong>${alert.title}</strong><span>${alert.severity.toUpperCase()} · ${alert.riskScore}/100</span></div>
      <p>${alert.message}</p>
      <small>${alert.recommendation}</small>
    </article>
  `).join('') || '<p class="muted">No active emergency alerts.</p>';
}

function renderScenario(name: string) {
  const sourceEvents = scenarioEvents[name] ?? scenarioEvents.normal;
  renderEvents(sourceEvents, `Scenario: ${name.replaceAll('_', ' ')}`);
  scenarioButtons.forEach((button) => button.classList.toggle('active', button.dataset.scenario === name));
}

async function loadLiveModelEvents(): Promise<boolean> {
  try {
    const response = await fetch('/api/highway/events', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    const events = Array.isArray(payload) ? payload : payload.events;
    if (events?.length) {
      renderEvents(events, payload.source === 'live_model' ? 'Live model output: experiments/results/highway_events.json' : 'Built-in demo fallback');
      scenarioButtons.forEach((button) => button.classList.remove('active'));
      return true;
    }
  } catch (error) {
    console.warn('Live highway events unavailable; using scenario simulation.', error);
  }
  return false;
}

let livePollInterval: ReturnType<typeof setInterval> | null = null;



async function startSimulation(scenario: string) {
  const toggleEl = document.getElementById('airsim-toggle') as HTMLInputElement | null;
  const isLive = toggleEl?.checked ?? false;
  const mjpegStream = document.getElementById('mjpeg-stream') as HTMLImageElement | null;
  const mockBg = document.getElementById('mock-bg');
  
  if (livePollInterval) clearInterval(livePollInterval);

  if (isLive) {
    if (feedSource) feedSource.textContent = "Connecting to Live Inference...";
    if (mjpegStream) mjpegStream.style.display = 'none';
    if (highwayVideo) highwayVideo.style.display = 'block';
    if (mockBg) mockBg.style.display = 'none';

    try {
      livePollInterval = setInterval(async () => {
          await loadLiveModelEvents();
          if (feedSource) feedSource.textContent = `Live Inference feed: ${scenario}`;
      }, 2000);
    } catch (e) {
      console.error(e);
      if (feedSource) feedSource.textContent = "Failed to connect to Inference.";
    }
  } else {
    if (mjpegStream) mjpegStream.style.display = 'none';
    if (highwayVideo) highwayVideo.style.display = 'block';
    if (mockBg) mockBg.style.display = 'none'; // We use video instead of mockBg now
    renderScenario(scenario);
  }
}

scenarioButtons.forEach((button) => {
  button.addEventListener('click', () => {
      const scenario = button.dataset.scenario;
      if(scenario) startSimulation(scenario);
  });
});

loadLiveModelEvents().then((loaded) => {
  if (!loaded) renderScenario('accident');
});
