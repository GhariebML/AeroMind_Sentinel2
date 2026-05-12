"""
src.rewards — Reward computation modules.

Provides the extended reward function with obstacle avoidance
and target proximity terms for real-time RL adaptation.
"""

from src.rewards.rt_reward import RealTimeRewardComputer

__all__ = ["RealTimeRewardComputer"]
