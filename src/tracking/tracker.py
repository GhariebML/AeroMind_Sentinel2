"""
src/tracking/tracker.py
BoT-SORT multi-object tracker with Re-ID appearance module.
Implements the tracking pipeline described in the AeroMind AI technical report.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
from loguru import logger

from src.detection.detector import Detection


# ─────────────────────────────────────────────────────────────────────────────
# Kalman Filter (simplified for 2D bounding box state)
# ─────────────────────────────────────────────────────────────────────────────

class KalmanBoxTracker:
    """
    Constant-velocity Kalman filter for bounding box tracking.
    State: [cx, cy, s, r, dcx, dcy, ds]  (center_x, center_y, scale, ratio, velocities)
    """

    count = 0

    def __init__(self, bbox: np.ndarray, class_id: int = 0,
                 class_name: str = "vehicle", confidence: float = 1.0):
        from filterpy.kalman import KalmanFilter

        self.kf = KalmanFilter(dim_x=7, dim_z=4)
        self.kf.F = np.eye(7)
        self.kf.F[0, 4] = 1.0  # cx += dcx
        self.kf.F[1, 5] = 1.0  # cy += dcy
        self.kf.F[2, 6] = 1.0  # s += ds

        self.kf.H = np.zeros((4, 7))
        for i in range(4):
            self.kf.H[i, i] = 1.0

        self.kf.R[2:, 2:] *= 10.0   # measurement noise
        self.kf.P[4:, 4:] *= 1000.0 # velocity uncertainty
        self.kf.Q[-1, -1] *= 0.01
        self.kf.Q[4:, 4:] *= 0.01

        self.kf.x[:4] = self._bbox_to_z(bbox)

        KalmanBoxTracker.count += 1
        self.id = KalmanBoxTracker.count
        self.hits = 1
        self.hit_streak = 1
        self.age = 0
        self.time_since_update = 0
        self.history: List[np.ndarray] = []
        self.reid_embedding: Optional[np.ndarray] = None
        # Class metadata — updated on every successful match
        self.class_id: int = class_id
        self.class_name: str = class_name
        self.confidence: float = confidence

    def predict(self) -> np.ndarray:
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        self.age += 1
        self.kf.predict()
        self.history.append(self._z_to_bbox(self.kf.x))
        return self.history[-1]

    def update(self, bbox: np.ndarray,
               embedding: Optional[np.ndarray] = None,
               class_id: Optional[int] = None,
               class_name: Optional[str] = None,
               confidence: Optional[float] = None) -> None:
        self.time_since_update = 0
        self.hits += 1
        self.hit_streak += 1
        self.kf.update(self._bbox_to_z(bbox))
        # Update class metadata from matched detection
        if class_id is not None:
            self.class_id = class_id
        if class_name is not None:
            self.class_name = class_name
        if confidence is not None:
            self.confidence = confidence
        if embedding is not None:
            alpha = 0.9  # EMA update for Re-ID embedding
            if self.reid_embedding is None:
                self.reid_embedding = embedding
            else:
                self.reid_embedding = alpha * self.reid_embedding + (1 - alpha) * embedding
                self.reid_embedding /= np.linalg.norm(self.reid_embedding) + 1e-6

    def get_state(self) -> np.ndarray:
        return self._z_to_bbox(self.kf.x)

    @staticmethod
    def _bbox_to_z(bbox: np.ndarray) -> np.ndarray:
        x1, y1, x2, y2 = bbox
        w, h = x2 - x1, y2 - y1
        cx, cy = x1 + w / 2, y1 + h / 2
        s = w * h
        r = w / max(h, 1e-6)
        return np.array([[cx], [cy], [s], [r]])

    @staticmethod
    def _z_to_bbox(x: np.ndarray) -> np.ndarray:
        cx = float(x[0].item()) if hasattr(x[0], 'item') else float(x[0])
        cy = float(x[1].item()) if hasattr(x[1], 'item') else float(x[1])
        s  = float(x[2].item()) if hasattr(x[2], 'item') else float(x[2])
        r  = float(x[3].item()) if hasattr(x[3], 'item') else float(x[3])
        w = np.sqrt(max(s * r, 0))
        h = max(s / max(w, 1e-6), 0)
        return np.array([cx - w/2, cy - h/2, cx + w/2, cy + h/2])


# ─────────────────────────────────────────────────────────────────────────────
# Re-ID Module
# ─────────────────────────────────────────────────────────────────────────────

class ReIDModule:
    """
    Lightweight Re-ID using OSNet or FastReID.
    Extracts 256-dim normalized embeddings from detected crops.
    """

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.embed_dim = cfg["embedding_dim"]
        self.model = None
        self._load_model(cfg["weights"])

    def _load_model(self, weights_path: str) -> None:
        try:
            import torch
            from pathlib import Path
            path = Path(weights_path)
            if path.exists():
                self.model = self._build_osnet()
                state = torch.load(path, map_location="cpu")
                self.model.load_state_dict(state, strict=False)
                self.model.eval()
                logger.info(f"Loaded Re-ID model from {path}")
            else:
                logger.warning("Re-ID weights not found — using random embeddings (dev mode).")
        except Exception as e:
            logger.warning(f"Re-ID load failed: {e} — using random embeddings.")

    def _build_osnet(self):
        """Build lightweight OSNet backbone."""
        try:
            import torchreid
            model = torchreid.models.build_model(
                name="osnet_x0_25",
                num_classes=1000,
                loss="softmax",
                pretrained=True,
            )
            return model
        except ImportError:
            return None

    def extract(self, frame: np.ndarray,
                bboxes: List[np.ndarray]) -> List[Optional[np.ndarray]]:
        """Extract embeddings for all bounding boxes in the frame."""
        embeddings = []
        for bbox in bboxes:
            crop = self._crop(frame, bbox)
            emb = self._embed(crop)
            embeddings.append(emb)
        return embeddings

    def _crop(self, frame: np.ndarray, bbox: np.ndarray) -> np.ndarray:
        import cv2
        x1, y1, x2, y2 = bbox.astype(int)
        x1, y1 = max(x1, 0), max(y1, 0)
        x2, y2 = min(x2, frame.shape[1]), min(y2, frame.shape[0])
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            crop = np.zeros((64, 32, 3), dtype=np.uint8)
        return cv2.resize(crop, (128, 256))

    def _embed(self, crop: np.ndarray) -> np.ndarray:
        if self.model is None:
            # Dev mode: deterministic random based on crop content
            rng = np.random.default_rng(int(crop.mean() * 1000))
            emb = rng.standard_normal(self.embed_dim).astype(np.float32)
            emb /= np.linalg.norm(emb) + 1e-6
            return emb

        import torch
        import torchvision.transforms as T
        transform = T.Compose([
            T.ToPILImage(),
            T.Resize((256, 128)),
            T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        tensor = transform(crop).unsqueeze(0)
        with torch.no_grad():
            emb = self.model(tensor).squeeze().cpu().numpy()
        emb /= np.linalg.norm(emb) + 1e-6
        return emb


# ─────────────────────────────────────────────────────────────────────────────
# BoT-SORT Tracker
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Track:
    id: int
    bbox: np.ndarray
    class_id: int
    class_name: str
    confidence: float
    age: int = 0
    hits: int = 1
    time_since_update: int = 0
    reid_embedding: Optional[np.ndarray] = None


class BotSortTracker:
    """
    BoT-SORT: Robust multi-object tracker combining:
    - Kalman filter for motion prediction
    - IoU-based spatial cost
    - Re-ID cosine similarity for appearance cost
    - Hungarian algorithm for optimal assignment

    Reference: Aharon et al., arXiv:2206.14651
    """

    def __init__(self, cfg: dict, reid_module: Optional[ReIDModule] = None):
        self.iou_thresh = cfg["iou_threshold"]
        self.reid_thresh = cfg["reid_cosine_threshold"]
        self.iou_w = cfg["iou_weight"]
        self.reid_w = cfg["reid_weight"]
        self.max_age = cfg["max_age"]
        self.min_hits = cfg["min_hits"]
        self.use_reid = cfg.get("use_reid", True) and reid_module is not None
        self.reid = reid_module

        self._trackers: List[KalmanBoxTracker] = []
        self._frame_count = 0
        self._id_switch_count = 0

    # ── Public API ────────────────────────────────────────────────────────────

    def update(self, detections: List[Detection],
               frame: np.ndarray) -> List[Track]:
        """
        Main tracking step. Returns confirmed tracks for this frame.
        """
        self._frame_count += 1

        # 1. Predict all existing tracks forward
        predicted_boxes = []
        alive = []
        for trk in self._trackers:
            pred = trk.predict()
            if not np.any(np.isnan(pred)):
                predicted_boxes.append(pred)
                alive.append(trk)
        self._trackers = alive

        # 2. Extract Re-ID embeddings for detections
        det_bboxes = [d.bbox for d in detections]
        embeddings = (self.reid.extract(frame, det_bboxes)
                      if self.use_reid and detections else
                      [None] * len(detections))

        # 3. Build cost matrix and associate
        matched, unmatched_dets, unmatched_trks = self._associate(
            detections, predicted_boxes, embeddings
        )

        # 4. Update matched trackers — propagate detection class info
        for det_idx, trk_idx in matched:
            det = detections[det_idx]
            self._trackers[trk_idx].update(
                det.bbox,
                embeddings[det_idx],
                class_id=det.class_id,
                class_name=det.class_name,
                confidence=det.confidence,
            )

        # 5. Create new trackers for unmatched detections
        for det_idx in unmatched_dets:
            det = detections[det_idx]
            trk = KalmanBoxTracker(
                det.bbox,
                class_id=det.class_id,
                class_name=det.class_name,
                confidence=det.confidence,
            )
            trk.reid_embedding = embeddings[det_idx]
            self._trackers.append(trk)

        # 6. Remove dead tracks
        self._trackers = [t for t in self._trackers
                          if t.time_since_update <= self.max_age]

        # 7. Build output: only confirmed tracks
        output: List[Track] = []
        for t in self._trackers:
            if t.hit_streak >= self.min_hits or self._frame_count <= self.min_hits:
                bbox = t.get_state()
                output.append(Track(
                    id=t.id,
                    bbox=bbox,
                    class_id=t.class_id,
                    class_name=t.class_name,
                    confidence=t.confidence,
                    age=t.age,
                    hits=t.hits,
                    time_since_update=t.time_since_update,
                    reid_embedding=t.reid_embedding,
                ))

        return output

    @property
    def active_track_count(self) -> int:
        return sum(1 for t in self._trackers if t.time_since_update == 0)

    # ── Association ───────────────────────────────────────────────────────────

    def _associate(
        self,
        detections: List[Detection],
        predicted_boxes: List[np.ndarray],
        embeddings: List[Optional[np.ndarray]],
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """Hungarian assignment with combined IoU + Re-ID cost."""
        if not detections or not predicted_boxes:
            return [], list(range(len(detections))), list(range(len(predicted_boxes)))

        from scipy.optimize import linear_sum_assignment

        n_dets = len(detections)
        n_trks = len(predicted_boxes)

        # IoU cost
        iou_cost = np.ones((n_dets, n_trks))
        for i, d in enumerate(detections):
            for j, p in enumerate(predicted_boxes):
                iou_cost[i, j] = 1.0 - self._iou(d.bbox, p)

        # Re-ID cosine cost
        reid_cost = np.ones((n_dets, n_trks))
        if self.use_reid:
            for i, emb in enumerate(embeddings):
                if emb is None:
                    continue
                for j, trk in enumerate(self._trackers[:n_trks]):
                    if trk.reid_embedding is not None:
                        cos_sim = float(np.dot(emb, trk.reid_embedding))
                        reid_cost[i, j] = 1.0 - max(cos_sim, 0.0)

        cost = self.iou_w * iou_cost + self.reid_w * reid_cost

        row_ind, col_ind = linear_sum_assignment(cost)

        matched, unmatched_dets, unmatched_trks = [], [], []
        for d in range(n_dets):
            if d not in row_ind:
                unmatched_dets.append(d)
        for t in range(n_trks):
            if t not in col_ind:
                unmatched_trks.append(t)

        for r, c in zip(row_ind, col_ind):
            if cost[r, c] > 0.7:   # threshold: discard poor matches
                unmatched_dets.append(r)
                unmatched_trks.append(c)
            else:
                matched.append((r, c))

        return matched, unmatched_dets, unmatched_trks

    @staticmethod
    def _iou(bb1: np.ndarray, bb2: np.ndarray) -> float:
        x1 = max(bb1[0], bb2[0]); y1 = max(bb1[1], bb2[1])
        x2 = min(bb1[2], bb2[2]); y2 = min(bb1[3], bb2[3])
        inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
        a1 = (bb1[2]-bb1[0]) * (bb1[3]-bb1[1])
        a2 = (bb2[2]-bb2[0]) * (bb2[3]-bb2[1])
        union = a1 + a2 - inter
        return inter / max(union, 1e-6)

    # ── Visualization ─────────────────────────────────────────────────────────

    def draw(self, frame: np.ndarray, tracks: List[Track]) -> np.ndarray:
        """Annotate frame with track bounding boxes and IDs."""
        import cv2
        out = frame.copy()
        rng = np.random.default_rng(0)
        colors = {tid: tuple(rng.integers(80, 230, 3).tolist())
                  for tid in range(500)}
        for t in tracks:
            x1, y1, x2, y2 = t.bbox.astype(int)
            color = colors.get(t.id % 500, (0, 255, 0))
            cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
            label = f"ID:{t.id} {t.class_name}"
            cv2.putText(out, label, (x1, max(y1 - 5, 14)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
        cv2.putText(out, f"Active tracks: {len(tracks)}", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return out
