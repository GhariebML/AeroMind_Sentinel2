"""
scripts/train_rl.py
Phase 4: Train PPO navigation agent in AirSim.

Usage:
    python scripts/train_rl.py --config configs/config.yaml
    python scripts/train_rl.py --config configs/config.yaml --timesteps 2000000
    python scripts/train_rl.py --config configs/config.yaml --resume models/rl/ppo_latest.zip
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml
from loguru import logger


def parse_args():
    p = argparse.ArgumentParser(description="Train PPO RL Controller — AeroMind AI Phase 4")
    p.add_argument("--config", default="configs/config.yaml")
    p.add_argument("--timesteps", type=int, default=None)
    p.add_argument("--resume", default=None, help="Path to existing PPO checkpoint")
    p.add_argument("--mock", action="store_true",
                   help="Mock mode: run without AirSim (for testing)")
    p.add_argument("--n-envs", type=int, default=1,
                   help="Number of parallel environments")
    return p.parse_args()


def make_env(cfg: dict, detector=None, tracker=None):
    """Factory for creating the Gymnasium env."""
    from src.simulation.airsim_env import AerialTrackingEnv
    return AerialTrackingEnv(cfg, detector=detector, tracker=tracker)


def load_perception(cfg: dict):
    """Load pre-trained detector + tracker (required if not mock)."""
    try:
        from src.detection.detector import AerialDetector
        from src.tracking.tracker import BotSortTracker, ReIDModule

        logger.info("Loading pre-trained detector ...")
        detector = AerialDetector(cfg["detection"])

        logger.info("Loading Re-ID module ...")
        reid = ReIDModule(cfg["reid"])

        logger.info("Building BoT-SORT tracker ...")
        tracker = BotSortTracker(cfg["tracking"], reid_module=reid)

        return detector, tracker
    except Exception as e:
        logger.warning(f"Could not load perception: {e} — RL will use mock perception.")
        return None, None


def main():
    args = parse_args()

    with open(ROOT / args.config) as f:
        cfg = yaml.safe_load(f)

    logger.info("=" * 60)
    logger.info("  AeroMind AI Phase 4: PPO RL Navigation Training")
    logger.info(f"  Algorithm : PPO")
    logger.info(f"  Steps     : {args.timesteps or cfg['rl']['total_timesteps']:,}")
    logger.info(f"  Reward    : α={cfg['rl']['reward']['alpha']} · T(t) "
                f"− β={cfg['rl']['reward']['beta']} · E(t) "
                f"− γ={cfg['rl']['reward']['gamma']} · P(t)")
    logger.info(f"  Network   : {cfg['rl']['policy_kwargs']['net_arch']}")
    logger.info(f"  Mock mode : {args.mock}")
    logger.info("=" * 60)

    # Load perception modules
    if args.mock:
        detector, tracker = None, None
    else:
        detector, tracker = load_perception(cfg)

    # Build environment
    env = make_env(cfg, detector=detector, tracker=tracker)
    logger.info("Environment created successfully.")

    # Build RL controller
    from src.navigation.rl_controller import RLNavigationController
    controller = RLNavigationController(cfg, env=env)

    if args.resume:
        logger.info(f"Resuming from checkpoint: {args.resume}")
        controller.load(args.resume)
    else:
        controller.build(env=env)

    # Train
    total_steps = args.timesteps or cfg["rl"]["total_timesteps"]
    controller.train(total_timesteps=total_steps)

    # Quick evaluation
    logger.info("\nRunning post-training evaluation ...")
    results = controller.evaluate(n_episodes=cfg["rl"]["n_episodes_eval"])

    logger.info("\nFinal Evaluation Summary:")
    for k, v in results.items():
        logger.info(f"  {k:<30}: {v:.3f}")

    logger.success("Phase 4 complete. RL agent saved to models/rl/")


if __name__ == "__main__":
    main()
