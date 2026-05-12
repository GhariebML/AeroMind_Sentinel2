"""
src/models/online_adapter.py
Phase 03: Online Adapter for real-time policy correction.

A lightweight 2-layer MLP that sits on top of the frozen PPO and
learns real-time delta corrections. The frozen base policy provides
stability; the adapter provides adaptability.
"""

import torch
import torch.nn as nn

class OnlineAdapter(nn.Module):
    """
    A 2-layer MLP that learns real-time delta corrections to the base PPO policy.
    Input: 83-dim state vector.
    Output: 3-dim action delta (forward_vel, vertical_vel, yaw_rate).
    """
    def __init__(self, input_dim: int = 83, hidden_dim: int = 64, output_dim: int = 3):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, output_dim),
            nn.Tanh()
        )
        # Learnable scalar initialized to 0.1 to scale adapter influence
        self.alpha = nn.Parameter(torch.tensor(0.1))
        
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        Returns the scaled delta action.
        """
        delta = self.mlp(state)
        return self.alpha * delta

    def __repr__(self) -> str:
        return (f"OnlineAdapter(input=83, hidden=64, output=3, "
                f"alpha={self.alpha.item():.4f})")
