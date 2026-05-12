"""
src/models/temporal_encoder.py
Phase 02: GRU-based temporal encoder for state history.
"""

import torch
import torch.nn as nn
from collections import deque
import numpy as np

class TemporalStateEncoder(nn.Module):
    """
    Encodes the last 10 flight steps into a context vector using a GRU.
    Input: 83-dim state vector.
    Hidden: 128-dim context vector.
    Sequence Length: 10.
    """
    def __init__(self, input_dim: int = 83, hidden_dim: int = 128, seq_len: int = 10):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.seq_len = seq_len
        
        self.gru = nn.GRU(input_dim, hidden_dim, batch_first=True)
        self.history = deque(maxlen=seq_len)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: (batch, seq_len, input_dim)
        Returns: (batch, hidden_dim) last hidden state
        """
        _, h_n = self.gru(x)
        return h_n[-1] # (batch, hidden_dim)

    def get_context(self, current_state: np.ndarray) -> np.ndarray:
        """
        Main interface for the RL loop.
        Maintains internal history and returns the 128-dim context vector.
        """
        # 1. Update history
        self.history.append(current_state)
        
        # 2. Prepare sequence (pad with zeros if history < seq_len)
        seq = list(self.history)
        if len(seq) < self.seq_len:
            padding = [np.zeros(self.input_dim) for _ in range(self.seq_len - len(seq))]
            seq = padding + seq
            
        # 3. Convert to torch tensor (batch=1)
        seq_tensor = torch.from_numpy(np.array(seq)).float().unsqueeze(0)
        
        # 4. Forward pass
        with torch.no_grad():
            context = self.forward(seq_tensor).squeeze(0).cpu().numpy()
            
        return context

    def reset(self):
        """Clear history for new episodes."""
        self.history.clear()
        
    def get_enriched_state(self, current_state: np.ndarray) -> np.ndarray:
        """
        Returns the concatenated [state, context] vector (211-dim).
        """
        context = self.get_context(current_state)
        return np.concatenate([current_state, context])
