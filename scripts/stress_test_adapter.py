"""
scripts/stress_test_adapter.py
Phase 03: Stress test the OnlineAdapter and RealTimeFlightController.
"""

import torch
import numpy as np
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.control.rt_controller import RealTimeFlightController

class MockBasePolicy:
    def predict(self, state, deterministic=True):
        # Returns a random action in [-1, 1]
        return np.random.uniform(-1, 1, size=(3,)), None

def stress_test():
    print("Starting Phase 03 Stress Test (1000 steps)...")
    
    base_policy = MockBasePolicy()
    controller = RealTimeFlightController(base_policy)
    
    # Track alpha value
    initial_alpha = controller.adapter.alpha.item()
    print(f"Initial Alpha: {initial_alpha:.4f}")
    
    # TensorBoard setup (simulated for this environment if tb not installed)
    try:
        from torch.utils.tensorboard import SummaryWriter
        writer = SummaryWriter("runs/adapter")
        TB_AVAILABLE = True
    except ImportError:
        print("TensorBoard not installed — skipping TB logging.")
        TB_AVAILABLE = False

    for i in range(1000):
        state = np.random.randn(83)
        action = controller.predict(state)
        
        # Simulate reward (simple distance-based or random)
        reward = -np.linalg.norm(action) + 0.5 # Encourage small actions
        
        next_state = np.random.randn(83)
        done = False
        
        controller.store_transition(state, action, reward, next_state, done)
        
        if (i + 1) % 100 == 0:
            current_alpha = controller.adapter.alpha.item()
            print(f"Step {i+1:4d} | Alpha: {current_alpha:.4f}")
            if TB_AVAILABLE:
                writer.add_scalar("Adapter/Alpha", current_alpha, i)
    
    final_alpha = controller.adapter.alpha.item()
    print(f"Final Alpha: {final_alpha:.4f}")
    
    if abs(final_alpha) > 10.0:
        print("FAILURE: Alpha exploded!")
        sys.exit(1)
    else:
        print("SUCCESS: Alpha stable.")
        
    if TB_AVAILABLE:
        writer.close()

if __name__ == "__main__":
    stress_test()
