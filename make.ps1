# ═══════════════════════════════════════════════════════════════════════
#  AIC-4 DroneTracking — Windows PowerShell Build Script
#  Usage:  .\make.ps1 <target>
#  Example: .\make.ps1 help
# ═══════════════════════════════════════════════════════════════════════

param([string]$Target = "help")

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ROOT

function Log-Info    { param($msg) Write-Host "  $msg" -ForegroundColor Cyan }
function Log-Success { param($msg) Write-Host "  OK  $msg" -ForegroundColor Green }
function Log-Warn    { param($msg) Write-Host "  WARN  $msg" -ForegroundColor Yellow }
function Log-Error   { param($msg) Write-Host "  ERR  $msg" -ForegroundColor Red }
function Log-Section { param($msg) Write-Host "`n=== $msg ===" -ForegroundColor Magenta }

# ── Docker pre-flight check ───────────────────────────────────────────────────
function Assert-DockerRunning {
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Log-Error "Docker Desktop is not running (or Linux engine not started)."
        Log-Info  "Please launch Docker Desktop, wait for the whale icon in the system tray,"
        Log-Info  "then try this command again."
        exit 1
    }
}

# ── Setup ────────────────────────────────────────────────────────────────────
if ($Target -eq "install") {
    Log-Section "Installing Python Dependencies"
    pip install -r requirements.txt

} elseif ($Target -eq "setup") {
    Log-Section "Creating Project Directories"
    $dirs = @(
        "data/raw", "data/processed/images/train", "data/processed/images/val",
        "data/processed/labels/train", "data/processed/labels/val",
        "data/annotations", "data/reid/train", "data/reid/val",
        "models/detection", "models/reid", "models/rl", "models/exported",
        "experiments/logs", "experiments/checkpoints", "experiments/results"
    )
    foreach ($d in $dirs) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
    Log-Success "Project directories created."

# ── Data Collection ──────────────────────────────────────────────────────────
} elseif ($Target -eq "collect-data") {
    Log-Section "Collecting AirSim Frames"
    python scripts/collect_data.py --config configs/config.yaml

} elseif ($Target -eq "collect-data-mock") {
    Log-Section "Collecting Synthetic Frames (Mock)"
    python scripts/collect_data.py --config configs/config.yaml --mock

} elseif ($Target -eq "collect-reid-mock") {
    Log-Section "Collecting Re-ID Crops (Mock)"
    python scripts/collect_reid_crops.py --config configs/config.yaml --mock

# ── Training ─────────────────────────────────────────────────────────────────
} elseif ($Target -eq "train-all") {
    Log-Section "Running All Training Phases (Mock)"
    python scripts/train_detector.py --config configs/config.yaml
    python scripts/train_reid.py --config configs/config.yaml --mock
    python scripts/train_rl.py --config configs/config.yaml --mock --timesteps 10000

} elseif ($Target -eq "train-detector") {
    Log-Section "Training YOLOv8 Detector"
    python scripts/train_detector.py --config configs/config.yaml

} elseif ($Target -eq "train-reid") {
    Log-Section "Training OSNet Re-ID (Mock)"
    python scripts/train_reid.py --config configs/config.yaml --mock

} elseif ($Target -eq "train-rl") {
    Log-Section "Training PPO Navigation Agent (Mock)"
    python scripts/train_rl.py --config configs/config.yaml --mock --timesteps 10000

# ── Evaluation & Demo ────────────────────────────────────────────────────────
} elseif ($Target -eq "evaluate-mock") {
    Log-Section "Running Mock Evaluation"
    python scripts/evaluate.py --config configs/config.yaml --scenario all --mock

} elseif ($Target -eq "demo-mock") {
    Log-Section "Running Mock Demo"
    python scripts/run_demo.py --scenario dense_urban --mock

} elseif ($Target -eq "demo-record") {
    Log-Section "Recording Mock Demo"
    python scripts/run_demo.py --scenario dense_urban --mock --record --max-frames 300

# ── Dashboard / Simulation ───────────────────────────────────────────────────
} elseif ($Target -eq "dashboard") {
    Log-Section "Starting C2 Dashboard"
    Log-Info "Open http://localhost:5000 in your browser"
    python dashboard/app.py

} elseif ($Target -eq "simulation") {
    Log-Section "Starting Mock Simulation Pipeline"
    python scripts/run_simulation.py --mock --record

} elseif ($Target -eq "swarm") {
    Log-Section "Starting 3-Drone Swarm (Mock)"
    python scripts/run_swarm.py --mock

# ── Tests ────────────────────────────────────────────────────────────────────
} elseif ($Target -eq "test") {
    Log-Section "Running Full Test Suite"
    pytest tests/ -v --cov=src --cov-report=term-missing

} elseif ($Target -eq "test-fast") {
    Log-Section "Running Tests (fast)"
    pytest tests/ -v -x -q

# ── Docker ───────────────────────────────────────────────────────────────────
} elseif ($Target -eq "docker-build") {
    Log-Section "Building Docker Image"
    Assert-DockerRunning
    Set-Location $ROOT
    docker build -t aic4-dronetracking:latest .
    if ($LASTEXITCODE -eq 0) { Log-Success "Image built: aic4-dronetracking:latest" }
    else { Log-Error "docker build failed (exit $LASTEXITCODE)"; exit $LASTEXITCODE }

} elseif ($Target -eq "docker-up") {
    Log-Section "Starting Dashboard Container"
    Assert-DockerRunning
    Set-Location $ROOT
    docker compose up -d dashboard
    if ($LASTEXITCODE -eq 0) { Log-Success "Dashboard running at http://localhost:5000" }
    else { Log-Error "docker compose up failed (exit $LASTEXITCODE)"; exit $LASTEXITCODE }

} elseif ($Target -eq "docker-up-sim") {
    Log-Section "Starting Dashboard + Mock Simulation"
    Assert-DockerRunning
    Set-Location $ROOT
    docker compose up -d dashboard simulation
    if ($LASTEXITCODE -eq 0) { Log-Success "Dashboard at http://localhost:5000" }
    else { Log-Error "docker compose up failed (exit $LASTEXITCODE)"; exit $LASTEXITCODE }

} elseif ($Target -eq "docker-up-swarm") {
    Log-Section "Starting Dashboard + 3-Drone Swarm"
    Assert-DockerRunning
    Set-Location $ROOT
    docker compose --profile swarm up -d
    if ($LASTEXITCODE -eq 0) { Log-Success "Swarm C2 at http://localhost:5000/swarm" }
    else { Log-Error "docker compose up failed (exit $LASTEXITCODE)"; exit $LASTEXITCODE }

} elseif ($Target -eq "docker-down") {
    Log-Section "Stopping All Containers"
    Assert-DockerRunning
    Set-Location $ROOT
    docker compose down
    if ($LASTEXITCODE -eq 0) { Log-Success "All containers stopped." }
    else { Log-Error "docker compose down failed (exit $LASTEXITCODE)"; exit $LASTEXITCODE }

} elseif ($Target -eq "docker-logs") {
    Assert-DockerRunning
    Set-Location $ROOT
    docker compose logs -f

# ── Edge Model Export ────────────────────────────────────────────────────────
} elseif ($Target -eq "export-models") {
    Log-Section "Exporting Models to ONNX"
    python scripts/export_models.py --model all

} elseif ($Target -eq "export-models-trt") {
    Log-Section "Exporting Models to ONNX + TensorRT"
    python scripts/export_models.py --model all --trt

# ── Utilities ────────────────────────────────────────────────────────────────
} elseif ($Target -eq "tensorboard") {
    tensorboard --logdir experiments/logs

} elseif ($Target -eq "fmt") {
    Log-Section "Formatting Code"
    black src/ scripts/ tests/
    isort src/ scripts/ tests/

} elseif ($Target -eq "clean") {
    Log-Section "Cleaning Build Artefacts"
    Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Recurse -Filter "*.log" | Remove-Item -Force -ErrorAction SilentlyContinue
    Log-Success "Clean complete."

# ── Help ─────────────────────────────────────────────────────────────────────
} elseif ($Target -eq "help") {
    Write-Host ""
    Write-Host "  AIC-4 DroneTracking -- Windows PowerShell Build Script" -ForegroundColor Cyan
    Write-Host "  Usage: .\make.ps1 <target>" -ForegroundColor White
    Write-Host ""
    Write-Host "  SETUP" -ForegroundColor Yellow
    Write-Host "    setup              Create all project directories"
    Write-Host "    install            pip install -r requirements.txt"
    Write-Host ""
    Write-Host "  DATA COLLECTION" -ForegroundColor Yellow
    Write-Host "    collect-data-mock  Generate synthetic frames (no AirSim)"
    Write-Host "    collect-reid-mock  Generate synthetic Re-ID crops"
    Write-Host ""
    Write-Host "  TRAINING" -ForegroundColor Yellow
    Write-Host "    train-all          Run all phases (mock)"
    Write-Host "    train-detector     Phase 1: YOLOv8"
    Write-Host "    train-reid         Phase 2: OSNet Re-ID"
    Write-Host "    train-rl           Phase 4: PPO RL"
    Write-Host ""
    Write-Host "  EVALUATION & DEMO" -ForegroundColor Yellow
    Write-Host "    evaluate-mock      Full eval with synthetic data"
    Write-Host "    demo-mock          Live mock demo"
    Write-Host "    demo-record        Record demo frames"
    Write-Host ""
    Write-Host "  DASHBOARD (run in separate terminals)" -ForegroundColor Yellow
    Write-Host "    dashboard          Start Flask C2 Dashboard"
    Write-Host "    simulation         Start mock AI simulation"
    Write-Host "    swarm              Start 3-drone swarm pipeline"
    Write-Host ""
    Write-Host "  TESTS" -ForegroundColor Yellow
    Write-Host "    test               Full pytest suite"
    Write-Host "    test-fast          Stop on first failure"
    Write-Host ""
    Write-Host "  DOCKER (requires Docker Desktop running)" -ForegroundColor Yellow
    Write-Host "    docker-build       Build Docker image"
    Write-Host "    docker-up          Start dashboard container"
    Write-Host "    docker-up-sim      Start dashboard + mock simulation"
    Write-Host "    docker-up-swarm    Start dashboard + 3-drone swarm"
    Write-Host "    docker-down        Stop all containers"
    Write-Host "    docker-logs        Tail container logs"
    Write-Host ""
    Write-Host "  EDGE MODEL EXPORT" -ForegroundColor Yellow
    Write-Host "    export-models      Export to ONNX (FP32 + FP16)"
    Write-Host "    export-models-trt  Also compile TensorRT engines"
    Write-Host ""
    Write-Host "  UTILITIES" -ForegroundColor Yellow
    Write-Host "    tensorboard        Launch TensorBoard"
    Write-Host "    fmt                Format code (black + isort)"
    Write-Host "    clean              Remove __pycache__ and .pyc files"
    Write-Host ""

} else {
    Write-Host "  Unknown target: '$Target'" -ForegroundColor Red
    Write-Host "  Run '.\make.ps1 help' to see all available targets." -ForegroundColor Red
    exit 1
}
