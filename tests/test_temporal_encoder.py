"""
tests/test_temporal_encoder.py
Phase 02: Unit tests for TemporalStateEncoder.
"""

import pytest
import torch
import numpy as np
from src.models.temporal_encoder import TemporalStateEncoder

def test_output_shape():
    encoder = TemporalStateEncoder(input_dim=83, hidden_dim=128, seq_len=10)
    # Batch size 1, Seq len 10, Input dim 83
    x = torch.randn(1, 10, 83)
    out = encoder(x)
    assert out.shape == (1, 128)

def test_cold_start_padding():
    encoder = TemporalStateEncoder(input_dim=83, hidden_dim=128, seq_len=10)
    state = np.ones(83)
    
    # 1st step: history has only 1 item
    context = encoder.get_context(state)
    assert context.shape == (128,)
    assert len(encoder.history) == 1
    
    # After 15 steps, history should be capped at 10
    for _ in range(14):
        encoder.get_context(state)
    assert len(encoder.history) == 10

def test_enriched_state_dim():
    encoder = TemporalStateEncoder(input_dim=83, hidden_dim=128, seq_len=10)
    state = np.random.rand(83)
    enriched = encoder.get_enriched_state(state)
    assert enriched.shape == (83 + 128,) # 211
    assert enriched.shape[0] == 211

def test_gradient_flow():
    encoder = TemporalStateEncoder(input_dim=83, hidden_dim=128, seq_len=10)
    x = torch.randn(1, 10, 83, requires_grad=True)
    out = encoder(x)
    loss = out.sum()
    loss.backward()
    assert x.grad is not None
    # Check GRU weights have grads
    for param in encoder.gru.parameters():
        assert param.grad is not None

def test_reset():
    encoder = TemporalStateEncoder(input_dim=83, hidden_dim=128, seq_len=10)
    state = np.ones(83)
    encoder.get_context(state)
    assert len(encoder.history) == 1
    encoder.reset()
    assert len(encoder.history) == 0
