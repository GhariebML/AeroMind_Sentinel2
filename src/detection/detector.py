"""
src/detection/detector.py
YOLOv8/v10 detector with SAHI tiling for small aerial objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np
import cv2
from loguru import logger


@dataclass
class Detection:
    bbox: np.ndarray        # [x1, y1, x2, y2] in pixels
    confidence: float
    class_id: int
    class_name: str


CLASS_NAMES = {0: "vehicle", 1: "pedestrian", 2: "aircraft"}


class AerialDetector:
    """
    YOLOv8/v10 detector wrapper with optional SAHI tiling.

    Usage:
        detector = AerialDetector(cfg["detection"])
        detections = detector.detect(frame)
    """

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.conf_thresh = cfg["confidence_threshold"]
        self.nms_iou = cfg["nms_iou_threshold"]
        self.input_size = cfg["input_size"]
        self.use_sahi = cfg["sahi"]["enabled"]
        self.model = None
        self._sahi_warned = False
        self._load_model(cfg["weights"])

    # ── Public API ────────────────────────────────────────────────────────────

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Run detection on a single RGB frame."""
        if self.use_sahi:
            return self._detect_sahi(frame)
        return self._detect_full(frame)

    def detect_batch(self, frames: List[np.ndarray]) -> List[List[Detection]]:
        """Run detection on a batch of frames."""
        return [self.detect(f) for f in frames]

    # ── Internal ──────────────────────────────────────────────────────────────

    def _load_model(self, weights_path: str) -> None:
        try:
            from ultralytics import YOLO
            path = Path(weights_path)
            if path.exists():
                self.model = YOLO(str(path))
                logger.info(f"Loaded YOLO weights from {path}")
            else:
                # Fall back to pretrained weights for development
                self.model = YOLO("yolov8m.pt")
                logger.warning(f"Weights not found at {path} — using yolov8m pretrained.")
        except ImportError:
            logger.error("ultralytics not installed. Run: pip install ultralytics")
            self.model = None

    def _detect_full(self, frame: np.ndarray) -> List[Detection]:
        """Standard inference on the full frame."""
        if self.model is None:
            return self._mock_detections(frame)

        results = self.model.predict(
            frame,
            conf=self.conf_thresh,
            iou=self.nms_iou,
            imgsz=self.input_size,
            verbose=False,
        )
        return self._parse_results(results[0])

    def _detect_sahi(self, frame: np.ndarray) -> List[Detection]:
        """
        SAHI: run detector on overlapping slices, merge with NMS.
        Falls back to full-frame detection if sahi is not installed.
        """
        try:
            from sahi import AutoDetectionModel
            from sahi.predict import get_sliced_prediction
        except ImportError:
            if not self._sahi_warned:
                logger.warning("sahi not installed — using full-frame detection. "
                                "Install with: pip install sahi")
                self._sahi_warned = True
                self.use_sahi = False   # disable for all future calls
            return self._detect_full(frame)

        sahi_cfg = self.cfg["sahi"]
        # For SAHI we need a model path; fall back gracefully
        if self.model is None:
            return self._mock_detections(frame)

        result = get_sliced_prediction(
            image=frame,
            detection_model=self._get_sahi_model(),
            slice_height=sahi_cfg["slice_height"],
            slice_width=sahi_cfg["slice_width"],
            overlap_height_ratio=sahi_cfg["overlap_height_ratio"],
            overlap_width_ratio=sahi_cfg["overlap_width_ratio"],
            perform_standard_pred=True,
            postprocess_type="NMS",
            postprocess_match_threshold=self.nms_iou,
            verbose=0,
        )
        return self._parse_sahi_results(result)

    def _get_sahi_model(self):
        """Cache SAHI model wrapper."""
        if not hasattr(self, "_sahi_model"):
            from sahi import AutoDetectionModel
            self._sahi_model = AutoDetectionModel.from_pretrained(
                model_type="ultralytics",
                model=self.model,
                confidence_threshold=self.conf_thresh,
            )
        return self._sahi_model

    def _parse_results(self, result) -> List[Detection]:
        detections = []
        if result.boxes is None:
            return detections
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            if cls not in CLASS_NAMES:
                continue
            detections.append(Detection(
                bbox=np.array([x1, y1, x2, y2]),
                confidence=conf,
                class_id=cls,
                class_name=CLASS_NAMES[cls],
            ))
        return detections

    def _parse_sahi_results(self, result) -> List[Detection]:
        detections = []
        for obj in result.object_prediction_list:
            bbox = obj.bbox.to_xyxy()
            cls = obj.category.id
            if cls not in CLASS_NAMES:
                continue
            detections.append(Detection(
                bbox=np.array(bbox, dtype=np.float32),
                confidence=obj.score.value,
                class_id=cls,
                class_name=CLASS_NAMES[cls],
            ))
        return detections

    def _mock_detections(self, frame: np.ndarray) -> List[Detection]:
        """Generate random detections for testing without GPU."""
        h, w = frame.shape[:2]
        n = np.random.randint(0, 12)
        detections = []
        for i in range(n):
            x1 = np.random.randint(0, w - 50)
            y1 = np.random.randint(0, h - 50)
            x2 = x1 + np.random.randint(20, 80)
            y2 = y1 + np.random.randint(20, 80)
            cls = np.random.randint(0, 3)
            detections.append(Detection(
                bbox=np.array([x1, y1, x2, y2], dtype=np.float32),
                confidence=round(np.random.uniform(0.5, 0.99), 2),
                class_id=cls,
                class_name=CLASS_NAMES[cls],
            ))
        return detections

    # ── Visualization ─────────────────────────────────────────────────────────

    def draw(self, frame: np.ndarray,
             detections: List[Detection]) -> np.ndarray:
        """Draw bounding boxes on frame (BGR expected for OpenCV)."""
        colors = {0: (0, 255, 100), 1: (255, 180, 0), 2: (0, 150, 255)}
        out = frame.copy()
        for d in detections:
            x1, y1, x2, y2 = d.bbox.astype(int)
            color = colors.get(d.class_id, (200, 200, 200))
            cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
            label = f"{d.class_name} {d.confidence:.2f}"
            cv2.putText(out, label, (x1, max(y1 - 6, 12)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
        return out
