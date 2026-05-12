"""
scripts/pretrain_gru.py
Phase 02: Pre-train the GRU-based temporal encoder on synthetic/recorded trajectories.
"""

import torch
import torch.optim as optim
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.models.temporal_encoder import TemporalStateEncoder

def generate_synthetic_data(num_samples=5000, seq_len=10, input_dim=83):
    """
    Generates synthetic trajectories where the next state is a noisy function 
    of the previous ones, allowing the GRU to learn temporal dependencies.
    """
    X = np.zeros((num_samples, seq_len, input_dim))
    Y = np.zeros((num_samples, input_dim))
    
    for i in range(num_samples):
        # Initial random state
        state = np.random.randn(input_dim)
        for t in range(seq_len):
            X[i, t] = state
            # Simple random walk with some trend
            state = 0.95 * state + 0.05 * np.random.randn(input_dim)
        Y[i] = state
        
    return torch.from_numpy(X).float(), torch.from_numpy(Y).float()

def train():
    print("Initializing Phase 02: GRU Pre-training...")
    input_dim = 83
    hidden_dim = 128
    seq_len = 10
    
    encoder = TemporalStateEncoder(input_dim, hidden_dim, seq_len)
    
    # We add a small predictor head for pre-training (reconstruction task)
    predictor = nn.Sequential(
        nn.Linear(hidden_dim, 256),
        nn.ReLU(),
        nn.Linear(256, input_dim)
    )
    
    X, Y = generate_synthetic_data()
    dataset = TensorDataset(X, Y)
    loader = DataLoader(dataset, batch_size=64, shuffle=True)
    
    optimizer = optim.Adam(list(encoder.parameters()) + list(predictor.parameters()), lr=0.001)
    criterion = nn.MSELoss()
    
    epochs = 5
    for epoch in range(epochs):
        total_loss = 0
        for batch_x, batch_y in loader:
            optimizer.zero_grad()
            context = encoder(batch_x)
            pred = predictor(context)
            loss = criterion(pred, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        print(f"Epoch {epoch+1}/{epochs} | Loss: {total_loss/len(loader):.6f}")
        
    # Save weights
    save_path = ROOT / "checkpoints" / "gru_pretrained.pt"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(encoder.state_dict(), save_path)
    print(f"DONE: Pre-trained GRU weights saved to {save_path}")

if __name__ == "__main__":
    train()
