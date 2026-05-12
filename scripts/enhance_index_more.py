import re

with open('dashboard/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add Animated radar sweep circles in Hero
css_radar = """
        /* --- Radar Sweep --- */
        .radar-container {
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            width: 800px; height: 800px; border-radius: 50%; border: 1px solid rgba(0, 232, 122, 0.1);
            pointer-events: none; z-index: 1;
        }
        .radar-container::before {
            content: ''; position: absolute; inset: 0; border-radius: 50%;
            border: 1px solid rgba(0, 170, 255, 0.1); transform: scale(0.6);
        }
        .radar-sweep {
            position: absolute; top: 0; left: 50%; width: 50%; height: 50%;
            background: linear-gradient(90deg, rgba(0,232,122,0), rgba(0,232,122,0.3));
            transform-origin: 0% 100%; border-right: 2px solid var(--accent-green);
            border-radius: 0 100% 0 0; animation: sweep 4s infinite linear;
        }
        @keyframes sweep { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
"""
if "/* --- Radar Sweep --- */" not in content:
    content = content.replace("</style>", css_radar + "\n    </style>")

if '<div class="radar-container">' not in content:
    content = content.replace(
        '<div id="hero-canvas"></div>',
        '<div id="hero-canvas"></div>\n        <div class="radar-container"><div class="radar-sweep"></div></div>'
    )

# 2. Technology Cards Glowing border animation, performance bars on card backs
css_tech_glow = """
        /* --- Enhanced Tech Card Glow & Perf --- */
        .tech-card:hover .tech-front {
            border-color: rgba(0,170,255,0.8);
            box-shadow: 0 0 30px rgba(0,170,255,0.4);
            animation: pulse-glow 1.5s infinite alternate;
        }
        @keyframes pulse-glow {
            from { box-shadow: 0 0 10px rgba(0,170,255,0.2); }
            to { box-shadow: 0 0 40px rgba(0,170,255,0.6); }
        }
        .perf-bar-bg { width: 100%; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; margin-top: 10px; overflow: hidden; }
        .perf-bar-fill { height: 100%; background: var(--accent-green); width: 0; transition: width 1s ease-out 0.3s; }
        .tech-card:hover .perf-bar-fill { width: var(--fill-pct); }
"""
if "/* --- Enhanced Tech Card Glow & Perf --- */" not in content:
    content = content.replace("</style>", css_tech_glow + "\n    </style>")

if "perf-bar-bg" not in content:
    content = content.replace(
        '<div class="spec">Params: 25.9M | Conf: 0.5</div>',
        '<div class="spec">Params: 25.9M | Conf: 0.5</div>\n                        <div class="perf-bar-bg"><div class="perf-bar-fill" style="--fill-pct: 95%;"></div></div>'
    )
    content = content.replace(
        '<div class="spec">Max Age: 30 | Min Hits: 3</div>',
        '<div class="spec">Max Age: 30 | Min Hits: 3</div>\n                        <div class="perf-bar-bg"><div class="perf-bar-fill" style="--fill-pct: 88%;"></div></div>'
    )
    content = content.replace(
        '<div class="spec">Params: ~1.0M | Dist: Cosine</div>',
        '<div class="spec">Params: ~1.0M | Dist: Cosine</div>\n                        <div class="perf-bar-bg"><div class="perf-bar-fill" style="--fill-pct: 92%;"></div></div>'
    )
    content = content.replace(
        '<div class="spec">Steps: 3M | Net: [256,256]</div>',
        '<div class="spec">Steps: 3M | Net: [256,256]</div>\n                        <div class="perf-bar-bg"><div class="perf-bar-fill" style="--fill-pct: 98%;"></div></div>'
    )

with open('dashboard/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("done")
