"""
src.control — Real-time flight control layer.

Wraps the frozen PPO base policy with a learnable OnlineAdapter
to produce corrected actions in the 22 Hz control loop.
"""

from src.control.rt_controller import RealTimeFlightController

__all__ = ["RealTimeFlightController"]
