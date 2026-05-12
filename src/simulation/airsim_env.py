"""
src/simulation/airsim_env.py
AirSim implementation of the BaseDronePlatform HAL.

Connects to Unreal Engine via the AirSim RPC API, captures frames,
executes drone velocity commands, and exposes a Gymnasium-compatible
step API for PPO training.

Rich mock mode generates animated synthetic targets (sinusoidal paths)
so the full perception pipeline can run without AirSim installed.

To swap to a physical drone, replace AirSimClient with a class that
inherits from BaseDronePlatform — zero RL code changes required.
"""

from __future__ import annotations

import json
import math
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import cv2

from src.simulation.platform import BaseDronePlatform, DroneState
import gymnasium as gym
from gymnasium import spaces
from loguru import logger

# ── Ensure vendor/ is on path so airsim + msgpackrpc shim are available ───────
_VENDOR = Path(__file__).resolve().parent.parent.parent / "vendor"
if str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

try:
    import airsim
    AIRSIM_AVAILABLE = True
except ImportError:
    AIRSIM_AVAILABLE = False
    logger.warning("AirSim not installed — running in mock mode.")


# Import Track here so _run_perception returns the correct type
try:
    from src.tracking.tracker import Track
except ImportError:
    from dataclasses import dataclass as _dc
    @_dc
    class Track:          # type: ignore
        id: int = 0
        bbox: object = None
        class_id: int = 0
        class_name: str = "vehicle"
        confidence: float = 0.9
        age: int = 0
        hits: int = 1
        time_since_update: int = 0
        reid_embedding: object = None


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

# DroneState is now imported from src.simulation.platform (HAL)
# It remains accessible here for backwards-compatibility with other modules.
# from src.simulation.platform import DroneState  (already imported above)


@dataclass
class EnergyAccumulator:
    """E_total ≈ c1·L + c2·v̄² + c3·Δz + c4·T_fly"""
    c1: float = 0.10
    c2: float = 0.05
    c3: float = 0.20
    c4: float = 0.02
    battery_capacity_joules: float = 500.0

    _consumed: float  = field(default=0.0,  init=False, repr=False)
    _prev_pos: Optional[np.ndarray] = field(default=None, init=False, repr=False)
    _prev_time: Optional[float]     = field(default=None, init=False, repr=False)

    def reset(self) -> None:
        self._consumed  = 0.0
        self._prev_pos  = None
        self._prev_time = None

    def update(self, pos: np.ndarray, vel: np.ndarray, t: float) -> float:
        if self._prev_pos is None:
            self._prev_pos  = pos.copy()
            self._prev_time = t
            return 0.0
        dt    = max(t - self._prev_time, 1e-6)
        dl    = float(np.linalg.norm(pos - self._prev_pos))
        speed = float(np.linalg.norm(vel))
        dz    = abs(float(pos[2] - self._prev_pos[2]))
        delta = self.c1*dl + self.c2*speed**2 + self.c3*dz + self.c4*dt
        self._consumed += delta
        self._prev_pos  = pos.copy()
        self._prev_time = t
        return delta

    @property
    def consumed(self) -> float:
        return self._consumed

    @property
    def remaining_fraction(self) -> float:
        return max(0.0, 1.0 - self._consumed / self.battery_capacity_joules)


# ─────────────────────────────────────────────────────────────────────────────
# Rich synthetic scene generator (mock mode)
# ─────────────────────────────────────────────────────────────────────────────

class SyntheticScene:
    """
    Generates realistic-looking aerial frames with moving targets.
    Each target follows a sinusoidal path; colours differ by class.
    This allows the full YOLOv8 + BoT-SORT pipeline to run on synthetic data.
    """

    _CLASS_COLORS = {
        "vehicle":    (180, 220, 60),
        "pedestrian": (240, 140, 50),
        "aircraft":   (60,  180, 240),
    }
    _CLASS_NAMES = ["vehicle", "pedestrian", "aircraft"]

    def __init__(self, width: int = 640, height: int = 640, n_targets: int = 12, seed: int = 42):
        self.w, self.h = width, height
        self.rng = np.random.default_rng(seed)

        # Per-target state: [cx, cy, vx, vy, w, h, class_idx, phase_x, phase_y, freq]
        self._targets: list[dict] = []
        for i in range(n_targets):
            cls = int(self.rng.integers(0, 3))
            sz  = 60 if cls == 0 else (25 if cls == 1 else 45)
            self._targets.append({
                "id":      i,
                "cx":      float(self.rng.uniform(80, width  - 80)),
                "cy":      float(self.rng.uniform(80, height - 80)),
                "amp_x":   float(self.rng.uniform(50, 180)),
                "amp_y":   float(self.rng.uniform(50, 180)),
                "phase_x": float(self.rng.uniform(0, 2*math.pi)),
                "phase_y": float(self.rng.uniform(0, 2*math.pi)),
                "freq":    float(self.rng.uniform(0.3, 1.2)),
                "w":       sz + int(self.rng.integers(-10, 10)),
                "h":       sz + int(self.rng.integers(-10, 10)),
                "cls":     cls,
                "class_name": self._CLASS_NAMES[cls],
            })
        self._t = 0.0

    def step(self, dt: float = 0.1) -> np.ndarray:
        """Advance simulation by dt seconds; return RGB frame (H, W, 3)."""
        self._t += dt
        # Background — dark asphalt look
        frame = np.full((self.h, self.w, 3), (55, 60, 65), dtype=np.uint8)
        # Road grid lines
        for x in range(0, self.w, 80):
            cv2.line(frame, (x, 0), (x, self.h), (70, 75, 78), 1)
        for y in range(0, self.h, 80):
            cv2.line(frame, (0, y), (self.w, y), (70, 75, 78), 1)
        # Main roads
        cv2.line(frame, (self.w//2, 0), (self.w//2, self.h), (90, 95, 100), 3)
        cv2.line(frame, (0, self.h//2), (self.w, self.h//2), (90, 95, 100), 3)

        # Draw targets
        for tgt in self._targets:
            cx = tgt["cx"] + tgt["amp_x"] * math.sin(tgt["freq"] * self._t + tgt["phase_x"])
            cy = tgt["cy"] + tgt["amp_y"] * math.cos(tgt["freq"] * self._t + tgt["phase_y"])
            cx = np.clip(cx, tgt["w"]//2+1, self.w - tgt["w"]//2 - 1)
            cy = np.clip(cy, tgt["h"]//2+1, self.h - tgt["h"]//2 - 1)
            tgt["_cx"] = cx
            tgt["_cy"] = cy
            x1 = int(cx - tgt["w"] // 2)
            y1 = int(cy - tgt["h"] // 2)
            x2 = int(cx + tgt["w"] // 2)
            y2 = int(cy + tgt["h"] // 2)
            col = self._CLASS_COLORS[tgt["class_name"]]
            # Shadow
            cv2.rectangle(frame, (x1+3, y1+3), (x2+3, y2+3), (30, 30, 30), -1)
            # Target body
            cv2.rectangle(frame, (x1, y1), (x2, y2), col, -1)
            # Highlight edge
            cv2.rectangle(frame, (x1, y1), (x2, y2), tuple(min(255, c+60) for c in col), 1)

        weather = getattr(self, "weather", "clear")
        if weather == "night":
            frame = (frame * 0.3).astype(np.uint8)
        elif weather == "fog":
            frame = cv2.addWeighted(frame, 0.5, np.full_like(frame, 200), 0.5, 0)
        elif weather == "rain":
            # simple rain effect
            frame = cv2.addWeighted(frame, 0.8, np.full_like(frame, 100), 0.2, 0)
            noise = self.rng.integers(100, 255, (self.h//4, self.w//4, 1), dtype=np.uint8)
            noise = cv2.resize(noise, (self.w, self.h))
            frame[noise > 240] = 255

        # Subtle noise (grain)
        noise = self.rng.integers(-10, 10, frame.shape, dtype=np.int16)
        frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        return frame

    def set_weather(self, weather_str: str):
        self.weather = weather_str

    def get_gt_bboxes(self) -> list[dict]:
        """Ground-truth bboxes for current frame (used by mock perception)."""
        out = []
        for tgt in self._targets:
            if "_cx" not in tgt:
                continue
            cx, cy = tgt["_cx"], tgt["_cy"]
            out.append({
                "id":    tgt["id"],
                "bbox":  np.array([cx-tgt["w"]//2, cy-tgt["h"]//2,
                                   cx+tgt["w"]//2, cy+tgt["h"]//2], dtype=np.float32),
                "class_id":   tgt["cls"],
                "class_name": tgt["class_name"],
            })
        return out


# ─────────────────────────────────────────────────────────────────────────────
# AirSim Client wrapper
# ─────────────────────────────────────────────────────────────────────────────

class AirSimClient(BaseDronePlatform):
    """
    AirSim implementation of the BaseDronePlatform HAL.

    Wraps the AirSim Python RPC API.  Automatically falls back to
    SyntheticScene mock mode when AirSim is not installed or unreachable.
    """

    def __init__(self, ip: str = "127.0.0.1", port: int = 41451,
                 camera_name: str = "front_center", vehicle_name: str = "Drone1"):
        self.camera_name = camera_name
        self.vehicle_name = vehicle_name
        self._mock = not AIRSIM_AVAILABLE
        self._scene = SyntheticScene()  # always ready for mock fallback
        self._drone_pos = np.zeros(3)
        self._drone_vel = np.zeros(3)
        self._heading   = 0.0

        if not self._mock:
            try:
                self._client = airsim.MultirotorClient(ip=ip, port=port)
                self._client.confirmConnection()
                self._client.enableApiControl(True, vehicle_name=self.vehicle_name)
                self._client.armDisarm(True, vehicle_name=self.vehicle_name)
                logger.success(f"Connected to AirSim at {ip}:{port} for {self.vehicle_name}")
            except Exception as e:
                logger.warning(f"AirSim connection failed ({e}) — switching to mock mode.")
                self._mock = True
        else:
            logger.info("AirSim mock mode — using rich SyntheticScene.")

    def set_weather(self, weather_str: str) -> None:
        if self._mock:
            self._scene.set_weather(weather_str)
            return
        
        # Reset weather
        self._client.simSetWeatherParameter(airsim.WeatherParameter.Rain, 0)
        self._client.simSetWeatherParameter(airsim.WeatherParameter.Fog, 0)
        self._client.simSetWeatherParameter(airsim.WeatherParameter.Dust, 0)
        
        if weather_str == "rain":
            self._client.simSetWeatherParameter(airsim.WeatherParameter.Rain, 0.8)
            self._client.simSetWeatherParameter(airsim.WeatherParameter.Fog, 0.2)
        elif weather_str == "fog":
            self._client.simSetWeatherParameter(airsim.WeatherParameter.Fog, 0.8)
        elif weather_str == "night":
            # Optional time of day adjustment if enabled in UE
            pass

    # ── Frame ─────────────────────────────────────────────────────────────────

    def get_frame(self) -> np.ndarray:
        """Returns RGB frame (H, W, 3) uint8."""
        if self._mock:
            return self._scene.step(dt=0.1)
        responses = self._client.simGetImages([
            airsim.ImageRequest(self.camera_name, airsim.ImageType.Scene, False, False)
        ], vehicle_name=self.vehicle_name)
        img   = responses[0]
        frame = np.frombuffer(img.image_data_uint8, dtype=np.uint8)
        frame = frame.reshape(img.height, img.width, 3)
        return frame.copy()

    # ── State ─────────────────────────────────────────────────────────────────

    def get_state(self) -> DroneState:
        if self._mock:
            # Simulate gentle circular hover
            t = time.time()
            self._drone_pos = np.array([
                20*math.sin(0.1*t), 20*math.cos(0.1*t), -30.0
            ])
            self._drone_vel = np.array([
                2*math.cos(0.1*t), -2*math.sin(0.1*t), 0.0
            ])
            return DroneState(
                position    = self._drone_pos.copy(),
                velocity    = self._drone_vel.copy(),
                heading_deg = (math.degrees(0.1*t)) % 360,
                battery_level = 1.0,
                timestamp   = t,
            )
        s   = self._client.getMultirotorState(vehicle_name=self.vehicle_name)
        pos = s.kinematics_estimated.position
        vel = s.kinematics_estimated.linear_velocity
        o   = s.kinematics_estimated.orientation
        yaw = math.atan2(
            2*(o.w_val*o.z_val + o.x_val*o.y_val),
            1 - 2*(o.y_val**2 + o.z_val**2)
        )
        return DroneState(
            position    = np.array([pos.x_val, pos.y_val, pos.z_val]),
            velocity    = np.array([vel.x_val, vel.y_val, vel.z_val]),
            heading_deg = math.degrees(yaw) % 360,
            battery_level = 1.0,
            timestamp   = time.time(),
        )

    # ── Control ───────────────────────────────────────────────────────────────

    def move(self, vx: float, vy: float, vz: float,
             yaw_rate: float, duration: float = 0.2) -> None:
        if self._mock:
            return
        self._client.moveByVelocityAsync(
            vx, vy, vz, duration,
            drivetrain=airsim.DrivetrainType.MaxDegreeOfFreedom,
            yaw_mode=airsim.YawMode(is_rate=True, yaw_or_rate=yaw_rate),
            vehicle_name=self.vehicle_name
        ).join()

    def reset(self) -> None:
        if self._mock:
            self._scene = SyntheticScene()
            return
        self._client.reset()
        self._client.enableApiControl(True, vehicle_name=self.vehicle_name)
        self._client.armDisarm(True, vehicle_name=self.vehicle_name)
        self._client.takeoffAsync(vehicle_name=self.vehicle_name).join()

    def land(self) -> None:
        if not self._mock:
            self._client.landAsync(vehicle_name=self.vehicle_name).join()

    def close(self) -> None:
        """Disconnect from AirSim gracefully."""
        if not self._mock:
            try:
                self._client.enableApiControl(False, vehicle_name=self.vehicle_name)
            except Exception:
                pass

    @property
    def is_mock(self) -> bool:
        return self._mock

    @property
    def platform_name(self) -> str:
        return f"AirSim[{self.vehicle_name}]" + (" (mock)" if self._mock else "")

    @property
    def synthetic_scene(self) -> SyntheticScene:
        return self._scene


# ─────────────────────────────────────────────────────────────────────────────
# Gymnasium Environment
# ─────────────────────────────────────────────────────────────────────────────

class AerialTrackingEnv(gym.Env):
    """
    Custom Gymnasium environment for PPO training.

    State vector:
        [pos(3), vel(3), heading(1), battery(1), n_tracks(1),
         heatmap(64), track_dur_hist(10)]  → 83-dim

    Action space (continuous):
        [forward_vel, vertical_vel, yaw_rate]
    """

    metadata = {"render_modes": ["rgb_array"]}

    def __init__(self, cfg: dict, detector=None, tracker=None, vehicle_name: str = "Drone1"):
        super().__init__()
        self.cfg         = cfg
        self._detector   = detector
        self._tracker    = tracker
        self.vehicle_name = vehicle_name

        rl_cfg = cfg["rl"]
        self._episode_length = rl_cfg["episode_length"]
        self._alpha      = rl_cfg["reward"]["alpha"]
        self._beta       = rl_cfg["reward"]["beta"]
        self._gamma      = rl_cfg["reward"]["gamma"]
        self._heatmap_size = rl_cfg["state"]["heatmap_size"]

        self._energy  = EnergyAccumulator(**cfg["energy"])
        self._client  = AirSimClient(
            ip          = cfg["airsim"]["ip"],
            port        = cfg["airsim"]["port"],
            camera_name = cfg["airsim"]["camera_name"],
            vehicle_name = self.vehicle_name,
        )

        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)

        obs_dim = 3 + 3 + 1 + 1 + 1 + self._heatmap_size**2 + 10
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32
        )

        self._step_count  = 0
        self._prev_tracks: dict = {}
        self._last_frame:  Optional[np.ndarray] = None
        self._last_tracks: list = []
        self._last_info:   dict = {}

    # ── Gymnasium interface ───────────────────────────────────────────────────

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self._client.reset()
        self._energy.reset()
        self._step_count  = 0
        self._prev_tracks = {}
        self._last_tracks = []
        self._last_info   = {}
        obs = self._get_obs()
        return obs, {}

    def step(self, action: np.ndarray) -> Tuple:
        rl_cfg = self.cfg["rl"]["action"]
        vx = float(action[0]) * rl_cfg["max_forward_vel"]
        vz = float(action[1]) * rl_cfg["max_vertical_vel"]
        yr = float(action[2]) * rl_cfg["max_yaw_rate"]
        self._client.move(vx, 0.0, vz, yr)

        # ── Dynamic Weather Check ──
        weather_file = Path("experiments/results/weather_control.json").resolve()
        if weather_file.exists():
            try:
                mt = weather_file.stat().st_mtime
                if not hasattr(self, "_last_weather_mtime") or mt > self._last_weather_mtime:
                    self._last_weather_mtime = mt
                    import json
                    with open(weather_file) as f:
                        w = json.load(f).get("weather", "clear")
                    self._client.set_weather(w)
            except Exception:
                pass

        frame       = self._client.get_frame()
        drone_state = self._client.get_state()
        self._last_frame = frame

        tracks      = self._run_perception(frame)
        self._last_tracks = tracks
        n_tracks    = len(tracks)

        energy_delta = self._energy.update(
            drone_state.position, drone_state.velocity, drone_state.timestamp
        )
        id_switches = self._count_id_switches(tracks)

        reward = (self._alpha * n_tracks
                  - self._beta  * energy_delta
                  - self._gamma * id_switches)

        self._prev_tracks = {t.id: t for t in tracks}
        self._step_count += 1

        obs        = self._build_obs(drone_state, tracks, frame)
        terminated = self._energy.remaining_fraction <= 0.0
        truncated  = self._step_count >= self._episode_length

        info = {
            "n_tracks":        n_tracks,
            "energy_consumed": self._energy.consumed,
            "battery_remaining": self._energy.remaining_fraction,
            "id_switches":     id_switches,
            "step":            self._step_count,
            "is_mock":         self._client.is_mock,
            "pos_x":           float(drone_state.position[0]),
            "pos_y":           float(drone_state.position[1]),
            "pos_z":           float(drone_state.position[2]),
            "vel_x":           float(drone_state.velocity[0]),
            "vel_y":           float(drone_state.velocity[1]),
            "heading_deg":     float(drone_state.heading_deg),
        }
        self._last_info = info
        return obs, reward, terminated, truncated, info

    def render(self):
        if self._last_frame is not None:
            return self._last_frame
        return np.zeros((640, 640, 3), dtype=np.uint8)

    # ── Telemetry property (for dashboard) ────────────────────────────────────

    @property
    def telemetry(self) -> dict:
        """JSON-serialisable telemetry snapshot."""
        info = self._last_info
        return {
            "n_tracks":        info.get("n_tracks", 0),
            "energy_J":        round(info.get("energy_consumed", 0.0), 2),
            "battery_pct":     round(info.get("battery_remaining", 1.0) * 100, 1),
            "pos_x":           round(info.get("pos_x", 0.0), 2),
            "pos_y":           round(info.get("pos_y", 0.0), 2),
            "pos_z":           round(info.get("pos_z", 0.0), 2),
            "vel_x":           round(info.get("vel_x", 0.0), 2),
            "vel_y":           round(info.get("vel_y", 0.0), 2),
            "heading_deg":     round(info.get("heading_deg", 0.0), 1),
            "step":            info.get("step", 0),
            "is_mock":         info.get("is_mock", True),
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _run_perception(self, frame: np.ndarray) -> List[Track]:
        """Run detector + tracker; returns list of Track objects."""

        # ── Mock mode: use SyntheticScene ground-truth bboxes ────────────────
        if self._client.is_mock:
            gt = self._client.synthetic_scene.get_gt_bboxes()
            # Feed GT as Detection objects into the real tracker (if available)
            # so we get persistent Kalman-filtered track IDs
            if self._tracker is not None and gt:
                try:
                    from src.detection.detector import Detection
                    dets = [
                        Detection(
                            bbox=b["bbox"],
                            confidence=0.95,
                            class_id=b["class_id"],
                            class_name=b["class_name"],
                        )
                        for b in gt
                    ]
                    tracks = self._tracker.update(dets, frame)
                    if tracks:
                        return tracks
                except Exception:
                    pass
            # Fallback: return simple Track objects from GT directly
            class_names = ["vehicle", "pedestrian", "aircraft"]
            return [
                Track(
                    id=b["id"],
                    bbox=b["bbox"],
                    class_id=b["class_id"],
                    class_name=b["class_name"],
                    confidence=0.95,
                    age=self._step_count,
                    hits=max(1, self._step_count),
                )
                for b in gt
            ]

        # ── Real mode: no detector/tracker ────────────────────────────────────
        if self._detector is None or self._tracker is None:
            n   = np.random.randint(0, 15)
            rng = np.random.default_rng()
            class_names = ["vehicle", "pedestrian", "aircraft"]
            return [
                Track(
                    id=i,
                    bbox=rng.integers(0, 600, size=4).astype(float),
                    class_id=int(rng.integers(0, 3)),
                    class_name=class_names[int(rng.integers(0, 3))],
                    confidence=round(float(rng.uniform(0.5, 0.99)), 2),
                    age=int(rng.integers(0, 50)),
                )
                for i in range(n)
            ]

        # ── Real mode: full pipeline ───────────────────────────────────────────
        detections = self._detector.detect(frame)
        tracks     = self._tracker.update(detections, frame)
        return tracks


    def _build_obs(self, state: DroneState, tracks: list,
                   frame: np.ndarray) -> np.ndarray:
        pos_norm     = state.position / 100.0
        vel_norm     = state.velocity / 15.0
        heading_norm = np.array([state.heading_deg / 360.0])
        battery      = np.array([self._energy.remaining_fraction])
        n_tracks     = np.array([len(tracks) / 20.0])

        heatmap      = self._build_heatmap(tracks, frame.shape[:2])
        dur_hist     = self._build_duration_hist(tracks)

        return np.concatenate([
            pos_norm, vel_norm, heading_norm, battery, n_tracks,
            heatmap.flatten(), dur_hist
        ]).astype(np.float32)

    def _get_obs(self) -> np.ndarray:
        frame  = self._client.get_frame()
        state  = self._client.get_state()
        tracks = self._run_perception(frame)
        self._last_frame  = frame
        self._last_tracks = tracks
        return self._build_obs(state, tracks, frame)

    def _build_heatmap(self, tracks: List[Track],
                       frame_shape: Tuple[int, int]) -> np.ndarray:
        h, w = frame_shape
        hm   = np.zeros((self._heatmap_size, self._heatmap_size), dtype=np.float32)
        for t in tracks:
            bbox = t.bbox
            cx = int((bbox[0] + bbox[2]) / 2 / w * self._heatmap_size)
            cy = int((bbox[1] + bbox[3]) / 2 / h * self._heatmap_size)
            cx = np.clip(cx, 0, self._heatmap_size - 1)
            cy = np.clip(cy, 0, self._heatmap_size - 1)
            hm[cy, cx] += 1.0
        if hm.max() > 0:
            hm /= hm.max()
        return hm

    def _build_duration_hist(self, tracks: List[Track], bins: int = 10) -> np.ndarray:
        durations = [t.age for t in tracks]
        if not durations:
            return np.zeros(bins, dtype=np.float32)
        hist, _ = np.histogram(durations, bins=bins, range=(0, 300))
        return (hist / max(hist.max(), 1)).astype(np.float32)

    def _count_id_switches(self, current_tracks: List[Track]) -> int:
        if not self._prev_tracks:
            return 0
        switches = 0
        for t in current_tracks:
            if t.id in self._prev_tracks:
                if self._prev_tracks[t.id].class_id != t.class_id:
                    switches += 1
        return switches
