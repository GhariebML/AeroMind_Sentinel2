# AeroMind AI — State Space Documentation

## Overview
The AeroMind AI RL navigation agent uses an 83-dimensional continuous state vector to perceive its environment and the status of the drone. This vector is computed at each flight step (~6Hz) and serves as the input to the PPO policy.

## Dimension Mapping

| Dimensions | Feature | Range / Normalization | Source |
|------------|---------|-----------------------|--------|
| 0–2 | Drone Position (NED) | Scaled by 1/100 | `DroneState.position` |
| 3–5 | Drone Velocity (NED) | Scaled by 1/15 | `DroneState.velocity` |
| 6 | Drone Heading | Scaled by 1/360 (Degrees) | `DroneState.heading_deg` |
| 7 | Battery Level | [0, 1] Normalized | `EnergyAccumulator.remaining_fraction` |
| 8 | Active Track Count | Scaled by 1/20 | `len(tracks)` |
| 9–72 | Target Density Heatmap | 8x8 grid, [0, 1] Normalized | `AerialTrackingEnv._build_heatmap` |
| 73–82 | Track Duration Hist | 10 bins, [0, 1] Normalized | `AerialTrackingEnv._build_duration_hist` |

## Feature Details

### Target Density Heatmap (64-dim)
The 640x640 camera frame is projected onto an 8x8 grid. Each cell contains the count of active tracks whose bounding box centers fall within that grid cell. The entire heatmap is normalized by its maximum value to keep the input within a stable range for the neural network.

### Track Duration Histogram (10-dim)
This feature provides the agent with a sense of "track stability". It is a 10-bin histogram of the ages (in frames) of all active tracks. The bins range from 0 to 300 frames. Like the heatmap, it is normalized by the maximum bin value.

### Normalization Constants
- **Position**: 100.0 (Assumes typical operation within a 100m radius)
- **Velocity**: 15.0 m/s (Max speed of the drone)
- **Heading**: 360.0 degrees
- **Tracks**: 20 (Typical maximum number of simultaneous targets)
