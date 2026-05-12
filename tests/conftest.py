"""
tests/conftest.py
Shared pytest fixtures for the AeroMind AI DroneTracking test suite.
Centralising fixtures here eliminates duplication across test files.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pytest


# ─── Configuration fixtures ───────────────────────────────────────────────────

@pytest.fixture(scope="session")
def base_cfg() -> dict:
    """
    Minimal but structurally complete config dictionary.
    Shared across detection, tracking, simulation, and RL tests.
    """
    return {
        "airsim": {
            "ip": "127.0.0.1",
            "port": 41451,
            "camera_name": "front_center",
            "frame_rate": 6,
            "environments": [
                "dense_urban", "highway", "parking_lot",
                "airport_apron", "campus", "mixed_terrain",
            ],
            "drone": {
                "start_altitude": -30,
                "max_altitude": -60,
                "max_speed": 15.0,
            },
        },
        "detection": {
            "model": "yolov8n",
            "weights": "models/detection/nonexistent.pt",
            "input_size": 640,
            "confidence_threshold": 0.5,
            "nms_iou_threshold": 0.45,
            "classes": {0: "vehicle", 1: "pedestrian", 2: "aircraft"},
            "sahi": {
                "enabled": False,
                "slice_height": 320,
                "slice_width": 320,
                "overlap_height_ratio": 0.2,
                "overlap_width_ratio": 0.2,
            },
            "training": {
                "epochs": 1,
                "batch_size": 2,
                "lr0": 0.001,
                "lrf": 0.00001,
                "warmup_epochs": 1,
                "augmentation": {
                    "mosaic": True,
                    "mixup": 0.1,
                    "random_scale": [0.5, 1.5],
                    "motion_blur": True,
                    "brightness_jitter": 0.3,
                    "contrast_jitter": 0.3,
                    "perspective": 0.2,
                },
                "dataset_split": [0.7, 0.15, 0.15],
                "target_frames": 100,
            },
        },
        "reid": {
            "model": "osnet_x0_25",
            "weights": "models/reid/nonexistent.pt",
            "embedding_dim": 256,
            "training": {
                "epochs": 1,
                "batch_size": 4,
                "lr": 0.0003,
                "loss": "triplet",
                "triplet_margin": 0.5,
                "mining": "hard",
                "warmup_steps": 10,
            },
        },
        "tracking": {
            "tracker": "botsort",
            "kalman": {
                "process_noise_scale": 1.0,
                "measurement_noise_scale": 1.0,
            },
            "iou_threshold": 0.3,
            "reid_cosine_threshold": 0.4,
            "iou_weight": 0.5,
            "reid_weight": 0.5,
            "max_age": 30,
            "min_hits": 3,
            "use_reid": False,
            "reid_freq": 1,
        },
        "rl": {
            "algorithm": "PPO",
            "policy": "MlpPolicy",
            "policy_kwargs": {"net_arch": [64, 64], "activation_fn": "tanh"},
            "learning_rate": 3e-4,
            "n_steps": 64,
            "batch_size": 16,
            "n_epochs": 2,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "clip_range": 0.2,
            "ent_coef": 0.01,
            "vf_coef": 0.5,
            "max_grad_norm": 0.5,
            "total_timesteps": 256,
            "episode_length": 20,
            "n_episodes_eval": 1,
            "eval_freq": 100,
            "reward": {"alpha": 5.0, "beta": 0.1, "gamma": 0.05},
            "state": {
                "use_drone_pose": True,
                "use_battery": True,
                "use_active_tracks": True,
                "heatmap_size": 8,
                "use_track_duration_hist": True,
            },
            "action": {
                "max_forward_vel": 10.0,
                "max_vertical_vel": 3.0,
                "max_yaw_rate": 45.0,
            },
        },
        "energy": {
            "c1": 0.10,
            "c2": 0.05,
            "c3": 0.20,
            "c4": 0.02,
            "battery_capacity_joules": 500.0,
        },
        "logging": {
            "level": "WARNING",   # suppress output during tests
            "log_dir": "experiments/logs",
            "checkpoint_dir": "experiments/checkpoints",
            "results_dir": "experiments/results",
            "tensorboard": False,
            "wandb": {"enabled": False, "project": "test", "entity": "test"},
            "save_freq": 100,
            "video_freq": 500,
        },
    }


# ─── Frame fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def dummy_frame() -> np.ndarray:
    """640×640 synthetic RGB frame."""
    return np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)


@pytest.fixture
def small_frame() -> np.ndarray:
    """320×320 RGB frame for lightweight tests."""
    return np.random.randint(0, 255, (320, 320, 3), dtype=np.uint8)


# ─── Detection fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def make_detection():
    """Factory function for creating Detection objects."""
    def _make(x1: float, y1: float, x2: float, y2: float,
               cls: int = 0, conf: float = 0.9):
        from src.detection.detector import Detection
        class_names = {0: "vehicle", 1: "pedestrian", 2: "aircraft"}
        return Detection(
            bbox=np.array([x1, y1, x2, y2], dtype=np.float32),
            confidence=conf,
            class_id=cls,
            class_name=class_names.get(cls, "unknown"),
        )
    return _make


# ─── Tracking fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def fresh_tracker(base_cfg):
    """
    A clean BotSortTracker with Re-ID disabled and reset ID counter.
    Used for tests that need a deterministic, fresh tracker state.
    """
    pytest.importorskip("filterpy")
    from src.tracking.tracker import BotSortTracker, KalmanBoxTracker
    KalmanBoxTracker.count = 0
    return BotSortTracker(base_cfg["tracking"])


# ─── Environment fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def mock_env(base_cfg):
    """
    AerialTrackingEnv in mock mode — no AirSim, no detector, no tracker.
    Suitable for Gymnasium API and reward tests.
    """
    from src.simulation.airsim_env import AerialTrackingEnv
    return AerialTrackingEnv(base_cfg)


# ─── Energy fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def fresh_energy():
    """A reset EnergyAccumulator for energy model unit tests."""
    from src.simulation.airsim_env import EnergyAccumulator
    ea = EnergyAccumulator()
    ea.reset()
    return ea
