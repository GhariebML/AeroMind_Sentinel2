"""
tests/test_simulation.py
Unit tests for the AirSim Gymnasium environment and energy model.
Run with: pytest tests/test_simulation.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pytest


# ─── Shared config fixture ────────────────────────────────────────────────────

@pytest.fixture
def full_cfg():
    """Minimal config that mirrors configs/config.yaml structure."""
    return {
        "airsim": {
            "ip":          "127.0.0.1",
            "port":        41451,
            "camera_name": "front_center",
            "frame_rate":  6,
            "drone": {
                "start_altitude": -30,
                "max_altitude":   -60,
                "max_speed":      15.0,
            },
        },
        "detection": {
            "model":                "yolov8n",
            "weights":              "models/detection/nonexistent.pt",
            "input_size":           640,
            "confidence_threshold": 0.5,
            "nms_iou_threshold":    0.45,
            "classes":              {0: "vehicle", 1: "pedestrian", 2: "aircraft"},
            "sahi": {
                "enabled":               False,
                "slice_height":          320,
                "slice_width":           320,
                "overlap_height_ratio":  0.2,
                "overlap_width_ratio":   0.2,
            },
            "training": {
                "epochs": 1, "batch_size": 2,
                "lr0": 0.001, "lrf": 0.00001, "warmup_epochs": 1,
                "augmentation": {
                    "mosaic": True, "mixup": 0.1, "random_scale": [0.5, 1.5],
                    "motion_blur": True, "brightness_jitter": 0.3,
                    "contrast_jitter": 0.3, "perspective": 0.2,
                },
                "dataset_split": [0.7, 0.15, 0.15],
                "target_frames": 100,
            },
        },
        "reid": {
            "model":         "osnet_x0_25",
            "weights":       "models/reid/nonexistent.pt",
            "embedding_dim": 256,
            "training": {
                "epochs": 1, "batch_size": 4, "lr": 0.0003,
                "loss": "triplet", "triplet_margin": 0.5,
                "mining": "hard", "warmup_steps": 10,
            },
        },
        "tracking": {
            "tracker":               "botsort",
            "kalman": {
                "process_noise_scale":     1.0,
                "measurement_noise_scale": 1.0,
            },
            "iou_threshold":          0.3,
            "reid_cosine_threshold":  0.4,
            "iou_weight":             0.5,
            "reid_weight":            0.5,
            "max_age":                30,
            "min_hits":               3,
            "use_reid":               False,
            "reid_freq":              1,
        },
        "rl": {
            "algorithm":     "PPO",
            "policy":        "MlpPolicy",
            "policy_kwargs": {"net_arch": [64, 64], "activation_fn": "tanh"},
            "learning_rate": 0.0003,
            "n_steps":       128,
            "batch_size":    32,
            "n_epochs":      2,
            "gamma":         0.99,
            "gae_lambda":    0.95,
            "clip_range":    0.2,
            "ent_coef":      0.01,
            "vf_coef":       0.5,
            "max_grad_norm": 0.5,
            "total_timesteps": 500,
            "episode_length":  20,
            "n_episodes_eval": 2,
            "eval_freq":       100,
            "reward": {"alpha": 5.0, "beta": 0.1, "gamma": 0.05},
            "state": {
                "use_drone_pose":          True,
                "use_battery":             True,
                "use_active_tracks":       True,
                "heatmap_size":            8,
                "use_track_duration_hist": True,
            },
            "action": {
                "max_forward_vel":  10.0,
                "max_vertical_vel":  3.0,
                "max_yaw_rate":     45.0,
            },
        },
        "energy": {
            "c1": 0.10, "c2": 0.05, "c3": 0.20, "c4": 0.02,
            "battery_capacity_joules": 500.0,
        },
        "logging": {
            "level":          "INFO",
            "log_dir":        "experiments/logs",
            "checkpoint_dir": "experiments/checkpoints",
            "results_dir":    "experiments/results",
            "tensorboard":    False,
            "wandb":          {"enabled": False, "project": "test", "entity": "test"},
            "save_freq":      100,
            "video_freq":     500,
        },
    }


# ─── EnergyAccumulator ────────────────────────────────────────────────────────

class TestEnergyAccumulator:
    def test_starts_at_zero(self):
        from src.simulation.airsim_env import EnergyAccumulator
        ea = EnergyAccumulator()
        ea.reset()
        assert ea.consumed == 0.0

    def test_full_battery_on_reset(self):
        from src.simulation.airsim_env import EnergyAccumulator
        ea = EnergyAccumulator(battery_capacity_joules=100.0)
        ea.reset()
        assert ea.remaining_fraction == pytest.approx(1.0)

    def test_energy_increases_with_motion(self):
        from src.simulation.airsim_env import EnergyAccumulator
        ea = EnergyAccumulator()
        ea.reset()
        ea.update(np.zeros(3), np.zeros(3), 0.0)
        delta = ea.update(np.array([5., 5., 0.]), np.array([3., 3., 0.]), 1.0)
        assert delta > 0.0
        assert ea.consumed > 0.0

    def test_altitude_change_costs_energy(self):
        from src.simulation.airsim_env import EnergyAccumulator
        ea1 = EnergyAccumulator(c3=0.20)
        ea1.reset()
        ea1.update(np.zeros(3), np.zeros(3), 0.0)
        cost_with_altitude = ea1.update(np.array([0., 0., 10.]), np.zeros(3), 1.0)

        ea2 = EnergyAccumulator(c3=0.20)
        ea2.reset()
        ea2.update(np.zeros(3), np.zeros(3), 0.0)
        cost_flat = ea2.update(np.zeros(3), np.zeros(3), 1.0)

        assert cost_with_altitude > cost_flat

    def test_remaining_decreases(self):
        from src.simulation.airsim_env import EnergyAccumulator
        ea = EnergyAccumulator(battery_capacity_joules=100.0)
        ea.reset()
        ea.update(np.zeros(3), np.zeros(3), 0.0)
        ea.update(np.array([10., 0., 0.]), np.array([5., 0., 0.]), 1.0)
        assert ea.remaining_fraction < 1.0

    def test_remaining_does_not_go_below_zero(self):
        from src.simulation.airsim_env import EnergyAccumulator
        ea = EnergyAccumulator(battery_capacity_joules=0.001)
        ea.reset()
        ea.update(np.zeros(3), np.zeros(3), 0.0)
        # Many large movements
        for i in range(100):
            ea.update(np.array([100., 100., 50.]), np.array([15., 15., 5.]), float(i))
        assert ea.remaining_fraction >= 0.0

    def test_energy_model_coefficients(self):
        """Verify c1 coefficient is applied correctly to path length."""
        from src.simulation.airsim_env import EnergyAccumulator
        ea = EnergyAccumulator(c1=1.0, c2=0.0, c3=0.0, c4=0.0, battery_capacity_joules=1e6)
        ea.reset()
        ea.update(np.zeros(3), np.zeros(3), 0.0)
        # Move exactly 5 units in X: path_length = 5
        delta = ea.update(np.array([5., 0., 0.]), np.zeros(3), 1.0)
        assert pytest.approx(delta, rel=0.01) == 5.0  # c1 * L = 1.0 * 5.0


# ─── AerialTrackingEnv ────────────────────────────────────────────────────────

class TestAerialTrackingEnv:
    @pytest.fixture
    def env(self, full_cfg):
        from src.simulation.airsim_env import AerialTrackingEnv
        return AerialTrackingEnv(full_cfg)

    def test_action_space_shape(self, env):
        assert env.action_space.shape == (3,)

    def test_action_space_bounds(self, env):
        assert env.action_space.low.min() == pytest.approx(-1.0)
        assert env.action_space.high.max() == pytest.approx(1.0)

    def test_observation_space_shape(self, env):
        # pos(3) + vel(3) + heading(1) + battery(1) + n_tracks(1)
        # + heatmap(8*8=64) + dur_hist(10) = 83
        assert env.observation_space.shape == (83,)

    def test_reset_returns_correct_obs_shape(self, env):
        obs, info = env.reset()
        assert obs.shape == (83,)
        assert isinstance(info, dict)

    def test_step_returns_5_tuple(self, env):
        env.reset()
        action = env.action_space.sample()
        result = env.step(action)
        assert len(result) == 5

    def test_step_obs_shape(self, env):
        env.reset()
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        assert obs.shape == (83,)

    def test_step_reward_is_scalar(self, env):
        env.reset()
        action = env.action_space.sample()
        _, reward, _, _, _ = env.step(action)
        assert np.isscalar(reward) or isinstance(reward, (int, float, np.floating))

    def test_step_info_keys(self, env):
        env.reset()
        _, _, _, _, info = env.step(env.action_space.sample())
        for key in ("n_tracks", "energy_consumed", "battery_remaining",
                    "id_switches", "step"):
            assert key in info

    def test_episode_truncation(self, env):
        """Episode must truncate at episode_length steps."""
        obs, _ = env.reset()
        truncated = False
        for _ in range(25):   # episode_length = 20 in fixture
            _, _, _, truncated, _ = env.step(env.action_space.sample())
            if truncated:
                break
        assert truncated, "Episode should have truncated within episode_length steps"

    def test_render_returns_array(self, env):
        env.reset()
        frame = env.render()
        assert isinstance(frame, np.ndarray)
        assert frame.ndim == 3
        assert frame.shape[2] == 3

    def test_gym_api_compliance(self, full_cfg):
        """Verify the env passes stable_baselines3 env checker."""
        try:
            from stable_baselines3.common.env_checker import check_env
            from src.simulation.airsim_env import AerialTrackingEnv
            env = AerialTrackingEnv(full_cfg)
            check_env(env, warn=True)  # should not raise
        except ImportError:
            pytest.skip("stable-baselines3 not installed")


# ─── AirSimClient (mock) ─────────────────────────────────────────────────────

class TestAirSimClientMock:
    @pytest.fixture
    def client(self):
        from src.simulation.airsim_env import AirSimClient
        # AirSim not running → should fall back to mock automatically
        return AirSimClient(ip="127.0.0.1", port=41451)

    def test_get_frame_shape(self, client):
        frame = client.get_frame()
        assert frame.ndim == 3
        assert frame.shape[2] == 3
        assert frame.dtype == np.uint8

    def test_get_state_returns_drone_state(self, client):
        from src.simulation.airsim_env import DroneState
        state = client.get_state()
        assert isinstance(state, DroneState)
        assert state.position.shape == (3,)
        assert state.velocity.shape == (3,)
        assert 0.0 <= state.battery_level <= 1.0

    def test_move_does_not_raise_in_mock(self, client):
        client.move(1.0, 0.0, 0.0, 0.0)

    def test_reset_does_not_raise_in_mock(self, client):
        client.reset()
