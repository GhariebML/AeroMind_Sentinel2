"""
scripts/run_pipeline.py
One-command full pipeline runner for AeroMind AI.

Runs all four training phases in sequence, then evaluates.
Safe to re-run — checks for existing artifacts and skips completed phases.

Usage:
    python scripts/run_pipeline.py --config configs/config.yaml --all
    python scripts/run_pipeline.py --config configs/config.yaml --mock
    python scripts/run_pipeline.py --phase 2               # Re-ID only
    python scripts/run_pipeline.py --phase 4 --eval        # RL + eval
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from loguru import logger


# ─── CLI ─────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="AeroMind AI Full Pipeline Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Phases:
  0  Data collection (collect_data.py)
  1  Detection training (train_detector.py)
  2  Re-ID training (train_reid.py)
  3  Integration check (pytest)
  4  RL training (train_rl.py)
  5  Evaluation (evaluate.py)
        """,
    )
    p.add_argument("--config",  default="configs/config.yaml")
    p.add_argument("--phase",   type=int, default=None,
                   help="Run a single phase (0–5). Default: all phases.")
    p.add_argument("--all",     action="store_true",
                   help="Run all phases (same as not specifying --phase)")
    p.add_argument("--mock",    action="store_true",
                   help="Use mock/synthetic mode for all phases (no AirSim/GPU required)")
    p.add_argument("--eval",    action="store_true",
                   help="Run evaluation after training")
    p.add_argument("--skip-existing", action="store_true", default=True,
                   help="Skip a phase if its output artifact already exists")
    p.add_argument("--device",  default="cuda", help="cuda | cpu")
    p.add_argument("--timesteps", type=int, default=0,
                   help="Override RL training timesteps (0 = use config)")
    return p.parse_args()


# ─── Phase definitions ────────────────────────────────────────────────────────

def phase_0_collect(args) -> bool:
    """Phase 0 — Data collection from AirSim."""
    output_check = ROOT / "data" / "raw"
    if args.skip_existing and any(output_check.rglob("*.jpg")):
        logger.info("Phase 0 SKIPPED — data already collected.")
        return True

    cmd = [sys.executable, "scripts/collect_data.py", "--config", args.config]
    if args.mock:
        cmd += ["--mock", "--frames", "500"]
    return _run(cmd, "Phase 0: Data Collection")


def phase_1_detector(args) -> bool:
    """Phase 1 — YOLOv8 fine-tuning."""
    output_check = ROOT / "models" / "detection" / "best.pt"
    if args.skip_existing and output_check.exists():
        logger.info("Phase 1 SKIPPED — detection weights already exist.")
        return True

    cmd = [sys.executable, "scripts/train_detector.py",
           "--config", args.config, "--device", args.device]
    return _run(cmd, "Phase 1: Detection Training")


def phase_2_reid(args) -> bool:
    """Phase 2 — OSNet Re-ID training."""
    output_check = ROOT / "models" / "reid" / "reid_best.pt"
    if args.skip_existing and output_check.exists():
        logger.info("Phase 2 SKIPPED — Re-ID weights already exist.")
        return True

    cmd = [sys.executable, "scripts/train_reid.py",
           "--config", args.config, "--device", args.device]
    if args.mock:
        cmd.append("--mock")
    return _run(cmd, "Phase 2: Re-ID Training")


def phase_3_test(args) -> bool:
    """Phase 3 — Integration test suite."""
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-q"]
    return _run(cmd, "Phase 3: Integration Tests")


def phase_4_rl(args) -> bool:
    """Phase 4 — PPO RL training."""
    output_check = ROOT / "models" / "rl" / "ppo_final.zip"
    if args.skip_existing and output_check.exists():
        logger.info("Phase 4 SKIPPED — RL weights already exist.")
        return True

    cmd = [sys.executable, "scripts/train_rl.py",
           "--config", args.config, "--device", args.device]
    if args.mock:
        cmd += ["--mock", "--timesteps", "10000"]
    elif args.timesteps > 0:
        cmd += ["--timesteps", str(args.timesteps)]
    return _run(cmd, "Phase 4: RL Navigation Training")


def phase_5_eval(args) -> bool:
    """Phase 5 — Evaluation."""
    cmd = [sys.executable, "scripts/evaluate.py",
           "--config", args.config, "--scenario", "all"]
    if args.mock:
        cmd.append("--mock")
    return _run(cmd, "Phase 5: Evaluation")


PHASES = {
    0: phase_0_collect,
    1: phase_1_detector,
    2: phase_2_reid,
    3: phase_3_test,
    4: phase_4_rl,
    5: phase_5_eval,
}

PHASE_NAMES = {
    0: "Data Collection",
    1: "Detection Training",
    2: "Re-ID Training",
    3: "Integration Tests",
    4: "RL Training",
    5: "Evaluation",
}


# ─── Runner ───────────────────────────────────────────────────────────────────

def _run(cmd: list, phase_name: str) -> bool:
    """Execute a subprocess command, log output, return success status."""
    logger.info(f"\n{'='*60}")
    logger.info(f"  ▶ {phase_name}")
    logger.info(f"{'='*60}")
    logger.info(f"  Command: {' '.join(str(c) for c in cmd)}")

    t0 = time.perf_counter()
    try:
        result = subprocess.run(
            cmd,
            cwd=str(ROOT),
            check=False,
            text=True,
        )
        elapsed = time.perf_counter() - t0
        if result.returncode == 0:
            logger.success(f"  ✓ {phase_name} completed in {elapsed:.1f}s")
            return True
        else:
            logger.error(f"  ✗ {phase_name} failed (exit code {result.returncode}) after {elapsed:.1f}s")
            return False
    except FileNotFoundError as e:
        logger.error(f"  ✗ Command not found: {e}")
        return False


# ─── Entry ───────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    logger.info("\n" + "="*60)
    logger.info("  AeroMind AI DroneTracking — Full Pipeline Runner")
    logger.info(f"  Config  : {args.config}")
    logger.info(f"  Mock    : {args.mock}")
    logger.info(f"  Device  : {args.device}")
    logger.info("="*60)

    if args.phase is not None:
        # Single phase
        phases_to_run = [args.phase]
        if args.eval and args.phase != 5:
            phases_to_run.append(5)
    else:
        # All phases
        phases_to_run = sorted(PHASES.keys())

    results: dict[int, bool] = {}
    pipeline_start = time.perf_counter()

    for phase_id in phases_to_run:
        if phase_id not in PHASES:
            logger.warning(f"Unknown phase {phase_id}, skipping.")
            continue
        fn = PHASES[phase_id]
        success = fn(args)
        results[phase_id] = success
        if not success and phase_id < 3:
            logger.error(f"Critical phase {phase_id} failed — aborting pipeline.")
            break

    total = time.perf_counter() - pipeline_start

    # Summary
    logger.info("\n" + "="*60)
    logger.info("  PIPELINE SUMMARY")
    logger.info("="*60)
    for phase_id, success in results.items():
        icon = "✅" if success else "❌"
        logger.info(f"  {icon} Phase {phase_id}: {PHASE_NAMES.get(phase_id, '?')}")
    logger.info(f"\n  Total time: {total:.1f}s")
    logger.info("="*60)

    n_failed = sum(1 for v in results.values() if not v)
    sys.exit(0 if n_failed == 0 else 1)


if __name__ == "__main__":
    main()
