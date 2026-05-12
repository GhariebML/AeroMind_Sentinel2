"""
src/utils/metrics.py
Full tracking + energy evaluation metrics from the AeroMind AI report.
MOTA, IDF1, MOTP, energy efficiency η, and all ablation metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
from loguru import logger


@dataclass
class FrameResult:
    """Ground truth and tracker output for a single frame."""
    gt_bboxes: np.ndarray           # (N, 4) ground truth
    gt_ids: np.ndarray              # (N,)   ground truth IDs
    trk_bboxes: np.ndarray          # (M, 4) tracker output
    trk_ids: np.ndarray             # (M,)   tracker IDs
    frame_idx: int = 0


@dataclass
class EnergyResult:
    path_length: float = 0.0
    mean_speed: float = 0.0
    altitude_change: float = 0.0
    flight_time: float = 0.0
    total_joules: float = 0.0
    total_tracked_frames: float = 0.0  # Σ(targets × frames)

    @property
    def efficiency_eta(self) -> float:
        """η = (total target·frames) / E_total  [(target·frames)/J]"""
        return self.total_tracked_frames / max(self.total_joules, 1e-6)


@dataclass
class TrackingMetrics:
    mota: float = 0.0
    idf1: float = 0.0
    motp: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    id_switches: int = 0
    fragmentations: int = 0
    mostly_tracked: int = 0
    partially_tracked: int = 0
    mostly_lost: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    num_unique_objects: int = 0
    num_frames: int = 0

    def __str__(self) -> str:
        return (
            f"\n{'─'*50}\n"
            f"  MOTA          : {self.mota*100:6.2f}%  (target > 80%)\n"
            f"  IDF1          : {self.idf1*100:6.2f}%  (target > 75%)\n"
            f"  MOTP          : {self.motp*100:6.2f}%\n"
            f"  Precision     : {self.precision*100:6.2f}%\n"
            f"  Recall        : {self.recall*100:6.2f}%\n"
            f"  ID Switches   : {self.id_switches:6d}   (target < 20/1k frames)\n"
            f"  Fragmentations: {self.fragmentations:6d}\n"
            f"  FP / FN       : {self.false_positives} / {self.false_negatives}\n"
            f"  Frames        : {self.num_frames:6d}\n"
            f"{'─'*50}"
        )

    def passes_targets(self, targets: dict) -> bool:
        sw_per_1k = self.id_switches / max(self.num_frames, 1) * 1000
        return (
            self.mota >= targets["mota"]
            and self.idf1 >= targets["idf1"]
            and sw_per_1k <= targets["id_switches_per_1k"]
        )


# ─────────────────────────────────────────────────────────────────────────────
# MOTA / IDF1 / MOTP
# ─────────────────────────────────────────────────────────────────────────────

class MOTMetricsEvaluator:
    """
    Computes MOTA, IDF1, MOTP using the motmetrics library.
    Falls back to a manual implementation if library unavailable.
    """

    def __init__(self):
        self._use_lib = self._check_lib()

    @staticmethod
    def _check_lib() -> bool:
        try:
            import motmetrics  # noqa
            return True
        except ImportError:
            logger.warning("motmetrics not installed — using manual metrics.")
            return False

    def evaluate(self, frame_results: List[FrameResult]) -> TrackingMetrics:
        if self._use_lib:
            return self._eval_with_motmetrics(frame_results)
        return self._eval_manual(frame_results)

    def _eval_with_motmetrics(self, frames: List[FrameResult]) -> TrackingMetrics:
        import motmetrics as mm

        acc = mm.MOTAccumulator(auto_id=True)
        for fr in frames:
            gt_ids = list(fr.gt_ids.astype(int))
            trk_ids = list(fr.trk_ids.astype(int))
            if len(gt_ids) == 0 and len(trk_ids) == 0:
                acc.update([], [], [])
                continue
            if len(gt_ids) == 0:
                acc.update([], trk_ids, [])
                continue
            if len(trk_ids) == 0:
                acc.update(gt_ids, [], [])
                continue

            dist = mm.distances.iou_matrix(fr.gt_bboxes, fr.trk_bboxes, max_iou=0.5)
            acc.update(gt_ids, trk_ids, dist)

        mh = mm.metrics.create()
        summary = mh.compute(acc, metrics=[
            "mota", "idf1", "motp", "num_switches",
            "num_fragmentations", "precision", "recall",
            "num_false_positives", "num_misses",
            "num_unique_objects", "mostly_tracked",
            "partially_tracked", "mostly_lost",
        ], name="eval")

        row = summary.iloc[0]
        return TrackingMetrics(
            mota=float(row.get("mota", 0)),
            idf1=float(row.get("idf1", 0)),
            motp=float(row.get("motp", 0)),
            precision=float(row.get("precision", 0)),
            recall=float(row.get("recall", 0)),
            id_switches=int(row.get("num_switches", 0)),
            fragmentations=int(row.get("num_fragmentations", 0)),
            false_positives=int(row.get("num_false_positives", 0)),
            false_negatives=int(row.get("num_misses", 0)),
            num_unique_objects=int(row.get("num_unique_objects", 0)),
            mostly_tracked=int(row.get("mostly_tracked", 0)),
            partially_tracked=int(row.get("partially_tracked", 0)),
            mostly_lost=int(row.get("mostly_lost", 0)),
            num_frames=len(frames),
        )

    def _eval_manual(self, frames: List[FrameResult]) -> TrackingMetrics:
        """Simplified manual implementation of MOTA and IDF1."""
        tp = fp = fn = id_sw = 0
        iou_sum = matched_count = 0
        prev_match: Dict[int, int] = {}   # gt_id → trk_id

        for fr in frames:
            n_gt = len(fr.gt_ids)
            n_trk = len(fr.trk_ids)
            if n_gt == 0 and n_trk == 0:
                continue

            cur_match: Dict[int, int] = {}
            matched_trk = set()

            if n_gt > 0 and n_trk > 0:
                iou_matrix = self._iou_matrix(fr.gt_bboxes, fr.trk_bboxes)
                for gi in range(n_gt):
                    best_j = int(iou_matrix[gi].argmax())
                    if iou_matrix[gi, best_j] >= 0.5 and best_j not in matched_trk:
                        cur_match[int(fr.gt_ids[gi])] = int(fr.trk_ids[best_j])
                        matched_trk.add(best_j)
                        iou_sum += iou_matrix[gi, best_j]
                        matched_count += 1

            matched_gt = set(cur_match.keys())
            tp += len(matched_gt)
            fn += n_gt - len(matched_gt)
            fp += n_trk - len(matched_trk)

            for gid, tid in cur_match.items():
                if gid in prev_match and prev_match[gid] != tid:
                    id_sw += 1

            prev_match = cur_match

        total_gt = sum(len(fr.gt_ids) for fr in frames)
        mota = 1.0 - (fn + fp + id_sw) / max(total_gt, 1)
        motp = iou_sum / max(matched_count, 1)
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        idf1 = 2 * tp / max(2 * tp + fp + fn, 1)

        return TrackingMetrics(
            mota=max(mota, 0.0), idf1=idf1, motp=motp,
            precision=precision, recall=recall,
            id_switches=id_sw, false_positives=fp,
            false_negatives=fn, num_frames=len(frames),
        )

    @staticmethod
    def _iou_matrix(gt: np.ndarray, trk: np.ndarray) -> np.ndarray:
        mat = np.zeros((len(gt), len(trk)))
        for i, g in enumerate(gt):
            for j, t in enumerate(trk):
                xi1, yi1 = max(g[0], t[0]), max(g[1], t[1])
                xi2, yi2 = min(g[2], t[2]), min(g[3], t[3])
                inter = max(0, xi2-xi1) * max(0, yi2-yi1)
                ag = (g[2]-g[0]) * (g[3]-g[1])
                at = (t[2]-t[0]) * (t[3]-t[1])
                mat[i, j] = inter / max(ag + at - inter, 1e-6)
        return mat


# ─────────────────────────────────────────────────────────────────────────────
# Inference Latency
# ─────────────────────────────────────────────────────────────────────────────

class LatencyBenchmark:
    """Measure end-to-end inference latency for the full pipeline."""

    def __init__(self, detector, tracker):
        self.detector = detector
        self.tracker = tracker

    def benchmark(self, frames: List[np.ndarray]) -> dict:
        import time
        latencies = []
        for frame in frames:
            t0 = time.perf_counter()
            dets = self.detector.detect(frame)
            self.tracker.update(dets, frame)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000)  # ms

        return {
            "mean_latency_ms": float(np.mean(latencies)),
            "p50_ms": float(np.percentile(latencies, 50)),
            "p95_ms": float(np.percentile(latencies, 95)),
            "p99_ms": float(np.percentile(latencies, 99)),
            "fps": float(1000 / np.mean(latencies)),
            "passes_target": float(np.mean(latencies)) < 60.0,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Comparison Table Printer (matches Table 1 in the report)
# ─────────────────────────────────────────────────────────────────────────────

def print_comparison_table(fixed_metrics: TrackingMetrics,
                           rl_metrics: TrackingMetrics,
                           fixed_energy: EnergyResult,
                           rl_energy: EnergyResult) -> None:
    """Reproduces Table 1 from the technical report."""
    fixed_sw = fixed_metrics.id_switches / max(fixed_metrics.num_frames, 1) * 1000
    rl_sw = rl_metrics.id_switches / max(rl_metrics.num_frames, 1) * 1000
    energy_save = (fixed_energy.total_joules - rl_energy.total_joules) / max(fixed_energy.total_joules, 1) * 100

    print("\n" + "═"*70)
    print(f"  {'Metric':<30} {'Fixed Path':>12} {'RL-Optimized':>12} {'Δ':>10}")
    print("─"*70)
    rows = [
        ("MOTA (%)",       fixed_metrics.mota*100,       rl_metrics.mota*100,       "+pp"),
        ("IDF1 (%)",       fixed_metrics.idf1*100,       rl_metrics.idf1*100,       "+pp"),
        ("ID Switches/1k", fixed_sw,                      rl_sw,                      "−%"),
        ("Energy (J)",     fixed_energy.total_joules,     rl_energy.total_joules,     "−%"),
        ("Efficiency η",   fixed_energy.efficiency_eta,   rl_energy.efficiency_eta,   "+%"),
    ]
    for name, fv, rv, unit in rows:
        delta = rv - fv if unit == "+pp" else (rv - fv) / max(abs(fv), 1e-6) * 100
        sign = "+" if delta >= 0 else ""
        print(f"  {name:<30} {fv:>12.1f} {rv:>12.1f} {sign}{delta:>8.1f}{unit}")
    print("═"*70 + "\n")
