"""
tests/test_detection.py
Unit tests for detector, tracker, and metrics pipeline.
Run with: pytest tests/ -v
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Detection tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAerialDetector:
    """Tests for the YOLOv8 detector wrapper."""

    @pytest.fixture
    def dummy_cfg(self):
        return {
            "model": "yolov8n",
            "weights": "models/detection/nonexistent.pt",
            "input_size": 640,
            "confidence_threshold": 0.5,
            "nms_iou_threshold": 0.45,
            "classes": {0: "vehicle", 1: "pedestrian", 2: "aircraft"},
            "sahi": {
                "enabled": False,
                "slice_height": 320,
                "slice_width": 320,
                "overlap_height_ratio": 0.2,
                "overlap_width_ratio": 0.2,
            },
            "training": {
                "epochs": 100,
                "batch_size": 16,
                "lr0": 0.001,
                "lrf": 0.00001,
                "warmup_epochs": 3,
                "augmentation": {"mosaic": True, "mixup": 0.1,
                                  "random_scale": [0.5, 1.5],
                                  "motion_blur": True,
                                  "brightness_jitter": 0.3,
                                  "contrast_jitter": 0.3,
                                  "perspective": 0.2},
                "dataset_split": [0.7, 0.15, 0.15],
                "target_frames": 15000,
            },
        }

    @pytest.fixture
    def detector(self, dummy_cfg):
        from src.detection.detector import AerialDetector
        return AerialDetector(dummy_cfg)

    @pytest.fixture
    def dummy_frame(self):
        return np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

    def test_detect_returns_list(self, detector, dummy_frame):
        dets = detector._mock_detections(dummy_frame)
        assert isinstance(dets, list)

    def test_detection_bbox_shape(self, detector, dummy_frame):
        dets = detector._mock_detections(dummy_frame)
        for d in dets:
            assert d.bbox.shape == (4,)
            assert d.bbox[2] > d.bbox[0]  # x2 > x1
            assert d.bbox[3] > d.bbox[1]  # y2 > y1

    def test_detection_confidence_range(self, detector, dummy_frame):
        dets = detector._mock_detections(dummy_frame)
        for d in dets:
            assert 0.0 <= d.confidence <= 1.0

    def test_class_ids_valid(self, detector, dummy_frame):
        dets = detector._mock_detections(dummy_frame)
        for d in dets:
            assert d.class_id in [0, 1, 2]
            assert d.class_name in ["vehicle", "pedestrian", "aircraft"]

    def test_draw_returns_same_shape(self, detector, dummy_frame):
        dets = detector._mock_detections(dummy_frame)
        out = detector.draw(dummy_frame, dets)
        assert out.shape == dummy_frame.shape


# ─────────────────────────────────────────────────────────────────────────────
# Kalman Filter tests
# ─────────────────────────────────────────────────────────────────────────────

class TestKalmanBoxTracker:
    """Tests for the Kalman filter tracker."""

    @pytest.fixture
    def tracker(self):
        pytest.importorskip("filterpy")
        from src.tracking.tracker import KalmanBoxTracker
        KalmanBoxTracker.count = 0
        return KalmanBoxTracker(np.array([100., 100., 200., 200.]))

    def test_initial_state(self, tracker):
        state = tracker.get_state()
        assert state.shape == (4,)

    def test_predict_updates_age(self, tracker):
        initial_age = tracker.age
        tracker.predict()
        assert tracker.age == initial_age + 1

    def test_update_resets_time_since_update(self, tracker):
        tracker.predict()
        assert tracker.time_since_update == 1
        tracker.update(np.array([105., 105., 205., 205.]))
        assert tracker.time_since_update == 0

    def test_id_increments(self):
        pytest.importorskip("filterpy")
        from src.tracking.tracker import KalmanBoxTracker
        KalmanBoxTracker.count = 0
        t1 = KalmanBoxTracker(np.array([0., 0., 50., 50.]))
        t2 = KalmanBoxTracker(np.array([60., 60., 110., 110.]))
        assert t2.id == t1.id + 1


# ─────────────────────────────────────────────────────────────────────────────
# IoU tests
# ─────────────────────────────────────────────────────────────────────────────

class TestIoU:
    def test_perfect_overlap(self):
        from src.tracking.tracker import BotSortTracker
        bb = np.array([0., 0., 100., 100.])
        assert BotSortTracker._iou(bb, bb) == pytest.approx(1.0)

    def test_no_overlap(self):
        from src.tracking.tracker import BotSortTracker
        bb1 = np.array([0., 0., 50., 50.])
        bb2 = np.array([100., 100., 150., 150.])
        assert BotSortTracker._iou(bb1, bb2) == pytest.approx(0.0)

    def test_partial_overlap(self):
        from src.tracking.tracker import BotSortTracker
        bb1 = np.array([0., 0., 100., 100.])
        bb2 = np.array([50., 50., 150., 150.])
        iou = BotSortTracker._iou(bb1, bb2)
        assert 0.0 < iou < 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Energy model tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEnergyAccumulator:
    def test_zero_on_reset(self):
        from src.simulation.airsim_env import EnergyAccumulator
        ea = EnergyAccumulator()
        ea.reset()
        assert ea.consumed == 0.0

    def test_energy_increases(self):
        from src.simulation.airsim_env import EnergyAccumulator
        import time
        ea = EnergyAccumulator()
        ea.reset()
        p0 = np.array([0., 0., -30.])
        ea.update(p0, np.zeros(3), 0.0)
        p1 = np.array([5., 5., -30.])
        delta = ea.update(p1, np.array([2., 2., 0.]), 0.5)
        assert delta > 0.0
        assert ea.consumed > 0.0

    def test_remaining_fraction_decreases(self):
        from src.simulation.airsim_env import EnergyAccumulator
        ea = EnergyAccumulator(battery_capacity_joules=100.0)
        ea.reset()
        ea.update(np.zeros(3), np.zeros(3), 0.0)
        ea.update(np.array([10., 0., 0.]), np.array([5., 0., 0.]), 1.0)
        assert ea.remaining_fraction < 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Metrics tests
# ─────────────────────────────────────────────────────────────────────────────

class TestMetrics:
    def test_mota_perfect(self):
        from src.utils.metrics import MOTMetricsEvaluator, FrameResult
        evaluator = MOTMetricsEvaluator()
        frames = []
        for i in range(10):
            bbox = np.array([[10., 10., 50., 50.], [60., 60., 100., 100.]])
            frames.append(FrameResult(
                gt_bboxes=bbox, gt_ids=np.array([1, 2]),
                trk_bboxes=bbox, trk_ids=np.array([1, 2]),
                frame_idx=i,
            ))
        try:
            metrics = evaluator.evaluate(frames)
            assert metrics.mota > 0.5  # high accuracy on perfect match
            assert metrics.idf1 > 0.5
        except AttributeError as e:
            # motmetrics uses np.asfarray which was removed in NumPy 2.0
            pytest.skip(f"motmetrics incompatible with NumPy 2.0: {e}")

    def test_mota_no_detections(self):
        from src.utils.metrics import MOTMetricsEvaluator, FrameResult
        evaluator = MOTMetricsEvaluator()
        frames = [FrameResult(
            gt_bboxes=np.array([[10., 10., 50., 50.]]),
            gt_ids=np.array([1]),
            trk_bboxes=np.zeros((0, 4)),
            trk_ids=np.array([]),
            frame_idx=i,
        ) for i in range(5)]
        metrics = evaluator.evaluate(frames)
        assert metrics.mota <= 0.0

    def test_efficiency_eta(self):
        from src.utils.metrics import EnergyResult
        er = EnergyResult(total_joules=274.0, total_tracked_frames=6850.0)
        eta = er.efficiency_eta
        assert eta == pytest.approx(6850.0 / 274.0, rel=1e-3)
        assert eta > 24.0  # should be ~25 (target·frames)/J
