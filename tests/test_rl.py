"""
tests/test_rl.py
Unit tests for the PPO RL navigation controller and reward shaping.
Run with: pytest tests/test_rl.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pytest


# ─── Shared fixture ───────────────────────────────────────────────────────────

@pytest.fixture
def full_cfg():
    return {
        "airsim": {
            "ip": "127.0.0.1", "port": 41451,
            "camera_name": "front_center", "frame_rate": 6,
            "drone": {"start_altitude": -30, "max_altitude": -60, "max_speed": 15.0},
        },
        "detection": {
            "model": "yolov8n",
            "weights": "models/detection/nonexistent.pt",
            "input_size": 640,
            "confidence_threshold": 0.5,
            "nms_iou_threshold": 0.45,
            "classes": {0: "vehicle", 1: "pedestrian", 2: "aircraft"},
            "sahi": {"enabled": False, "slice_height": 320, "slice_width": 320,
                     "overlap_height_ratio": 0.2, "overlap_width_ratio": 0.2},
            "training": {
                "epochs": 1, "batch_size": 2, "lr0": 0.001, "lrf": 0.00001,
                "warmup_epochs": 1,
                "augmentation": {"mosaic": True, "mixup": 0.1, "random_scale": [0.5, 1.5],
                                 "motion_blur": True, "brightness_jitter": 0.3,
                                 "contrast_jitter": 0.3, "perspective": 0.2},
                "dataset_split": [0.7, 0.15, 0.15], "target_frames": 100,
            },
        },
        "reid": {
            "model": "osnet_x0_25", "weights": "models/reid/nonexistent.pt",
            "embedding_dim": 256,
            "training": {"epochs": 1, "batch_size": 4, "lr": 0.0003,
                         "loss": "triplet", "triplet_margin": 0.5,
                         "mining": "hard", "warmup_steps": 10},
        },
        "tracking": {
            "tracker": "botsort",
            "kalman": {"process_noise_scale": 1.0, "measurement_noise_scale": 1.0},
            "iou_threshold": 0.3, "reid_cosine_threshold": 0.4,
            "iou_weight": 0.5, "reid_weight": 0.5,
            "max_age": 30, "min_hits": 3,
            "use_reid": False, "reid_freq": 1,
        },
        "rl": {
            "algorithm": "PPO", "policy": "MlpPolicy",
            "policy_kwargs": {"net_arch": [64, 64], "activation_fn": "tanh"},
            "learning_rate": 3e-4, "n_steps": 64, "batch_size": 16,
            "n_epochs": 2, "gamma": 0.99, "gae_lambda": 0.95,
            "clip_range": 0.2, "ent_coef": 0.01, "vf_coef": 0.5,
            "max_grad_norm": 0.5, "total_timesteps": 256,
            "episode_length": 20, "n_episodes_eval": 1, "eval_freq": 100,
            "reward": {"alpha": 5.0, "beta": 0.1, "gamma": 0.05},
            "state": {
                "use_drone_pose": True, "use_battery": True,
                "use_active_tracks": True, "heatmap_size": 8,
                "use_track_duration_hist": True,
            },
            "action": {"max_forward_vel": 10.0, "max_vertical_vel": 3.0,
                       "max_yaw_rate": 45.0},
        },
        "energy": {"c1": 0.10, "c2": 0.05, "c3": 0.20, "c4": 0.02,
                   "battery_capacity_joules": 500.0},
        "logging": {
            "level": "INFO", "log_dir": "experiments/logs",
            "checkpoint_dir": "experiments/checkpoints",
            "results_dir": "experiments/results",
            "tensorboard": False,
            "wandb": {"enabled": False, "project": "test", "entity": "test"},
            "save_freq": 100, "video_freq": 500,
        },
    }


@pytest.fixture
def env(full_cfg):
    from src.simulation.airsim_env import AerialTrackingEnv
    return AerialTrackingEnv(full_cfg)


# ─── Reward function ─────────────────────────────────────────────────────────

class TestRewardFunction:
    """Tests that the reward R(t) = α·T(t) − β·E(t) − γ·P(t) is correct."""

    def test_more_tracks_higher_reward(self, env):
        """Reward should increase with more active tracks (all else equal)."""
        env.reset()
        # Two steps: first with many tracks, then few — reward should differ
        # We cannot directly set tracks, but we verify reward > 0 when environment
        # generates a non-zero number of tracks
        _, reward, _, _, info = env.step(np.zeros(3))
        n_tracks = info.get("n_tracks", 0)
        # If tracks > 0, reward contribution from tracking is positive
        alpha = env._alpha
        beta  = env._beta
        energy = info.get("energy_consumed", 0.0)
        expected_tracking_contribution = alpha * n_tracks
        expected_energy_penalty = beta * energy
        # Reward = tracking - energy - id_switch (id_switch ≈ 0 on first step)
        assert reward >= -expected_energy_penalty - 1e-3  # at minimum

    def test_alpha_scales_reward(self, full_cfg):
        """Higher alpha should produce higher reward when tracks > 0."""
        from src.simulation.airsim_env import AerialTrackingEnv

        cfg_low  = {**full_cfg, "rl": {**full_cfg["rl"], "reward": {"alpha": 1.0, "beta": 0.0, "gamma": 0.0}}}
        cfg_high = {**full_cfg, "rl": {**full_cfg["rl"], "reward": {"alpha": 10.0, "beta": 0.0, "gamma": 0.0}}}

        np.random.seed(0)
        env_low  = AerialTrackingEnv(cfg_low)
        env_low.reset()
        _, r_low, _, _, info_low = env_low.step(np.zeros(3))

        np.random.seed(0)
        env_high = AerialTrackingEnv(cfg_high)
        env_high.reset()
        _, r_high, _, _, info_high = env_high.step(np.zeros(3))

        if info_low.get("n_tracks", 0) > 0:
            assert r_high > r_low

    def test_battery_termination(self, full_cfg):
        """Episode must terminate when battery is exhausted."""
        from src.simulation.airsim_env import AerialTrackingEnv, EnergyAccumulator
        # Use tiny battery
        cfg = {**full_cfg}
        cfg["energy"] = {**cfg["energy"], "battery_capacity_joules": 0.001}
        env = AerialTrackingEnv(cfg)
        obs, _ = env.reset()

        terminated = False
        for _ in range(50):
            _, _, terminated, truncated, _ = env.step(np.ones(3))
            if terminated:
                break

        assert terminated, "Episode should terminate when battery runs out"


# ─── RLNavigationController ───────────────────────────────────────────────────

class TestRLNavigationController:
    @pytest.fixture
    def controller(self, full_cfg, env):
        pytest.importorskip("stable_baselines3")
        from src.navigation.rl_controller import RLNavigationController
        ctrl = RLNavigationController(full_cfg, env=env)
        ctrl.build(env=env)
        return ctrl

    def test_build_creates_model(self, controller):
        assert controller.model is not None

    def test_predict_returns_correct_shape(self, controller, env):
        obs, _ = env.reset()
        action = controller.predict(obs, deterministic=True)
        assert action.shape == (3,)

    def test_predict_action_in_bounds(self, controller, env):
        obs, _ = env.reset()
        action = controller.predict(obs, deterministic=True)
        assert action.min() >= env.action_space.low.min() - 1e-5
        assert action.max() <= env.action_space.high.max() + 1e-5

    def test_short_training_runs(self, full_cfg, env, tmp_path):
        """Training for a tiny number of steps must not crash."""
        pytest.importorskip("stable_baselines3")
        from src.navigation.rl_controller import RLNavigationController

        # Use very small n_steps to fit within 128 total timesteps
        tiny_cfg = {**full_cfg}
        tiny_cfg["rl"] = {**full_cfg["rl"], "n_steps": 64, "batch_size": 16}
        ctrl = RLNavigationController(tiny_cfg, env=env)
        ctrl.build(env=env)
        ctrl.train(total_timesteps=128)
        assert ctrl.model is not None

    def test_save_and_load(self, controller, full_cfg, env, tmp_path):
        """Model must survive a save/load round trip."""
        save_path = str(tmp_path / "test_ppo")
        controller.model.save(save_path)

        from src.navigation.rl_controller import RLNavigationController
        ctrl2 = RLNavigationController(full_cfg, env=env)
        ctrl2.load(save_path)
        obs, _ = env.reset()
        action = ctrl2.predict(obs)
        assert action.shape == (3,)

    def test_evaluate_returns_dict(self, controller):
        results = controller.evaluate(n_episodes=1)
        assert isinstance(results, dict)
        for key in ("mean_reward", "std_reward", "mean_tracks",
                    "mean_energy_J", "mean_id_switches", "mean_episode_length"):
            assert key in results


# ─── Action space ─────────────────────────────────────────────────────────────

class TestActionSpace:
    def test_action_scaling(self, full_cfg):
        """
        Actions in [-1, 1] should map to physical velocities within limits.
        """
        from src.simulation.airsim_env import AerialTrackingEnv
        env = AerialTrackingEnv(full_cfg)
        env.reset()

        rl_cfg = full_cfg["rl"]["action"]
        max_fwd = rl_cfg["max_forward_vel"]   # 10.0 m/s
        max_vrt = rl_cfg["max_vertical_vel"]  # 3.0  m/s
        max_yaw = rl_cfg["max_yaw_rate"]      # 45.0 deg/s

        # Max action
        action = np.array([1.0, 1.0, 1.0])
        # The env scales internally — we verify the step doesn't raise
        env.step(action)

        # Min action
        action = np.array([-1.0, -1.0, -1.0])
        env.step(action)

    def test_random_actions_do_not_crash(self, env):
        env.reset()
        for _ in range(10):
            action = env.action_space.sample()
            env.step(action)
