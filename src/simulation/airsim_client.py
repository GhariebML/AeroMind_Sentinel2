"""
src/simulation/airsim_client.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Unified AirSim client — works transparently in both real and mock mode.

Real mode  : connects to AirSim Unreal Engine at 127.0.0.1:41451
Mock mode  : uses SyntheticScene (fully animated synthetic environment)

The AerialTrackingEnv imports this module so the rest of the code
never needs to know whether AirSim is connected or not.

Usage:
    client = AirSimClientWrapper(use_mock=False)   # auto-fallback on error
    frame  = client.get_camera_frame()             # np.ndarray H×W×3
    state  = client.get_drone_state()              # DroneState
    client.send_velocity(vx=1.0, vy=0.0, vz=0.0, yaw_rate=0.0, duration=0.1)
"""
from __future__ import annotations

import time
import math
import threading
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from loguru import logger


# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class DroneState:
    position:    np.ndarray = field(default_factory=lambda: np.zeros(3))
    velocity:    np.ndarray = field(default_factory=lambda: np.zeros(3))
    orientation: np.ndarray = field(default_factory=lambda: np.zeros(4))  # quaternion
    heading_deg: float      = 0.0
    timestamp:   float      = 0.0


@dataclass
class BoundingBox:
    id:         int
    bbox:       list[float]   # [x1, y1, x2, y2]
    class_id:   int
    class_name: str
    confidence: float = 0.95


# ─── Synthetic Scene ──────────────────────────────────────────────────────────

class SyntheticScene:
    """
    Generates a convincing aerial tracking environment without Unreal Engine.
    Renders:
      - Dark asphalt ground grid
      - Animated coloured targets (vehicles, pedestrians, aircraft)
      - Sinusoidal + random-walk motion
    """

    COLOURS = [
        (  0, 230, 122),   # teal-green
        (255, 107,  53),   # orange
        ( 86, 180, 233),   # sky blue
        (240, 228,  66),   # yellow
        (204, 121, 167),   # purple-pink
        (  0, 158, 115),   # dark teal
        (213,  94,   0),   # burnt orange
        (  0, 114, 178),   # royal blue
    ]

    CLASS_MAP = {0: "vehicle", 1: "pedestrian", 2: "aircraft"}

    def __init__(self, n_targets: int = 12, canvas_size: tuple = (640, 640)):
        self.n = n_targets
        self.W, self.H = canvas_size
        self._t     = 0.0
        self._lock  = threading.Lock()

        rng = np.random.default_rng(42)

        # Target state: [cx, cy, w, h, vx, vy, phase, class_id]
        self._targets = []
        for i in range(n_targets):
            cx   = rng.uniform(60, self.W - 60)
            cy   = rng.uniform(60, self.H - 60)
            cid  = int(rng.integers(0, 3))
            spd  = rng.uniform(0.3, 2.0)
            size = (40, 20) if cid == 0 else (15, 15) if cid == 1 else (50, 30)
            self._targets.append({
                "cx": cx, "cy": cy, "w": size[0], "h": size[1],
                "vx": rng.choice([-1, 1]) * spd,
                "vy": rng.choice([-1, 1]) * spd * rng.uniform(0.3, 1.0),
                "phase": rng.uniform(0, 2 * math.pi),
                "class_id": cid,
                "colour": self.COLOURS[i % len(self.COLOURS)],
                "id": i,
            })

    def step(self, dt: float = 1/30):
        """Advance simulation by dt seconds."""
        with self._lock:
            self._t += dt
            for t in self._targets:
                # Sinusoidal cross-component for curved paths
                t["cx"] += t["vx"] + 0.5 * math.sin(self._t * 0.5 + t["phase"])
                t["cy"] += t["vy"] + 0.5 * math.cos(self._t * 0.7 + t["phase"])
                # Bounce off walls
                pad = 40
                if t["cx"] < pad or t["cx"] > self.W - pad:
                    t["vx"] *= -1
                    t["cx"] = max(pad, min(self.W - pad, t["cx"]))
                if t["cy"] < pad or t["cy"] > self.H - pad:
                    t["vy"] *= -1
                    t["cy"] = max(pad, min(self.H - pad, t["cy"]))

    def get_frame(self) -> np.ndarray:
        """Render and return a 640×640 BGR frame."""
        import cv2
        with self._lock:
            # Background: dark asphalt with grid
            frame = np.full((self.H, self.W, 3), 30, dtype=np.uint8)
            # Grid lines
            for x in range(0, self.W, 80):
                cv2.line(frame, (x, 0), (x, self.H), (45, 45, 45), 1)
            for y in range(0, self.H, 80):
                cv2.line(frame, (0, y), (self.W, y), (45, 45, 45), 1)

            # Draw targets
            for t in self._targets:
                cx, cy = int(t["cx"]), int(t["cy"])
                hw, hh = int(t["w"]//2), int(t["h"]//2)
                x1, y1 = cx - hw, cy - hh
                x2, y2 = cx + hw, cy + hh
                col = tuple(int(c) for c in t["colour"])
                cv2.rectangle(frame, (x1, y1), (x2, y2), col, -1)   # filled
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255,255,255), 1)  # outline

            return frame.copy()

    def get_gt_bboxes(self) -> list[dict]:
        """Return ground-truth bounding boxes for direct tracker injection."""
        with self._lock:
            result = []
            for t in self._targets:
                cx, cy = t["cx"], t["cy"]
                hw, hh = t["w"] / 2, t["h"] / 2
                result.append({
                    "id":         t["id"],
                    "bbox":       [cx - hw, cy - hh, cx + hw, cy + hh],
                    "class_id":   t["class_id"],
                    "class_name": self.CLASS_MAP[t["class_id"]],
                    "confidence": 0.95,
                })
            return result


# ─── Real AirSim client (lazy-imported) ───────────────────────────────────────

class _RealAirSimClient:
    """Thin wrapper around the airsim Python client for the Multirotor API."""

    def __init__(self, host: str = "127.0.0.1", port: int = 41451,
                 camera: str = "front_center", vehicle: str = "Drone1"):
        import airsim
        self._as   = airsim
        self._c    = airsim.MultirotorClient(ip=host, port=port)
        self.camera  = camera
        self.vehicle = vehicle

        self._c.confirmConnection()
        self._c.enableApiControl(True, vehicle_name=vehicle)
        self._c.armDisarm(True, vehicle_name=vehicle)
        self._c.takeoffAsync(timeout_sec=10, vehicle_name=vehicle).join()
        logger.success(f"AirSim connected: {host}:{port} | vehicle={vehicle}")

    def get_frame(self) -> np.ndarray:
        import airsim
        resp = self._c.simGetImages(
            [airsim.ImageRequest(self.camera, airsim.ImageType.Scene, False, False)],
            vehicle_name=self.vehicle
        )
        if not resp or resp[0].width == 0:
            return np.zeros((640, 640, 3), dtype=np.uint8)
        img1d = np.frombuffer(resp[0].image_data_uint8, dtype=np.uint8)
        return img1d.reshape(resp[0].height, resp[0].width, 3).copy()

    def get_state(self) -> DroneState:
        import airsim
        s = self._c.getMultirotorState(vehicle_name=self.vehicle)
        pos = s.kinematics_estimated.position
        vel = s.kinematics_estimated.linear_velocity
        ori = s.kinematics_estimated.orientation
        # Yaw from quaternion
        yaw = math.degrees(math.atan2(
            2*(ori.w*ori.z + ori.x*ori.y),
            1 - 2*(ori.y**2 + ori.z**2)
        ))
        return DroneState(
            position    = np.array([pos.x_val, pos.y_val, pos.z_val]),
            velocity    = np.array([vel.x_val, vel.y_val, vel.z_val]),
            orientation = np.array([ori.w, ori.x, ori.y, ori.z]),
            heading_deg = yaw,
            timestamp   = time.time(),
        )

    def send_velocity(self, vx: float, vy: float, vz: float,
                      yaw_rate: float, duration: float = 0.1):
        self._c.moveByVelocityAsync(
            vx, vy, vz,
            duration=duration,
            yaw_mode=self._as.YawMode(is_rate=True, yaw_or_rate=yaw_rate),
            vehicle_name=self.vehicle,
        )

    def reset(self):
        self._c.reset()
        self._c.enableApiControl(True, vehicle_name=self.vehicle)
        self._c.armDisarm(True, vehicle_name=self.vehicle)
        self._c.takeoffAsync(timeout_sec=10, vehicle_name=self.vehicle).join()


# ─── Unified wrapper ───────────────────────────────────────────────────────────

class AirSimClientWrapper:
    """
    Single entry-point for AirSim interaction.

    Automatically falls back to SyntheticScene if:
      - use_mock=True is passed explicitly, OR
      - AirSim connection fails (auto-fallback)
    """

    def __init__(self, use_mock: bool = False,
                 host: str = "127.0.0.1", port: int = 41451,
                 camera: str = "front_center", vehicle: str = "Drone1",
                 n_targets: int = 12, canvas_size: tuple = (640, 640)):

        self.is_mock = use_mock
        self.synthetic_scene: Optional[SyntheticScene] = None
        self._real: Optional[_RealAirSimClient] = None
        self._step_dt = 1/30

        # Drone state for mock mode
        self._mock_state = DroneState(
            position    = np.array([0.0, 0.0, -10.0]),
            velocity    = np.zeros(3),
            orientation = np.array([1.0, 0.0, 0.0, 0.0]),
            heading_deg = 0.0,
            timestamp   = time.time(),
        )
        self._mock_energy_J   = 0.0
        self._mock_battery_pct = 100.0

        if not use_mock:
            try:
                self._real = _RealAirSimClient(host, port, camera, vehicle)
                logger.info("AirSim real mode active.")
            except Exception as exc:
                logger.warning(f"AirSim connection failed ({exc}) — switching to mock mode.")
                self.is_mock = True

        if self.is_mock:
            self.synthetic_scene = SyntheticScene(
                n_targets=n_targets, canvas_size=canvas_size
            )
            logger.info(f"Mock mode: SyntheticScene with {n_targets} targets.")

    # ── Public API ─────────────────────────────────────────────────────────

    def get_camera_frame(self) -> np.ndarray:
        if self.is_mock:
            self.synthetic_scene.step(self._step_dt)
            return self.synthetic_scene.get_frame()
        return self._real.get_frame()

    def get_drone_state(self) -> DroneState:
        if self.is_mock:
            return self._mock_state
        return self._real.get_state()

    def send_velocity(self, vx: float, vy: float, vz: float,
                      yaw_rate: float, duration: float = 0.1):
        if self.is_mock:
            self._update_mock_state(vx, vy, vz, yaw_rate, duration)
        else:
            self._real.send_velocity(vx, vy, vz, yaw_rate, duration)

    def reset(self):
        if self.is_mock:
            self._mock_state = DroneState(
                position    = np.array([0.0, 0.0, -10.0]),
                velocity    = np.zeros(3),
                orientation = np.array([1.0, 0.0, 0.0, 0.0]),
                heading_deg = 0.0,
                timestamp   = time.time(),
            )
            self._mock_energy_J    = 0.0
            self._mock_battery_pct = 100.0
            if self.synthetic_scene:
                self.synthetic_scene._t = 0.0
        else:
            self._real.reset()

    @property
    def energy_J(self) -> float:
        return self._mock_energy_J

    @property
    def battery_pct(self) -> float:
        return self._mock_battery_pct

    # ── Internal helpers ───────────────────────────────────────────────────

    def _update_mock_state(self, vx, vy, vz, yaw_rate, dt):
        """Integrate velocity commands into mock drone state."""
        s = self._mock_state
        s.velocity = np.array([vx, vy, vz])
        s.position = s.position + s.velocity * dt
        s.heading_deg = (s.heading_deg + math.degrees(yaw_rate) * dt) % 360.0
        s.timestamp = time.time()

        # Simple energy model: E = (|v| + hover) * dt * mass
        speed  = float(np.linalg.norm(s.velocity))
        HOVER_W = 50.0   # watts at hover
        MOVE_W  = 30.0   # extra watts per m/s
        power  = HOVER_W + MOVE_W * speed
        self._mock_energy_J += power * dt
        self._mock_battery_pct = max(0.0, 100.0 - self._mock_energy_J / 5.0)
