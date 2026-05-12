import numpy as np
import math
from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger

@dataclass
class SwarmTrack:
    global_id: int
    class_name: str
    last_seen_time: float
    drone_source: str
    reid_embedding: Optional[np.ndarray] = None
    ground_x: float = 0.0
    ground_y: float = 0.0

class DistributedSwarmManager:
    """
    Centralised manager that receives tracks from multiple drones
    and merges them into a global tracking database using Re-ID embeddings
    and ground-plane spatial proximity.
    """
    def __init__(self, cosine_threshold: float = 0.8, distance_threshold: float = 20.0):
        self.cosine_threshold = cosine_threshold
        self.distance_threshold = distance_threshold
        
        # global_id -> SwarmTrack
        self.global_tracks: Dict[int, SwarmTrack] = {}
        self._next_global_id = 1
        
        # Mapping from (drone_name, local_id) -> global_id
        self.local_to_global: Dict[str, Dict[int, int]] = {}

    def register_drone(self, drone_name: str):
        if drone_name not in self.local_to_global:
            self.local_to_global[drone_name] = {}
            logger.info(f"[SwarmManager] Registered {drone_name}")

    def _cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        if emb1 is None or emb2 is None:
            return 0.0
        return float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2) + 1e-6))

    def update_tracks(self, drone_name: str, local_tracks: List, current_time: float, drone_pos: np.ndarray = None, drone_yaw: float = 0.0):
        """
        Receives local tracks (from BoT-SORT on a specific drone), 
        assigns or retrieves their Global IDs, and updates the global registry.
        """
        self.register_drone(drone_name)
        drone_map = self.local_to_global[drone_name]
        
        updated_global_ids = []

        for t in local_tracks:
            local_id = t.id
            emb = t.reid_embedding
            
            # Simple ground projection (mock ray-casting for now, assuming flat ground)
            # In a real 3D environment, we project the 2D bounding box centre down.
            if drone_pos is not None and t.bbox is not None:
                # Estimate ground X, Y based on drone pos and rough bounding box centre
                # (This is a simplified projection)
                cx = (t.bbox[0] + t.bbox[2]) / 2
                cy = (t.bbox[1] + t.bbox[3]) / 2
                # Simple approximation: target is straight down + offset by pixel center
                offset_x = (cx - 320) * 0.05
                offset_y = (cy - 320) * 0.05
                # Rotate offset by drone yaw
                rad = math.radians(drone_yaw)
                rot_x = offset_x * math.cos(rad) - offset_y * math.sin(rad)
                rot_y = offset_x * math.sin(rad) + offset_y * math.cos(rad)
                
                ground_x = drone_pos[0] + rot_y
                ground_y = drone_pos[1] + rot_x
            else:
                ground_x, ground_y = 0.0, 0.0

            # 1. Do we already know this local ID for this drone?
            if local_id in drone_map:
                g_id = drone_map[local_id]
                self.global_tracks[g_id].last_seen_time = current_time
                self.global_tracks[g_id].drone_source = drone_name
                self.global_tracks[g_id].ground_x = ground_x
                self.global_tracks[g_id].ground_y = ground_y
                if emb is not None:
                    # Exponential moving average for the embedding
                    old_emb = self.global_tracks[g_id].reid_embedding
                    if old_emb is not None:
                        new_emb = 0.9 * old_emb + 0.1 * emb
                        new_emb /= np.linalg.norm(new_emb)
                        self.global_tracks[g_id].reid_embedding = new_emb
                    else:
                        self.global_tracks[g_id].reid_embedding = emb
                updated_global_ids.append(g_id)
                t.global_id = g_id  # Inject global ID into local track
                continue

            # 2. Try to match with existing global tracks using Re-ID and Spatial distance
            best_g_id = None
            best_score = -1.0
            
            for g_id, g_track in self.global_tracks.items():
                if g_track.class_name != t.class_name:
                    continue
                    
                # Time decay (if not seen recently, it's a stronger candidate for Re-ID)
                time_diff = current_time - g_track.last_seen_time
                if time_diff > 30.0: # Track is very old, ignore
                    continue
                
                # Spatial distance
                dist = math.sqrt((ground_x - g_track.ground_x)**2 + (ground_y - g_track.ground_y)**2)
                
                # Cosine similarity
                sim = self._cosine_similarity(emb, g_track.reid_embedding)
                
                # Match logic: High similarity OR very close spatially
                if sim > self.cosine_threshold or (dist < self.distance_threshold and time_diff < 2.0):
                    if sim > best_score:
                        best_score = sim
                        best_g_id = g_id

            if best_g_id is not None:
                # Matched!
                drone_map[local_id] = best_g_id
                self.global_tracks[best_g_id].last_seen_time = current_time
                self.global_tracks[best_g_id].drone_source = drone_name
                self.global_tracks[best_g_id].ground_x = ground_x
                self.global_tracks[best_g_id].ground_y = ground_y
                t.global_id = best_g_id
                updated_global_ids.append(best_g_id)
                logger.debug(f"[SwarmManager] {drone_name} Track {local_id} -> Matched Global {best_g_id} (sim: {best_score:.2f})")
            else:
                # Create new Global Track
                new_g_id = self._next_global_id
                self._next_global_id += 1
                self.global_tracks[new_g_id] = SwarmTrack(
                    global_id=new_g_id,
                    class_name=t.class_name,
                    last_seen_time=current_time,
                    drone_source=drone_name,
                    reid_embedding=emb,
                    ground_x=ground_x,
                    ground_y=ground_y
                )
                drone_map[local_id] = new_g_id
                t.global_id = new_g_id
                updated_global_ids.append(new_g_id)
                logger.debug(f"[SwarmManager] {drone_name} Track {local_id} -> Created Global {new_g_id}")

        # Return the assigned global IDs
        return updated_global_ids

    def get_all_active_tracks(self, current_time: float, timeout: float = 5.0) -> List[SwarmTrack]:
        """Returns all global tracks seen within the last `timeout` seconds."""
        active = []
        for t in self.global_tracks.values():
            if current_time - t.last_seen_time <= timeout:
                active.append(t)
        return active
