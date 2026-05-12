import { 
  calculateHighwayRisk, 
  classifySeverity, 
  generateHighwayAlerts, 
  summarizeMissionRisk, 
  generateTimeline,
  scenarioEvents 
} from './highwayRiskEngine.js';

// ─── Constants & State ───
const CANVAS_ID = 'sim-canvas';
let canvas, ctx;
let animationId;
let currentScenario = 'normal';
let simulationActive = true;
let events = [];
let time = 0;

// DOM Elements
const alertPanel = document.getElementById('alert-panel');
const timelinePanel = document.getElementById('timeline-feed');
const riskScoreEl = document.getElementById('risk-score-value');
const riskSeverityEl = document.getElementById('risk-severity-tag');
const batteryEl = document.getElementById('battery-value');
const batteryFillEl = document.getElementById('battery-fill');
const missionSummaryEl = document.getElementById('mission-summary-text');
const scenarioButtons = document.querySelectorAll('[data-scenario]');

// ─── Initialization ───
export function initSimulation() {
  const container = document.getElementById('sim-canvas-container');
  if (!container) return;

  canvas = document.createElement('canvas');
  canvas.id = CANVAS_ID;
  ctx = canvas.getContext('2d');
  container.appendChild(canvas);

  const resize = () => {
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
  };
  window.addEventListener('resize', resize);
  resize();

  setupControls();
  startScenario('normal');
  animate();
}

function setupControls() {
  scenarioButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const scenario = btn.dataset.scenario;
      startScenario(scenario);
      scenarioButtons.forEach(b => b.classList.toggle('active', b === btn));
    });
  });

  document.getElementById('sim-toggle-play')?.addEventListener('click', () => {
    simulationActive = !simulationActive;
  });
}

function startScenario(name) {
  currentScenario = name;
  const rawEvents = scenarioEvents[name] || scenarioEvents.normal;
  
  // Clone and normalize events for simulation
  events = rawEvents.map(e => ({
    ...e,
    currentX: e.canvasX,
    currentY: e.canvasY,
    riskScore: calculateHighwayRisk(e),
    severity: classifySeverity(calculateHighwayRisk(e))
  }));

  updateDashboard();
}

// ─── Simulation Loop ───
function animate() {
  if (simulationActive) {
    update();
    draw();
  }
  animationId = requestAnimationFrame(animate);
}

function update() {
  time += 0.016; // ~60fps
  
  events.forEach(ev => {
    // Move vehicles based on velocity
    ev.currentX += ev.vx;
    ev.currentY += ev.vy;

    // Loop vehicles back
    if (ev.currentX > 1.2) ev.currentX = -0.2;
    if (ev.currentX < -0.2) ev.currentX = 1.2;
    if (ev.currentY > 1.2) ev.currentY = -0.2;
    if (ev.currentY < -0.2) ev.currentY = 1.2;
  });
}

// ─── Rendering ───
function draw() {
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  // 1. Draw Highway
  drawHighway(w, h);

  // 2. Draw Vehicles & Bounding Boxes
  events.forEach(ev => {
    const x = ev.currentX * w;
    const y = ev.currentY * h;
    const bw = ev.w * w;
    const bh = ev.h * h;

    // Draw Bounding Box
    const color = getSeverityColor(ev.severity);
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.strokeRect(x - bw/2, y - bh/2, bw, bh);

    // Box Label
    ctx.fillStyle = 'rgba(0,0,0,0.7)';
    ctx.fillRect(x - bw/2, y - bh/2 - 20, bw, 20);
    ctx.fillStyle = color;
    ctx.font = '10px Space Mono';
    ctx.fillText(`${ev.trackId} | ${ev.type}`, x - bw/2 + 5, y - bh/2 - 7);

    // Detection dots (HUD feel)
    ctx.beginPath();
    ctx.arc(x, y, 2, 0, Math.PI * 2);
    ctx.fill();
  });

  // 3. Drone Scan Overlay
  drawDroneHUD(w, h);
}

function drawHighway(w, h) {
  ctx.fillStyle = '#0f172a';
  ctx.fillRect(0, 0, w, h);

  ctx.strokeStyle = 'rgba(255,255,255,0.05)';
  ctx.lineWidth = 1;
  
  // Lane markings
  const laneCount = 4;
  for (let i = 1; i < laneCount; i++) {
    const y = (i / laneCount) * h;
    ctx.setLineDash([20, 20]);
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }
  ctx.setLineDash([]);
}

function drawDroneHUD(w, h) {
  // Scanning sweep
  const sweepX = (Math.sin(time) * 0.5 + 0.5) * w;
  const grad = ctx.createLinearGradient(sweepX - 100, 0, sweepX + 100, 0);
  grad.addColorStop(0, 'transparent');
  grad.addColorStop(0.5, 'rgba(0, 229, 255, 0.1)');
  grad.addColorStop(1, 'transparent');
  ctx.fillStyle = grad;
  ctx.fillRect(sweepX - 100, 0, 200, h);

  // HUD Corners
  ctx.strokeStyle = 'rgba(0, 229, 255, 0.4)';
  ctx.lineWidth = 2;
  const len = 20;
  // TL
  ctx.beginPath(); ctx.moveTo(10, 10+len); ctx.lineTo(10, 10); ctx.lineTo(10+len, 10); ctx.stroke();
  // TR
  ctx.beginPath(); ctx.moveTo(w-10-len, 10); ctx.lineTo(w-10, 10); ctx.lineTo(w-10, 10+len); ctx.stroke();
}

// ─── Dashboard Updates ───
function updateDashboard() {
  const summary = summarizeMissionRisk(events);
  const alerts = generateHighwayAlerts(events);
  const timeline = generateTimeline(events);

  // Update UI Elements
  if (riskScoreEl) riskScoreEl.textContent = summary.maxRisk;
  if (riskSeverityEl) {
    riskSeverityEl.textContent = classifySeverity(summary.maxRisk).toUpperCase();
    riskSeverityEl.className = `hud-tag severity-${classifySeverity(summary.maxRisk)}`;
  }

  const battery = Math.max(12, 98 - (summary.maxRisk / 5)).toFixed(1);
  if (batteryEl) batteryEl.textContent = `${battery}%`;
  if (batteryFillEl) batteryFillEl.style.width = `${battery}%`;

  if (missionSummaryEl) missionSummaryEl.textContent = summary.recommendedAction;

  // Render Alert Feed
  if (alertPanel) {
    alertPanel.innerHTML = alerts.map(a => `
      <div class="alert-item ${a.severity}">
        <div class="alert-header">
          <strong>${a.title}</strong>
          <span class="alert-score">${a.riskScore}/100</span>
        </div>
        <p class="alert-msg">${a.message}</p>
      </div>
    `).join('');
  }

  // Render Timeline
  if (timelinePanel) {
    timelinePanel.innerHTML = timeline.map(t => `
      <div class="timeline-row">
        <span class="time">${t.time}</span>
        <span class="event">${t.title}</span>
        <span class="severity ${t.severity}">${t.severity}</span>
      </div>
    `).join('');
  }
}

function getSeverityColor(sev) {
  const map = { critical: '#ef4444', high: '#f59e0b', medium: '#00e5ff', low: '#10b981' };
  return map[sev] || '#94a3b8';
}

// Start simulation on load
document.addEventListener('DOMContentLoaded', initSimulation);
window.startScenario = startScenario; // Expose for external calls if needed
