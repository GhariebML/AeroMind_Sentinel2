.PHONY: install setup \
        collect-data collect-reid \
        train-all train-detector train-reid train-rl \
        evaluate evaluate-mock \
        demo demo-mock demo-record \
        test test-fast \
        docker-build docker-up docker-down docker-logs \
        export-models \
        clean tensorboard fmt help

# ─── Setup ────────────────────────────────────────────────────────────────────

install:
	pip install -r requirements.txt

setup: install
	mkdir -p data/raw data/processed/images/{train,val,test} \
	         data/processed/labels/{train,val,test} \
	         data/annotations data/reid/{train,val} \
	         models/detection models/reid models/rl \
	         experiments/{logs,checkpoints,results}
	@echo "Project directories created."

# ─── Data Collection ──────────────────────────────────────────────────────────

collect-data:
	python scripts/collect_data.py --config configs/config.yaml

collect-data-mock:
	python scripts/collect_data.py --config configs/config.yaml --mock

collect-reid:
	python scripts/collect_reid_crops.py --config configs/config.yaml

collect-reid-mock:
	python scripts/collect_reid_crops.py --config configs/config.yaml --mock

# ─── Training ─────────────────────────────────────────────────────────────────

# Run all 4 training phases in sequence
train-all: train-detector train-reid train-rl

train-detector:
	python scripts/train_detector.py --config configs/config.yaml

train-reid:
	python scripts/train_reid.py --config configs/config.yaml

train-reid-mock:
	python scripts/train_reid.py --config configs/config.yaml --mock

train-rl:
	python scripts/train_rl.py --config configs/config.yaml

train-rl-mock:
	python scripts/train_rl.py --config configs/config.yaml --mock --timesteps 10000

# ─── Evaluation ───────────────────────────────────────────────────────────────

evaluate:
	python scripts/evaluate.py --config configs/config.yaml --scenario all

evaluate-mock:
	python scripts/evaluate.py --config configs/config.yaml --scenario all --mock

# ─── Demo ─────────────────────────────────────────────────────────────────────

demo:
	python scripts/run_demo.py --scenario dense_urban

demo-mock:
	python scripts/run_demo.py --scenario dense_urban --mock

demo-record:
	python scripts/run_demo.py --scenario dense_urban --mock --record --max-frames 300

# ─── Tests ────────────────────────────────────────────────────────────────────

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

test-fast:
	pytest tests/ -v -x -q

# ─── Utilities ────────────────────────────────────────────────────────────────

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.log" -delete 2>/dev/null || true

tensorboard:
	tensorboard --logdir experiments/logs

fmt:
	black src/ scripts/ tests/
	isort src/ scripts/ tests/

# ─── Docker ───────────────────────────────────────────────────────────────────

docker-build:
	docker build -t aic4-dronetracking:latest .

docker-up:
	docker-compose up -d dashboard
	@echo "Dashboard running at http://localhost:5000"

docker-up-sim:
	docker-compose up -d dashboard simulation
	@echo "Dashboard + mock simulation running."

docker-up-swarm:
	docker-compose --profile swarm up -d
	@echo "Dashboard + swarm simulation running."

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# ─── Edge Model Export ────────────────────────────────────────────────────────

export-models:
	python scripts/export_models.py --model all

export-models-trt:
	python scripts/export_models.py --model all --trt

# ─── Help ─────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "AeroMind AI DroneTracking — Build Commands"
	@echo "======================================"
	@echo "  make setup            Create all project directories"
	@echo "  make install          pip install -r requirements.txt"
	@echo ""
	@echo "  Data Collection:"
	@echo "  make collect-data     Collect frames from AirSim"
	@echo "  make collect-data-mock  Generate synthetic frames (no AirSim)"
	@echo "  make collect-reid     Extract Re-ID crops from sequences"
	@echo "  make collect-reid-mock  Generate synthetic Re-ID crops"
	@echo ""
	@echo "  Training (in order):"
	@echo "  make train-all        Run all 4 phases sequentially"
	@echo "  make train-detector   Phase 1: YOLOv8 fine-tuning"
	@echo "  make train-reid       Phase 2: OSNet Re-ID training"
	@echo "  make train-rl         Phase 4: PPO RL navigation"
	@echo ""
	@echo "  Evaluation:"
	@echo "  make evaluate         Full system eval (requires AirSim)"
	@echo "  make evaluate-mock    Full eval with synthetic data"
	@echo ""
	@echo "  Demo:"
	@echo "  make demo             Live AirSim demo"
	@echo "  make demo-mock        Mock demo (no AirSim)"
	@echo "  make demo-record      Record MP4 demo video"
	@echo ""
	@echo "  Dev:"
	@echo "  make test             Run full test suite"
	@echo "  make test-fast        Run tests, stop on first failure"
	@echo "  make tensorboard      Launch TensorBoard"
	@echo "  make fmt              Format code (black + isort)"
	@echo ""
	@echo "  Docker (Production Deployment):"
	@echo "  make docker-build     Build Docker image"
	@echo "  make docker-up        Start dashboard container"
	@echo "  make docker-up-sim    Start dashboard + mock simulation"
	@echo "  make docker-up-swarm  Start dashboard + 3-drone swarm"
	@echo "  make docker-down      Stop all containers"
	@echo "  make docker-logs      Tail container logs"
	@echo ""
	@echo "  Edge Model Export:"
	@echo "  make export-models    Export YOLO + Re-ID to ONNX"
	@echo "  make export-models-trt  Also compile TensorRT engines"
	@echo ""
