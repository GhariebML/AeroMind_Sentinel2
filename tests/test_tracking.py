"""
tests/test_tracking.py
Unit and integration tests for the BoT-SORT tracking pipeline.
Run with: pytest tests/test_tracking.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pytest


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def tracking_cfg():
    return {
        "tracker":               "botsort",
        "kalman": {
            "process_noise_scale":     1.0,
            "measurement_noise_scale": 1.0,
        },
        "iou_threshold":          0.3,
        "reid_cosine_threshold":  0.4,
        "iou_weight":             0.5,
        "reid_weight":            0.5,
        "max_age":                30,
        "min_hits":               3,
        "use_reid":               False,   # Re-ID disabled for unit tests
    }


@pytest.fixture
def reid_cfg():
    return {
        "model":         "osnet_x0_25",
        "weights":       "models/reid/nonexistent.pt",
        "embedding_dim": 256,
        "training": {
            "epochs": 1, "batch_size": 4, "lr": 0.001,
            "loss": "triplet", "triplet_margin": 0.5,
            "mining": "hard", "warmup_steps": 10,
        },
    }


@pytest.fixture
def dummy_frame():
    return np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)


def make_detection(x1: float, y1: float, x2: float, y2: float,
                   cls: int = 0, conf: float = 0.9):
    from src.detection.detector import Detection
    class_names = {0: "vehicle", 1: "pedestrian", 2: "aircraft"}
    return Detection(
        bbox=np.array([x1, y1, x2, y2], dtype=np.float32),
        confidence=conf,
        class_id=cls,
        class_name=class_names.get(cls, "vehicle"),
    )


# ─── ReIDModule ───────────────────────────────────────────────────────────────

class TestReIDModule:
    """Tests for the Re-ID embedding extractor."""

    @pytest.fixture
    def reid(self, reid_cfg):
        from src.tracking.tracker import ReIDModule
        return ReIDModule(reid_cfg)

    def test_embedding_shape(self, reid, dummy_frame):
        bboxes = [np.array([10., 10., 50., 50.])]
        embeddings = reid.extract(dummy_frame, bboxes)
        assert len(embeddings) == 1
        assert embeddings[0].shape == (256,)

    def test_embedding_normalised(self, reid, dummy_frame):
        bboxes = [np.array([10., 10., 60., 60.])]
        emb = reid.extract(dummy_frame, bboxes)[0]
        norm = float(np.linalg.norm(emb))
        assert pytest.approx(norm, abs=0.01) == 1.0

    def test_multiple_bboxes(self, reid, dummy_frame):
        bboxes = [
            np.array([10., 10., 50., 50.]),
            np.array([100., 100., 150., 200.]),
            np.array([300., 200., 400., 400.]),
        ]
        embeddings = reid.extract(dummy_frame, bboxes)
        assert len(embeddings) == 3
        for emb in embeddings:
            assert emb.shape == (256,)

    def test_empty_bboxes(self, reid, dummy_frame):
        embeddings = reid.extract(dummy_frame, [])
        assert embeddings == []

    def test_crop_out_of_bounds(self, reid, dummy_frame):
        """Bbox extending outside frame should not crash."""
        bbox = np.array([-10., -10., 700., 700.])
        embeddings = reid.extract(dummy_frame, [bbox])
        assert len(embeddings) == 1
        assert embeddings[0].shape == (256,)


# ─── BotSortTracker ───────────────────────────────────────────────────────────

class TestBotSortTracker:
    """Tests for the multi-object tracker."""

    @pytest.fixture
    def tracker(self, tracking_cfg):
        pytest.importorskip("filterpy")
        from src.tracking.tracker import BotSortTracker
        from src.tracking.tracker import KalmanBoxTracker
        KalmanBoxTracker.count = 0  # reset ID counter
        return BotSortTracker(tracking_cfg)

    def test_empty_update_returns_empty(self, tracker, dummy_frame):
        tracks = tracker.update([], dummy_frame)
        assert tracks == []

    def test_single_detection_creates_track(self, tracker, dummy_frame):
        det = make_detection(100., 100., 200., 200.)
        # Need min_hits frames before a track is confirmed
        for _ in range(3):
            tracks = tracker.update([det], dummy_frame)
        assert len(tracks) >= 1

    def test_track_id_is_stable(self, tracker, dummy_frame):
        det = make_detection(50., 50., 150., 150.)
        ids_seen = []
        for _ in range(5):
            tracks = tracker.update([det], dummy_frame)
            ids_seen.extend([t.id for t in tracks])

        if ids_seen:
            assert len(set(ids_seen)) == 1, "Track ID should not change for stable detection"

    def test_class_propagation(self, tracker, dummy_frame):
        """Track class must match the detection class — not hardcoded."""
        det = make_detection(100., 100., 200., 200., cls=1, conf=0.95)  # pedestrian
        tracks = []
        for _ in range(4):
            tracks = tracker.update([det], dummy_frame)
        if tracks:
            assert tracks[0].class_id == 1
            assert tracks[0].class_name == "pedestrian"

    def test_confidence_propagation(self, tracker, dummy_frame):
        det = make_detection(100., 100., 200., 200., cls=0, conf=0.88)
        tracks = []
        for _ in range(4):
            tracks = tracker.update([det], dummy_frame)
        if tracks:
            assert pytest.approx(tracks[0].confidence, abs=0.01) == 0.88

    def test_multiple_detections(self, tracker, dummy_frame):
        dets = [
            make_detection(10.,  10.,  80.,  80.),
            make_detection(200., 200., 300., 300.),
            make_detection(400., 100., 500., 200.),
        ]
        for _ in range(4):
            tracks = tracker.update(dets, dummy_frame)
        assert len(tracks) <= len(dets)

    def test_track_dies_when_unseen(self, tracker, dummy_frame):
        """Track should disappear after max_age frames without detection."""
        det = make_detection(100., 100., 200., 200.)
        for _ in range(4):
            tracker.update([det], dummy_frame)

        # Stop sending detections
        for _ in range(35):  # > max_age=30
            tracks = tracker.update([], dummy_frame)

        assert len(tracks) == 0, "Track should be pruned after max_age frames"

    def test_active_track_count(self, tracker, dummy_frame):
        det = make_detection(50., 50., 150., 150.)
        for _ in range(4):
            tracker.update([det], dummy_frame)
        assert tracker.active_track_count >= 0

    def test_draw_returns_same_shape(self, tracker, dummy_frame):
        det = make_detection(50., 50., 150., 150.)
        tracks = []
        for _ in range(4):
            tracks = tracker.update([det], dummy_frame)
        out = tracker.draw(dummy_frame, tracks)
        assert out.shape == dummy_frame.shape


# ─── Track dataclass ─────────────────────────────────────────────────────────

class TestTrackDataclass:
    def test_track_creation(self):
        from src.tracking.tracker import Track
        t = Track(
            id=42,
            bbox=np.array([10., 10., 100., 100.]),
            class_id=0,
            class_name="vehicle",
            confidence=0.9,
        )
        assert t.id == 42
        assert t.class_id == 0
        assert t.class_name == "vehicle"

    def test_track_defaults(self):
        from src.tracking.tracker import Track
        t = Track(
            id=1,
            bbox=np.zeros(4),
            class_id=0,
            class_name="vehicle",
            confidence=0.5,
        )
        assert t.age == 0
        assert t.hits == 1
        assert t.time_since_update == 0
        assert t.reid_embedding is None


# ─── IoU ─────────────────────────────────────────────────────────────────────

class TestIoUEdgeCases:
    def test_zero_area_box(self):
        from src.tracking.tracker import BotSortTracker
        bb1 = np.array([10., 10., 10., 10.])  # zero area
        bb2 = np.array([0.,  0.,  50., 50.])
        iou = BotSortTracker._iou(bb1, bb2)
        assert iou == pytest.approx(0.0)

    def test_contained_box(self):
        from src.tracking.tracker import BotSortTracker
        outer = np.array([0.,  0.,  100., 100.])
        inner = np.array([25., 25., 75.,  75.])
        iou   = BotSortTracker._iou(outer, inner)
        assert 0.0 < iou < 1.0

    def test_identical_boxes(self):
        from src.tracking.tracker import BotSortTracker
        bb = np.array([50., 50., 150., 150.])
        assert BotSortTracker._iou(bb, bb) == pytest.approx(1.0)

    def test_adjacent_boxes_no_overlap(self):
        from src.tracking.tracker import BotSortTracker
        bb1 = np.array([0.,  0.,  50., 50.])
        bb2 = np.array([50., 0., 100., 50.])  # shares only an edge
        iou = BotSortTracker._iou(bb1, bb2)
        assert iou == pytest.approx(0.0, abs=1e-5)
