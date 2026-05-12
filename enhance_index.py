import re

with open('dashboard/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add CSS
css_additions = """
        /* --- Glitch Effect --- */
        .glitch { position: relative; display: inline-block; }
        .glitch::before, .glitch::after {
            content: attr(data-text); position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        }
        .glitch::before { left: 2px; text-shadow: -2px 0 var(--accent-green); clip: rect(24px, 550px, 90px, 0); animation: glitch-anim-2 3s infinite linear alternate-reverse; }
        .glitch::after { left: -2px; text-shadow: -2px 0 var(--accent-blue); clip: rect(85px, 550px, 140px, 0); animation: glitch-anim 2.5s infinite linear alternate-reverse; }
        @keyframes glitch-anim { 0% { clip: rect(20px, 9999px, 85px, 0); } 20% { clip: rect(54px, 9999px, 15px, 0); } 40% { clip: rect(89px, 9999px, 96px, 0); } 60% { clip: rect(10px, 9999px, 45px, 0); } 80% { clip: rect(38px, 9999px, 11px, 0); } 100% { clip: rect(77px, 9999px, 66px, 0); } }
        @keyframes glitch-anim-2 { 0% { clip: rect(12px, 9999px, 59px, 0); } 20% { clip: rect(73px, 9999px, 2px, 0); } 40% { clip: rect(31px, 9999px, 98px, 0); } 60% { clip: rect(86px, 9999px, 21px, 0); } 80% { clip: rect(44px, 9999px, 78px, 0); } 100% { clip: rect(9px, 9999px, 34px, 0); } }

        /* --- Aurora Blobs --- */
        .aurora-container { position: absolute; inset: 0; overflow: hidden; z-index: 1; pointer-events: none; opacity: 0.4; }
        .aurora-blob { position: absolute; border-radius: 50%; filter: blur(80px); animation: aurora-float 20s infinite alternate ease-in-out; }
        .blob-1 { top: -10%; left: -10%; width: 500px; height: 500px; background: rgba(0, 232, 122, 0.2); }
        .blob-2 { bottom: -20%; right: -10%; width: 600px; height: 600px; background: rgba(0, 170, 255, 0.15); animation-delay: -10s; }
        @keyframes aurora-float { 0% { transform: translate(0, 0) scale(1); } 50% { transform: translate(50px, 50px) scale(1.1); } 100% { transform: translate(-50px, 20px) scale(0.9); } }

        /* --- Scroll Arrow --- */
        .scroll-down { position: absolute; bottom: 40px; left: 50%; transform: translateX(-50%); z-index: 20; color: var(--text-muted); font-size: 1.5rem; animation: bounce 2s infinite; }
        @keyframes bounce { 0%, 20%, 50%, 80%, 100% { transform: translateY(0) translateX(-50%); } 40% { transform: translateY(-20px) translateX(-50%); } 60% { transform: translateY(-10px) translateX(-50%); } }

        /* --- Step Connecting Trail --- */
        .steps-container { position: relative; }
        .step-trail { position: absolute; top: 50%; left: 0; width: 0%; height: 2px; background: linear-gradient(90deg, var(--accent-green), var(--accent-blue)); z-index: 0; transition: width 1s ease-out; box-shadow: 0 0 15px var(--accent-green); }
        
        /* --- Architecture Arrows --- */
        .flow-arrow { width: 2px; height: 40px; background: linear-gradient(180deg, var(--accent-green), transparent); margin: 0 auto; opacity: 0; animation: flow-down 1.5s infinite; }
        @keyframes flow-down { 0% { opacity: 0; transform: translateY(-10px); } 50% { opacity: 1; } 100% { opacity: 0; transform: translateY(10px); } }

        /* --- Custom Scrollbar --- */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg-dark); }
        ::-webkit-scrollbar-thumb { background: rgba(139, 155, 180, 0.3); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--accent-blue); }

        /* --- Glowing Metric Halos --- */
        .metric-box { position: relative; transition: transform 0.3s; }
        .metric-box::before { content: ''; position: absolute; inset: -2px; background: linear-gradient(45deg, var(--accent-green), var(--accent-blue), transparent); z-index: -1; filter: blur(10px); opacity: 0; transition: opacity 0.3s; border-radius: 16px; }
        .metric-box:hover { transform: translateY(-5px); }
        .metric-box:hover::before { opacity: 0.5; }

        /* --- Footer ASCII --- */
        .ascii-art { font-family: 'JetBrains Mono', monospace; font-size: 0.55rem; color: var(--accent-green); white-space: pre; text-align: center; margin-bottom: 2rem; opacity: 0.8; line-height: 1.2; text-shadow: 0 0 10px rgba(0,232,122,0.3); }
"""
content = content.replace("</style>", css_additions + "\n    </style>")

# 2. Add Aurora blobs and glitch to Hero
hero_old = """<section id="hero">
        <div id="hero-canvas"></div>
        <div class="hero-content">"""
hero_new = """<section id="hero">
        <div id="hero-canvas"></div>
        <div class="aurora-container">
            <div class="aurora-blob blob-1"></div>
            <div class="aurora-blob blob-2"></div>
        </div>
        <div class="hero-content" style="z-index: 2;">"""
content = content.replace(hero_old, hero_new)

content = content.replace(
    '<h1 class="hero-title">AeroMind AI',
    '<h1 class="hero-title glitch" data-text="AeroMind AI">AeroMind AI'
)

# 3. Add scroll arrow to hero
scroll_arrow = """
        <a href="#how" class="scroll-down"><i class="fas fa-chevron-down"></i></a>
    </section>"""
content = content.replace("</section>", scroll_arrow, 1)

# 4. Enhance How it works
content = content.replace(
    '<div class="steps-grid"',
    '<div class="steps-container"><div class="step-trail" id="step-trail"></div><div class="steps-grid"'
)
content = content.replace('</div>\n    </section>', '</div></div>\n    </section>', 1)

# 5. Architecture arrows
content = content.replace(
    '<div class="glass-panel reveal-right" style="width: 100%; position: relative; z-index: 1;">',
    '<div class="flow-arrow"></div>\n            <div class="glass-panel reveal-right" style="width: 100%; position: relative; z-index: 1;">'
)
content = content.replace(
    '<div class="glass-panel reveal-left" style="width: 100%; position: relative; z-index: 1;">\n                <h3 style="color: #b56cff',
    '<div class="flow-arrow"></div>\n            <div class="glass-panel reveal-left" style="width: 100%; position: relative; z-index: 1;">\n                <h3 style="color: #b56cff'
)

# 6. Add Third Chart
charts_old = """<div class="charts-container">
            <div class="glass-panel reveal-left chart-wrapper">
                <h3 style="text-align: center; margin-bottom: 1rem; font-size: 1.1rem; color: var(--text-muted);">MOTA & IDF1 Progression</h3>
                <canvas id="lineChart"></canvas>
            </div>
            <div class="glass-panel reveal-right chart-wrapper">
                <h3 style="text-align: center; margin-bottom: 1rem; font-size: 1.1rem; color: var(--text-muted);">Performance vs Baseline</h3>
                <canvas id="radarChart"></canvas>
            </div>
        </div>"""
charts_new = """<div class="charts-container" style="grid-template-columns: 1fr 1fr 1fr; gap: 1.5rem;">
            <div class="glass-panel reveal-left chart-wrapper" style="height: 300px;">
                <h3 style="text-align: center; margin-bottom: 1rem; font-size: 1rem; color: var(--text-muted);">MOTA Progression</h3>
                <canvas id="lineChart"></canvas>
            </div>
            <div class="glass-panel reveal chart-wrapper" style="height: 300px;">
                <h3 style="text-align: center; margin-bottom: 1rem; font-size: 1rem; color: var(--text-muted);">Performance vs Baseline</h3>
                <canvas id="radarChart"></canvas>
            </div>
            <div class="glass-panel reveal-right chart-wrapper" style="height: 300px;">
                <h3 style="text-align: center; margin-bottom: 1rem; font-size: 1rem; color: var(--text-muted);">Latency per Module (ms)</h3>
                <canvas id="barChart"></canvas>
            </div>
        </div>"""
content = content.replace(charts_old, charts_new)

# 7. Add sparkline and SVG to HUD
hud_old = """<img id="live-stream" class="hud-stream" src="/api/stream/live" alt="Simulation stream">"""
hud_new = """<img id="live-stream" class="hud-stream" src="/api/stream/live" alt="Simulation stream">
                
                <!-- Animated SVG Overlay -->
                <svg width="100%" height="100%" style="position: absolute; top:0; left:0; z-index:17; pointer-events:none;" id="hud-svg">
                    <rect x="30%" y="40%" width="80" height="150" fill="none" stroke="var(--accent-green)" stroke-width="2" stroke-dasharray="10 5" class="trk-box" style="opacity:0; transition: opacity 0.3s;"/>
                    <text x="30%" y="38%" fill="var(--accent-green)" font-family="JetBrains Mono" font-size="10" class="trk-box" style="opacity:0;">ID:4092 (PED)</text>
                    
                    <rect x="60%" y="55%" width="120" height="80" fill="none" stroke="var(--accent-blue)" stroke-width="2" class="trk-box" style="opacity:0; transition: opacity 0.3s;"/>
                    <text x="60%" y="53%" fill="var(--accent-blue)" font-family="JetBrains Mono" font-size="10" class="trk-box" style="opacity:0;">ID:112 (VEH)</text>
                </svg>"""
content = content.replace(hud_old, hud_new)

# 8. Footer ASCII Art
footer_top_old = """<div class="footer-top">
            <div class="footer-brand-col">"""
footer_top_new = """<div class="ascii-art">
   ___                __  __ _         _      _   ___ 
  / _ \              |  \/  (_)       | |    / \ |_ _|
 / /_\ \___ _ __ ___ | |\/| |_ _ __   | |   / _ \ | | 
 |  _  / _ \ '__/ _ \| |  | | | '_ \  | |  / ___ \| | 
 | | | \__ / | | (_) | |  | | | | | | | | / /   \ \ | 
 \_| |_/___|_|  \___/\_|  |_/_|_| |_| |_|/_/     \_\_|
</div>
        <div class="footer-top">
            <div class="footer-brand-col">"""
content = content.replace(footer_top_old, footer_top_new)

# 9. JS Chart Addition
js_chart_old = """const radarCtx = document.getElementById('radarChart').getContext('2d');"""
js_chart_new = """
        const barCtx = document.getElementById('barChart').getContext('2d');
        new Chart(barCtx, {
            type: 'bar',
            data: {
                labels: ['YOLOv8', 'SAHI', 'SORT', 'ReID', 'PPO'],
                datasets: [{
                    label: 'Latency (ms)',
                    data: [12.5, 8.2, 3.4, 15.6, 5.1],
                    backgroundColor: ['rgba(0,232,122,0.6)', 'rgba(0,170,255,0.6)', 'rgba(181,108,255,0.6)', 'rgba(255,69,96,0.6)', 'rgba(255,213,0,0.6)'],
                    borderWidth: 0
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { grid: { color: 'rgba(255,255,255,0.05)' } }, x: { grid: { display: false } } } }
        });

        const radarCtx = document.getElementById('radarChart').getContext('2d');"""
content = content.replace(js_chart_old, js_chart_new)

# 10. JS Logic Addition
js_logic_old = """function setRunning(running, mock){"""
js_logic_new = """
        // Count Up Animation
        function animateValue(obj, start, end, duration) {
            let startTimestamp = null;
            const step = (timestamp) => {
                if (!startTimestamp) startTimestamp = timestamp;
                const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                obj.innerHTML = (progress * (end - start) + start).toFixed(1) + '<span style="font-size:1.5rem">%</span>';
                if (progress < 1) { window.requestAnimationFrame(step); }
            };
            window.requestAnimationFrame(step);
        }

        const metricsObserver = new IntersectionObserver((entries) => {
            if(entries[0].isIntersecting) {
                const els = document.querySelectorAll('.metric-val');
                if(!els[0].classList.contains('counted')) {
                    animateValue(els[0], 0, 83.2, 2000);
                    animateValue(els[1], 0, 78.5, 2000);
                    els[0].classList.add('counted');
                }
            }
        });
        metricsObserver.observe(document.querySelector('.metrics-grid'));

        function setRunning(running, mock){"""
content = content.replace(js_logic_old, js_logic_new)

js_hud_old = """statusPill.style.borderColor = 'var(--accent-green)';"""
js_hud_new = """statusPill.style.borderColor = 'var(--accent-green)';
                document.querySelectorAll('.trk-box').forEach(el => el.style.opacity = '1');"""
content = content.replace(js_hud_old, js_hud_new)

js_hud_old2 = """statusPill.style.borderColor = 'var(--accent-blue)';"""
js_hud_new2 = """statusPill.style.borderColor = 'var(--accent-blue)';
                document.querySelectorAll('.trk-box').forEach(el => el.style.opacity = '0');"""
content = content.replace(js_hud_old2, js_hud_new2)

with open('dashboard/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("index.html enhanced successfully.")
