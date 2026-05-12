"""
src.system — Top-level system integration.

Contains the AeroMindRealTimeSystem entry point that wires
perception, tracking, navigation, and control into a unified
22 Hz real-time loop.
"""

from src.system.aeromind_rt import AeroMindRealTimeSystem

__all__ = ["AeroMindRealTimeSystem"]
