"""
src/simulation/platform.py
Hardware Abstraction Layer (HAL) for the AeroMind AI Drone Platform.

Defines the abstract interface that all drone backends must implement.
This decouples the RL agent, detection pipeline, and tracking logic
from any specific hardware or simulator.

Supported implementations:
  - AirSimClient  (src/simulation/airsim_env.py)  — simulation
  - [Future] MAVLinkPlatform                       — physical drone via PX4/ArduPilot

Usage:
    from src.simulation.platform import BaseDronePlatform
    # Any class inheriting BaseDronePlatform can be plugged into AerialTrackingEnv.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Shared data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DroneState:
    """
    Snapshot of the drone's kinematic state at a single point in time.
    Units: metres, m/s, degrees, seconds.
    """
    position:      np.ndarray = field(default_factory=lambda: np.zeros(3))
    velocity:      np.ndarray = field(default_factory=lambda: np.zeros(3))
    heading_deg:   float      = 0.0
    battery_level: float      = 1.0   # Fraction [0, 1]
    timestamp:     float      = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Abstract base class — the Hardware Abstraction Layer
# ─────────────────────────────────────────────────────────────────────────────

class BaseDronePlatform(ABC):
    """
    Abstract interface that every drone backend must implement.

    The RL environment (AerialTrackingEnv) exclusively uses this interface,
    which means swapping AirSim for a real physical drone requires only
    implementing this class — zero changes to the RL code.

    Required subclass implementations:
        get_frame()  -> np.ndarray
        get_state()  -> DroneState
        move(...)    -> None
        reset()      -> None
        land()       -> None

    Optional overrides:
        set_weather(...)
        close()
    """

    # ── Core API (must be implemented) ────────────────────────────────────────

    @abstractmethod
    def get_frame(self) -> np.ndarray:
        """
        Capture and return the current camera frame.

        Returns:
            np.ndarray: RGB image, shape (H, W, 3), dtype uint8.
        """
        ...

    @abstractmethod
    def get_state(self) -> DroneState:
        """
        Return the drone's current kinematic state.

        Returns:
            DroneState: position, velocity, heading, battery, timestamp.
        """
        ...

    @abstractmethod
    def move(self,
             vx: float,
             vy: float,
             vz: float,
             yaw_rate: float,
             duration: float = 0.2) -> None:
        """
        Command the drone to move at given velocities.

        Args:
            vx:       Forward velocity (m/s, body frame).
            vy:       Lateral velocity (m/s, body frame).
            vz:       Vertical velocity (m/s, world frame, positive = up).
            yaw_rate: Yaw rotation rate (deg/s, positive = clockwise).
            duration: Duration of the command (seconds).
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """
        Reset the drone to its initial state and take off.
        Called at the start of each RL episode.
        """
        ...

    @abstractmethod
    def land(self) -> None:
        """Command the drone to land safely."""
        ...

    # ── Optional extensions ────────────────────────────────────────────────────

    def set_weather(self, weather: str) -> None:
        """
        Apply a weather preset to the environment.

        Args:
            weather: One of 'clear', 'rain', 'fog', 'night'.

        Default implementation is a no-op. Simulators should override.
        Physical drones naturally experience real weather, so no override needed.
        """
        pass  # no-op by default

    def close(self) -> None:
        """
        Gracefully disconnect from the platform.
        Override for platforms that maintain a persistent connection.
        """
        pass

    # ── Introspection ─────────────────────────────────────────────────────────

    @property
    def is_mock(self) -> bool:
        """
        Returns True if this platform is a pure software simulation with
        no dependency on physical hardware or an external simulator.
        Used by the dashboard to display 'MOCK' vs 'LIVE' status.
        """
        return False

    @property
    def platform_name(self) -> str:
        """Human-readable name of this platform backend."""
        return self.__class__.__name__
