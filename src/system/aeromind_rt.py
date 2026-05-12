"""
src/system/aeromind_rt.py
Phase 05: Full System Integration & 22Hz Real-Time Loop.

This is the main entry point for the production-ready AeroMind RT system.
It wires the entire neural adaptation stack into a high-precision control loop.
"""

import time
import yaml
import torch
import numpy as np
from pathlib import Path
from loguru import logger
from datetime import datetime

from src.simulation.airsim_env import AerialTrackingEnv
from src.detection.detector import AerialDetector
from src.tracking.tracker import BotSortTracker, ReIDModule
from src.models.temporal_encoder import TemporalStateEncoder
from src.control.rt_controller import RealTimeFlightController
from src.rewards.rt_reward import RealTimeRewardComputer

class AeroMindRealTimeSystem:
    def __init__(self, config_path: str, mock: bool = False):
        with open(config_path, 'r') as f:
            self.cfg = yaml.safe_load(f)
        
        self.mock = mock
        self.dt = 1.0 / 22.0 # 22Hz ~ 45.45ms
        
        logger.info(f"Initializing AeroMind RT System (Mock: {mock}, Target: 22Hz)")
        
        # 1. Perception Stack
        self.detector = AerialDetector(self.cfg["detection"])
        self.reid = ReIDModule(self.cfg["reid"])
        self.tracker = BotSortTracker(self.cfg["tracking"], reid_module=self.reid)
        
        # 2. Simulation / Hardware Interface
        self.env = AerialTrackingEnv(self.cfg, detector=self.detector, tracker=self.tracker)
        
        # 3. Neural Stack
        self.temporal_encoder = TemporalStateEncoder()
        
        # Load base policy (Frozen PPO)
        # In a real scenario, we'd load the .zip file from SB3
        # For now, we'll use a mock or the build() method
        from src.navigation.rl_controller import RLNavigationController
        rl_wrapper = RLNavigationController(self.cfg, env=self.env)
        rl_wrapper.build(env=self.env) # Builds the PPO model
        
        self.controller = RealTimeFlightController(base_policy=rl_wrapper.model)
        
        # 4. Reward & Logging
        self.reward_computer = RealTimeRewardComputer()
        self.history = []

    def run(self, max_steps: int = 1000):
        logger.info("Starting real-time loop...")
        obs, _ = self.env.reset()
        self.temporal_encoder.reset()
        
        step = 0
        latencies = {"total": [], "perception": [], "control": [], "env": []}
        
        try:
            while step < max_steps:
                loop_start = time.perf_counter()
                
                # 1. Perception Stack
                p_start = time.perf_counter()
                enriched_obs = self.temporal_encoder.get_enriched_state(obs)
                # Note: In a full implementation, we'd also run detector/tracker here if not already in env.step
                latencies["perception"].append((time.perf_counter() - p_start) * 1000)
                
                # 2. Control Stack (PPO + Online Adapter)
                c_start = time.perf_counter()
                action = self.controller.predict(obs)
                latencies["control"].append((time.perf_counter() - c_start) * 1000)
                
                # 3. Environment Step
                e_start = time.perf_counter()
                next_obs, reward, terminated, truncated, info = self.env.step(action)
                latencies["env"].append((time.perf_counter() - e_start) * 1000)
                
                # 4. Update Adapter (Online Learning)
                rt_reward = self.reward_computer.compute(info)
                self.controller.store_transition(obs, action, rt_reward, next_obs, terminated)
                
                # 5. Timing & Profiling
                loop_end = time.perf_counter()
                total_latency = (loop_end - loop_start) * 1000
                latencies["total"].append(total_latency)
                
                if step % 50 == 0:
                    avg_lat = np.mean(latencies["total"][-50:])
                    freq = 1.0 / (avg_lat / 1000.0) if avg_lat > 0 else 0
                    logger.info(f"Step {step:04d} | Latency: {avg_lat:5.2f}ms | Freq: {freq:4.1f}Hz | Reward: {rt_reward:6.2f}")
                
                obs = next_obs
                step += 1
                
                if terminated or truncated:
                    logger.info(f"Episode finished at step {step} ({'Terminated' if terminated else 'Truncated'})")
                    break
                
                # 6. Precise 22Hz synchronization
                # We use a hybrid approach: sleep for most of the time, then spin-wait for precision
                target_time = loop_start + self.dt
                remaining = target_time - time.perf_counter()
                
                if remaining > 0.001:
                    time.sleep(remaining - 0.001) # Sleep for all but 1ms
                
                while time.perf_counter() < target_time:
                    pass # High-precision spin-wait
        
        except KeyboardInterrupt:
            logger.warning("\nManual shutdown triggered by user.")
        finally:
            self.shutdown(latencies)

    def shutdown(self, latencies=None):
        logger.info("Shutting down AeroMind RT System...")
        
        if latencies:
            avg_total = np.mean(latencies["total"])
            logger.info(f"Final Latency Profile (Average):")
            logger.info(f"  - Total:      {avg_total:.2f}ms")
            logger.info(f"  - Perception: {np.mean(latencies['perception']):.2f}ms")
            logger.info(f"  - Control:    {np.mean(latencies['control']):.2f}ms")
            logger.info(f"  - Env:        {np.mean(latencies['env']):.2f}ms")
            
            if avg_total > 45.45:
                logger.warning(f"LATENCY BUDGET EXCEEDED: {avg_total:.2f}ms > 45.45ms (22Hz target)")
            else:
                logger.success(f"LATENCY BUDGET MET: {avg_total:.2f}ms <= 45.45ms")

        # Save adapter weights
        save_path = Path("checkpoints/adapter_latest.pt")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.controller.save_adapter(str(save_path))
            logger.info(f"Adapter weights saved to {save_path}")
        except Exception as e:
            logger.error(f"Failed to save adapter weights: {e}")
        
        self.env.close()
        logger.info("System offline.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--mock", action="store_true", default=True)
    parser.add_argument("--steps", type=int, default=1000)
    args = parser.parse_args()
    
    system = AeroMindRealTimeSystem(args.config, mock=args.mock)
    system.run(max_steps=args.steps)
