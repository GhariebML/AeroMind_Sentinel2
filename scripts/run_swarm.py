import argparse
import sys
import time
from pathlib import Path
import json

import cv2
import numpy as np
import yaml
from loguru import logger
import torch

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── Ensure vendor/ is on path so airsim + msgpackrpc shim are available ───────
_VENDOR = ROOT / "vendor"
if str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

from src.simulation.airsim_env import AerialTrackingEnv
from src.tracking.swarm_manager import DistributedSwarmManager

def load_shared_models(cfg, args):
    logger.info("Loading Shared Perception & RL Models...")
    
    # 1. Detector
    try:
        from src.detection.detector import AerialDetector
        logger.info("Loading YOLOv8 Detector \u2014")
        w_path = str(ROOT / "models" / "detection" / "best.pt")
        det_cfg = {**cfg["detection"], "weights": w_path}
        detector = AerialDetector(det_cfg)
    except Exception as e:
        logger.error(f"Detector failed to load: {e}")
        detector = None

    # 2. PPO
    try:
        from src.navigation.rl_controller import RLNavigationController
        logger.info("Loading Shared PPO Controller \u2014")
        w_path = str(ROOT / "models" / "rl" / "ppo_final.zip")
        # Build empty agent then load weights if exist
        import gymnasium as gym
        from gymnasium import spaces
        # Dummy env for PPO initialisation
        dummy_env = gym.Env()
        dummy_env.action_space = spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)
        obs_dim = 3 + 3 + 1 + 1 + 1 + cfg["rl"]["state"]["heatmap_size"]**2 + 10
        dummy_env.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32)
        
        ppo_model = RLNavigationController(cfg, env=dummy_env)
        ppo_model.build(env=dummy_env)
        if Path(w_path).exists():
            ppo_model.load(w_path)
            logger.info("Loaded PPO weights successfully.")
        else:
            logger.warning("PPO weights not found \u2014 using random policy.")
    except Exception as e:
        logger.error(f"PPO failed to load: {e}")
        ppo_model = None

    return detector, ppo_model


def run_swarm(cfg, args):
    detector, ppo_model = load_shared_models(cfg, args)
    
    swarm_manager = DistributedSwarmManager()
    
    # Initialize 3 Drones
    drones = ["Drone1", "Drone2", "Drone3"]
    envs = {}
    trackers = {}
    obs = {}
    
    from src.tracking.tracker import BotSortTracker, ReIDModule
    
    # Setup ReID (shared weights)
    reid_w = str(ROOT / "models" / "reid" / "reid_best.pt")
    reid = ReIDModule({**cfg["reid"], "weights": reid_w})
    
    for drone in drones:
        logger.info(f"Initialising {drone}...")
        envs[drone] = AerialTrackingEnv(cfg, detector=detector, tracker=None, vehicle_name=drone)
        trackers[drone] = BotSortTracker(cfg["tracking"], reid_module=reid)
        obs[drone], _ = envs[drone].reset()

    logger.info("="*60)
    logger.info(f"   AeroMind AI SWARM SIMULATION ({len(drones)} Drones)")
    logger.info("="*60)

    try:
        while True:
            start_t = time.time()
            all_drone_states = []
            all_tracks = []
            
            for drone in drones:
                env = envs[drone]
                # 1. Get Frame & State
                frame = env._client.get_frame()
                state = env._client.get_state()
                current_time = state.timestamp
                all_drone_states.append({"name": drone, "pos": state.position, "yaw": state.heading_deg})
                
                # 2. Perception (Detector -> Tracker)
                bboxes = detector.detect(frame) if detector else []
                local_tracks = trackers[drone].update(bboxes, frame)
                
                # 3. Swarm Distributed Re-ID
                assigned_global_ids = swarm_manager.update_tracks(
                    drone_name=drone,
                    local_tracks=local_tracks,
                    current_time=current_time,
                    drone_pos=state.position,
                    drone_yaw=state.heading_deg
                )
                
                # Update observation with track count
                obs[drone][11] = len(assigned_global_ids) / 20.0
                
                # 4. PPO Action
                if ppo_model:
                    action = ppo_model.predict(obs[drone], deterministic=True)
                else:
                    action = env.action_space.sample() * 0.1
                
                # 5. Environment Step
                obs[drone], reward, terminated, truncated, info = env.step(action)
                
                if terminated or truncated:
                    obs[drone], _ = env.reset()
                    trackers[drone] = BotSortTracker(cfg["tracking"], reid_module=reid) # Reset tracker
                    
            # Telemetry Reporting for Dashboard
            telemetry = {
                "drones": all_drone_states,
                "targets": [
                    {"id": t.global_id, "cls": t.class_name, "x": t.ground_x, "y": t.ground_y, "source": t.drone_source}
                    for t in swarm_manager.get_all_active_tracks(time.time(), timeout=2.0)
                ]
            }
            
            # Write telemetry to disk for dashboard to read
            telemetry_path = ROOT / "experiments" / "results" / "swarm_telemetry.json"
            telemetry_path.parent.mkdir(parents=True, exist_ok=True)
            with open(telemetry_path, "w") as f:
                json.dump(telemetry, f)
            
            # Stop condition
            stop_file = ROOT / "experiments" / "results" / ".sim_stop"
            if stop_file.exists():
                logger.info("Stop signal received. Terminating.")
                stop_file.unlink()
                break
                
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user.")
    finally:
        for drone in drones:
            envs[drone].close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="configs/config.yaml")
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    with open(ROOT / args.config) as f:
        cfg = yaml.safe_load(f)

    run_swarm(cfg, args)
