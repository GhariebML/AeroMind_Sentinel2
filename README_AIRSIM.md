# AeroMind AI DroneTracking — AirSim Integration Guide

> **Real prototype, ready to run.** This guide covers everything from first-time setup to live simulation with Unreal Engine.

---

## Quick Start (60 seconds)

```batch
# 1. Setup environment (one-time)
python setup\setup_environment.py

# 2a. Mock mode — no AirSim needed
launch_all.bat --mock

# 2b. Real AirSim — download + run
python setup\download_airsim_env.py   # download Blocks binary
launch_all.bat                        # starts everything
```

Then open **http://localhost:5000/demo** and click **▶ Start Simulation**.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   AeroMind AI System                          │
│                                                         │
│  launch_all.bat                                         │
│    ├── AirSim Binary (Unreal Engine)  ←── settings.json │
│    ├── Flask Dashboard  (port 5000)                     │
│    └── Simulation Runner                                │
│              │                                          │
│              ▼                                          │
│   AirSimClientWrapper                                   │
│     ├── Real mode: airsim.MultirotorClient              │
│     │     └── vendor/msgpackrpc (Python 3.14 shim)      │
│     └── Mock mode: SyntheticScene                       │
│              │                                          │
│              ▼                                          │
│   YOLOv8m → BoT-SORT → PPO Agent → Drone Commands       │
│              │                                          │
│              ▼                                          │
│   MJPEG stream + Telemetry JSON → Dashboard UI          │
└─────────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites
- Windows 10/11 (64-bit)
- Python 3.10+ (tested on 3.14)
- 8 GB RAM minimum, 16 GB recommended
- NVIDIA GPU recommended for real-time YOLOv8 inference
- **For real AirSim:** GPU with 4+ GB VRAM, DirectX 11+

### Step 1 — Clone & Setup

```batch
git clone https://github.com/your-repo/AeroMind AI_DroneTracking.git
cd AeroMind AI_DroneTracking
python setup\setup_environment.py
```

This script:
- Installs all Python dependencies
- Deploys `configs/airsim_settings.json` → `%USERPROFILE%\Documents\AirSim\settings.json`
- Verifies all project source files exist
- Prints a colour-coded status report

### Step 2 — Download AirSim Environment (for real mode)

```batch
python setup\download_airsim_env.py            # Blocks (~280 MB, recommended)
python setup\download_airsim_env.py --env airsimnh   # Neighborhood (~760 MB)
python setup\download_airsim_env.py --list     # show all options
```

Downloaded to: `airsim_envs/<env_name>/`

---

## Running

### Option A — Mock Mode (no AirSim, best for development)

```batch
launch_all.bat --mock
# or
python scripts\run_simulation.py --mock --record --scenario dense_urban
```

Mock mode features:
- 12 animated targets with sinusoidal motion paths
- Full YOLOv8 + BoT-SORT + PPO pipeline active
- ~15–30 FPS on CPU alone
- Zero dependencies on Unreal Engine

### Option B — Real AirSim

```batch
launch_airsim.bat          # starts Blocks.exe, waits for UE4 to load
launch_dashboard.bat       # start Flask dashboard (new window)
launch_simulation.bat      # run simulation (auto-detects AirSim)
# or
launch_all.bat             # does all of the above
```

### Option C — Manual

```batch
# Terminal 1: AirSim
airsim_envs\Blocks\WindowsNoEditor\Blocks.exe -windowed -ResX=1280 -ResY=720

# Terminal 2: Dashboard
python dashboard\app.py

# Terminal 3: Simulation
python scripts\run_simulation.py --scenario dense_urban --record

# Terminal 4: Diagnostic (verify connection)
python scripts\check_airsim.py
```

---

## AirSim Python Client — Python 3.14 Fix

The official `airsim` PyPI package fails to build on Python 3.10+ due to
incompatible `msgpack-rpc-python` → `tornado 4.x` dependency chain.

**Our solution** (vendored in this repo):
```
vendor/
├── airsim/         ← cloned from github.com/microsoft/AirSim PythonClient/
│   ├── client.py   ← MultirotorClient, CarClient, etc.
│   ├── types.py    ← ImageRequest, YawMode, etc.
│   └── utils.py
└── msgpackrpc/     ← custom shim (stdlib socket + msgpack 1.x, no tornado)
    └── __init__.py ← Client, Address, error
```

This approach:
- Works on Python 3.10, 3.11, 3.12, 3.13, 3.14
- Uses no `tornado`, no `backports`, no C extensions
- Full AirSim Multirotor API compatible

---

## Scenarios

| Scenario | Targets | Difficulty | Description |
|---|---|---|---|
| `dense_urban` | 12 | Medium | Mixed vehicles + pedestrians in urban grid |
| `highway` | 8 | Easy | Fast vehicles on straight road |
| `parking_lot` | 15 | Hard | Dense static + moving targets |
| `airport_apron` | 6 | Medium | Large aircraft + ground vehicles |
| `campus` | 10 | Medium | Mixed pedestrians + cyclists |
| `mixed_terrain` | 12 | Hard | All target types, random terrain |

---

## AirSim Settings

The settings file is at `configs/airsim_settings.json` and is automatically
deployed to `%USERPROFILE%\Documents\AirSim\settings.json` by the launchers.

Key settings:
```json
{
  "SimMode": "Multirotor",
  "Vehicles": {
    "Drone1": {
      "VehicleType": "SimpleFlight",
      "Cameras": {
        "front_center": { "Pitch": -90, "Width": 640, "Height": 640 }
      }
    }
  }
}
```

The camera is pointed **straight down** (Pitch: -90) for aerial tracking.

---

## Dashboard

| URL | Description |
|---|---|
| `http://localhost:5000/` | Main dashboard with metrics + charts |
| `http://localhost:5000/demo` | **Live simulation** (Start/Stop, MJPEG stream, telemetry) |
| `http://localhost:5000/api/sim/status` | JSON: running status + telemetry |
| `http://localhost:5000/api/stream/live` | Raw MJPEG stream |

---

## Diagnostics

```batch
# Full environment check
python setup\setup_environment.py --skip-install

# AirSim connectivity
python scripts\check_airsim.py [--ip 127.0.0.1] [--port 41451] [--save]

# Quick smoke test
python scripts\run_simulation.py --mock --max-frames 60
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `Cannot connect to AirSim` | Make sure the UE4 binary is running **before** the simulation |
| `tracks=0` in real mode | UE4 may not have spawned NPCs; switch map or use `dense_urban` scenario |
| Low FPS in real mode | Lower `configs/config.yaml` detection `input_size` from 640 to 416 |
| SAHI warning | One-time warning; SAHI auto-disables if not installed |
| `msgpackrpc` import error | Vendor path issue; run `python setup/setup_environment.py` |
| Dashboard 404 on /api/sim/status | Dashboard not restarted after code update; run `launch_dashboard.bat` |

---

## File Structure

```
AeroMind AI_DroneTracking/
├── setup/
│   ├── setup_environment.py     ← one-command setup
│   └── download_airsim_env.py   ← download Blocks/NH/City binaries
├── vendor/
│   ├── airsim/                  ← AirSim Python client (from GitHub)
│   └── msgpackrpc/              ← msgpack-rpc shim (Python 3.14 compat)
├── airsim_envs/                 ← downloaded UE4 binaries live here
│   └── Blocks/WindowsNoEditor/Blocks.exe
├── configs/
│   ├── airsim_settings.json     ← AirSim UE4 settings
│   └── config.yaml              ← pipeline config
├── src/simulation/
│   ├── airsim_client.py         ← unified real/mock client wrapper
│   └── airsim_env.py            ← Gymnasium environment
├── scripts/
│   ├── check_airsim.py          ← connectivity diagnostic
│   └── run_simulation.py        ← main simulation runner
├── dashboard/app.py             ← Flask dashboard
├── launch_airsim.bat            ← start AirSim binary
├── launch_dashboard.bat         ← start Flask server
├── launch_simulation.bat        ← start simulation runner
├── launch_all.bat               ← one-click: everything
└── requirements.txt
```
