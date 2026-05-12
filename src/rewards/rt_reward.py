import numpy as np

class RealTimeRewardComputer:
    """
    Computes an extended reward function in real-time, incorporating
    obstacle avoidance and optimal target proximity terms.
    """
    def __init__(self, alpha=5.0, beta=0.1, gamma=0.05, delta=2.0, eta=1.5):
        # Base weights from offline training
        self.alpha = alpha   # tracking quality (number of active tracks)
        self.beta  = beta    # energy cost
        self.gamma = gamma   # ID switches penalty
        
        # New real-time adaptation weights
        self.delta = delta   # obstacle avoidance penalty
        self.eta   = eta     # target proximity bonus
    
    def compute(self, telemetry: dict) -> float:
        """
        Calculate the joint reward for the current step.
        """
        T = telemetry.get("active_tracks", 0)
        E = self._energy(telemetry)
        P = telemetry.get("id_switches", 0)
        
        # Obstacle penalty from lidar or distance sensors
        O = self._obstacle_penalty(telemetry.get("lidar_distances", []))
        
        # Proximity bonus for staying in the "sweet spot"
        B = self._proximity_bonus(telemetry.get("target_distances", []))
        
        return (
            self.alpha * T
            - self.beta * E
            - self.gamma * P
            - self.delta * O
            + self.eta  * B
        )
    
    def _energy(self, t):
        """Estimate energy cost based on movement and speed."""
        # Simple energy model based on path length and velocity changes
        path_len = t.get("path_length", 0.0)
        speed    = t.get("speed", 0.0)
        alt_diff = abs(t.get("delta_altitude", 0.0))
        dt       = t.get("dt", 0.05)
        
        return (
            0.10 * path_len +
            0.05 * (speed ** 2) +
            0.20 * alt_diff +
            0.02 * dt
        )
    
    def _obstacle_penalty(self, distances):
        """Exponential penalty as drone gets close to obstacles (< 3m)."""
        if not distances:
            return 0.0
            
        min_d = min(distances)
        if min_d > 3.0:
            return 0.0
            
        # Squared penalty increases rapidly as distance approaches 0
        # Clamp max penalty at 9.0 (when min_d == 0)
        return min((3.0 - min_d) ** 2, 9.0)
    
    def _proximity_bonus(self, target_distances):
        """Reward for staying in the optimal tracking range (2-8m)."""
        if not target_distances:
            return 0.0
            
        bonuses = []
        for d in target_distances:
            if 2.0 <= d <= 8.0:
                bonuses.append(1.0) # Sweet spot
            elif d < 2.0:
                bonuses.append(0.3) # Too close (occlusion/collision risk)
            else:
                # Linear decay for targets getting further away
                # 0 reward at 18m
                bonuses.append(max(0, 1 - (d - 8) / 10))
                
        return sum(bonuses) / max(len(bonuses), 1)
