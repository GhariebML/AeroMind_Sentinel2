/**
 * AeroMind Sentinel · Cyber Highway Background
 * Custom Canvas 2D engine for high-performance 3D perspective animation.
 */

export function initThreeJS() {
  const container = document.getElementById('hero-3d-canvas');
  if (!container) return;

  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  container.appendChild(canvas);

  let w, h;
  const resize = () => {
    w = canvas.width = container.clientWidth;
    h = canvas.height = container.clientHeight;
  };
  window.addEventListener('resize', resize);
  resize();

  // ─── Simulation State ───
  const particles = [];
  const lines = [];
  const particleCount = 100;
  const lineCount = 12;

  // Initialize particles
  for (let i = 0; i < particleCount; i++) {
    particles.push({
      x: Math.random() * w,
      y: Math.random() * h,
      size: Math.random() * 2,
      speed: Math.random() * 0.5 + 0.2,
      opacity: Math.random() * 0.5 + 0.2
    });
  }

  // Initialize perspective lines (Highway lanes)
  for (let i = 0; i < lineCount; i++) {
    lines.push({
      angle: (i / (lineCount - 1)) * Math.PI - Math.PI,
      offset: Math.random() * 100
    });
  }

  let time = 0;

  function draw() {
    ctx.clearRect(0, 0, w, h);
    time += 0.01;

    // ─── Draw Perspective Grid ───
    ctx.strokeStyle = 'rgba(0, 229, 255, 0.05)';
    ctx.lineWidth = 1;
    
    const vanishingPoint = { x: w / 2, y: h * 0.4 };
    
    // Vertical Perspective Lines
    for (let i = -10; i <= 10; i++) {
      ctx.beginPath();
      ctx.moveTo(vanishingPoint.x, vanishingPoint.y);
      ctx.lineTo(w / 2 + i * (w / 5), h);
      ctx.stroke();
    }

    // Horizontal moving lines (motion feel)
    ctx.strokeStyle = 'rgba(0, 229, 255, 0.1)';
    for (let i = 0; i < 10; i++) {
      const yPos = vanishingPoint.y + (( (i + (time * 2)) % 10 ) / 10) * (h - vanishingPoint.y);
      const width = ((yPos - vanishingPoint.y) / (h - vanishingPoint.y)) * w * 2;
      ctx.beginPath();
      ctx.moveTo(w/2 - width/2, yPos);
      ctx.lineTo(w/2 + width/2, yPos);
      ctx.stroke();
    }

    // ─── Draw Floating Particles ───
    particles.forEach(p => {
      ctx.fillStyle = `rgba(0, 229, 255, ${p.opacity})`;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fill();

      p.y -= p.speed;
      if (p.y < 0) {
        p.y = h;
        p.x = Math.random() * w;
      }
    });

    // ─── Scan Line Effect ───
    const scanY = (Math.sin(time * 0.5) * 0.5 + 0.5) * h;
    const gradient = ctx.createLinearGradient(0, scanY - 50, 0, scanY + 50);
    gradient.addColorStop(0, 'transparent');
    gradient.addColorStop(0.5, 'rgba(0, 229, 255, 0.1)');
    gradient.addColorStop(1, 'transparent');
    
    ctx.fillStyle = gradient;
    ctx.fillRect(0, scanY - 50, w, 100);

    // ─── Radar Pulse ───
    const pulseRadius = (time % 4) * (w / 4);
    ctx.strokeStyle = `rgba(0, 229, 255, ${1 - (time % 4) / 4})`;
    ctx.beginPath();
    ctx.arc(w/2, h/2, pulseRadius, 0, Math.PI * 2);
    ctx.stroke();

    requestAnimationFrame(draw);
  }

  draw();
}
