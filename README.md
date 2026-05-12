# AeroMind Sentinel

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](.github/workflows/baseline_eval.yml)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](Dockerfile)

## AI-Powered Smart Highway Monitoring & Emergency Response System

AeroMind Sentinel is a market-ready highway monitoring product built on the **AeroMind AI** autonomous drone surveillance platform. It uses drone-based AI perception, multi-object tracking, reinforcement learning navigation, and a highway risk engine to detect accidents, stopped vehicles, congestion, pedestrians on highways, blocked lanes, and emergency risk zones in real time.

> **Target:** AI for Egypt Real Problems Hackathon · **Domain:** Smart highways, emergency response, public safety

---

## Architecture

```text
Drone Camera + Telemetry
        ↓
  YOLOv8 + SAHI Detection
        ↓
  BoT-SORT + OSNet Tracking
        ↓
  Highway Risk Analysis Engine
        ↓
  PPO Energy-Aware Navigation
        ↓
  Emergency Dashboard + Alerts
```

## Technical Performance

| Metric | Value |
|---|---:|
| MOTA | 83.2% |
| IDF1 | 78.5% |
| Energy Saved | 34.8% |
| ID Switches / 1k | 11 |
| Latency | ~45 ms |
| Mission Duration | +72% |

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/your-org/AeroMind_Sentinel.git
cd AeroMind_Sentinel
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
```

### 2. Launch Dashboard

```bash
python dashboard/app.py
# → http://localhost:5000
```
> **Note:** The dashboard now includes interactive Pitch Deck visuals and live video integration for the highway simulation.

### 3. Run Tests

```bash
pytest tests/ -v --cov=src
```

---

## Project Structure

```text
AeroMind_Sentinel/
├── dashboard/               # Flask web dashboard
│   ├── app.py               # Application factory + entry point
│   ├── database.py          # SQLite persistence layer
│   ├── routes/              # Flask Blueprints
│   │   ├── pages.py         # HTML page routes
│   │   ├── api_core.py      # Core API (results, status, config)
│   │   ├── api_highway.py   # Highway events & KPIs
│   │   ├── api_sim.py       # Simulation control
│   │   ├── api_db.py        # Database CRUD
│   │   └── api_stream.py    # MJPEG streaming & telemetry
│   └── static/              # CSS, JS, assets
├── src/                     # AI & ML source code
│   ├── detection/           # YOLOv8 + SAHI detector
│   ├── tracking/            # BoT-SORT + OSNet Re-ID tracker
│   ├── navigation/          # PPO RL navigation controller
│   ├── simulation/          # AirSim Gymnasium environment
│   ├── control/             # Real-time flight controller
│   ├── models/              # GRU encoder + online adapter
│   ├── rewards/             # Extended reward function
│   ├── system/              # 22Hz RT system integration
│   └── utils/               # Metrics, visualization, logging
├── scripts/                 # Training, evaluation, demo scripts
├── configs/                 # YAML configuration
├── tests/                   # pytest test suite
├── docs/                    # Technical report & pitch deck
├── models/                  # Trained model weights
├── experiments/             # Run artifacts & results
├── .github/workflows/       # CI/CD pipeline
├── Dockerfile               # Multi-stage production container
├── Makefile                 # Build commands
└── requirements.txt         # Python dependencies
```

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/results` | GET | Evaluation metrics |
| `/api/status` | GET | System health & file checks |
| `/api/config` | GET | Active YAML configuration |
| `/api/highway/events` | GET | Live/mock highway events |
| `/api/highway/kpis` | GET | Highway product KPIs |
| `/api/sim/start` | POST | Start simulation |
| `/api/sim/stop` | POST | Stop simulation |
| `/api/sim/status` | GET | Simulation state + telemetry |
| `/api/db/stats` | GET | Aggregate database stats |
| `/api/stream/live` | GET | MJPEG video stream |

---

## Deployment

### Docker

```bash
docker build -t aeromind-sentinel .
docker run -p 5000:5000 aeromind-sentinel
```

### Vercel

```bash
# Push to GitHub, then import in Vercel
# Uses api/index.py + vercel.json
```

---

## License

© 2026 AeroMind Technologies · Powered by AeroMind AI
