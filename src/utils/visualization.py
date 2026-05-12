"""
src/utils/visualization.py
Centralised visualisation helpers for the AeroMind AI aerial tracking pipeline.

Provides:
  - draw_detections(frame, detections) -> np.ndarray
  - draw_tracks(frame, tracks)         -> np.ndarray
  - draw_hud(frame, info)              -> np.ndarray
  - make_comparison_grid(frames, labels) -> np.ndarray
  - save_result_plot(metrics_history, out_path)
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np


# ─── Colour palettes ─────────────────────────────────────────────────────────

# Class colours (BGR): vehicle=green, pedestrian=orange, aircraft=blue
CLASS_COLORS: Dict[int, tuple] = {
    0: (0, 220, 80),    # vehicle   — green
    1: (0, 140, 255),   # pedestrian — orange
    2: (220, 60, 0),    # aircraft  — blue
}

# Track-ID colour palette (deterministic, 32 distinct colours)
_TRACK_PALETTE = np.array([
    [0, 255, 128], [255, 80, 0],   [0, 150, 255], [255, 230, 0],
    [200, 0, 255], [0, 200, 200],  [255, 110, 110],[110, 255, 200],
    [255, 0, 128], [0, 255, 255],  [255, 200, 50], [50, 100, 255],
    [180, 255, 0], [255, 50, 200], [0, 180, 180],  [200, 200, 0],
    [100, 200, 255],[255, 150, 0], [0, 255, 80],   [200, 80, 255],
    [80, 255, 150], [255, 80, 150],[150, 80, 255], [80, 200, 100],
    [200, 100, 80],[100, 80, 200], [80, 100, 200], [255, 200, 100],
    [100, 255, 80],[200, 255, 80], [80, 255, 200], [255, 100, 80],
], dtype=np.uint8)


def track_color(track_id: int) -> tuple:
    c = _TRACK_PALETTE[track_id % len(_TRACK_PALETTE)]
    return int(c[0]), int(c[1]), int(c[2])


# ─── Detection overlay ────────────────────────────────────────────────────────

def draw_detections(frame: np.ndarray, detections) -> np.ndarray:
    """
    Draw raw detector output (before tracking) on the frame.

    Args:
        frame:      HxWx3 uint8 (RGB)
        detections: list of Detection objects with .bbox, .class_id, .class_name, .confidence
    Returns:
        Annotated frame copy (RGB)
    """
    out = frame.copy()
    for d in detections:
        x1, y1, x2, y2 = d.bbox.astype(int)
        color = CLASS_COLORS.get(d.class_id, (200, 200, 200))
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        label = f"{d.class_name} {d.confidence:.2f}"
        _put_label(out, label, x1, y1, color)
    return out


# ─── Track overlay ────────────────────────────────────────────────────────────

def draw_tracks(frame: np.ndarray, tracks) -> np.ndarray:
    """
    Draw confirmed tracker output on the frame.

    Args:
        frame:  HxWx3 uint8 (RGB)
        tracks: list of Track objects with .id, .bbox, .class_name, .confidence
    Returns:
        Annotated frame copy (RGB)
    """
    out = frame.copy()
    for t in tracks:
        x1, y1, x2, y2 = t.bbox.astype(int)
        color = track_color(t.id)
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        label = f"ID:{t.id} {t.class_name}"
        _put_label(out, label, x1, y1, color)

    # Active track count
    cv2.putText(out, f"Active tracks: {len(tracks)}", (8, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
    return out


# ─── HUD panel ────────────────────────────────────────────────────────────────

def draw_hud(frame: np.ndarray,
             info: dict,
             scenario: str = "",
             panel_pos: tuple = (10, 10)) -> np.ndarray:
    """
    Render a metrics HUD panel over the frame.

    Expected info keys:
        n_tracks, mota, idf1, energy_J, battery, fps, id_switches
    """
    out = frame.copy()
    px, py = panel_pos
    pw, ph = 295, 165

    panel = np.zeros((ph, pw, 3), dtype=np.uint8)
    panel[:] = (15, 15, 15)
    cv2.rectangle(panel, (0, 0), (pw - 1, ph - 1), (0, 180, 90), 1)

    # Title
    cv2.putText(panel, "AeroMind AI", (6, 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 220, 100), 1)
    if scenario:
        cv2.putText(panel, f"[{scenario}]", (pw - 110, 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (150, 150, 150), 1)

    rows = [
        ("Tracks",     f"{info.get('n_tracks',0):3d}"),
        ("MOTA",       f"{info.get('mota', 0)*100:5.1f}%"),
        ("IDF1",       f"{info.get('idf1', 0)*100:5.1f}%"),
        ("ID Switches",f"{info.get('id_switches', 0):4d}"),
        ("Energy",     f"{info.get('energy_J', 0):7.1f} J"),
        ("Battery",    f"{info.get('battery', 1)*100:5.1f}%"),
        ("FPS",        f"{info.get('fps', 0):5.1f}"),
    ]
    for i, (key, val) in enumerate(rows):
        y = 35 + i * 17
        cv2.putText(panel, key + " :", (6, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (160, 160, 160), 1)
        cv2.putText(panel, val, (pw - 90, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (230, 230, 230), 1)

    # Battery bar
    batt = float(np.clip(info.get("battery", 1.0), 0, 1))
    bar_color = (0, 200, 50) if batt > 0.3 else (30, 30, 220)
    bar_w = int((pw - 12) * batt)
    cv2.rectangle(panel, (6, ph - 20), (6 + bar_w, ph - 8), bar_color, -1)
    cv2.rectangle(panel, (6, ph - 20), (pw - 7, ph - 8), (70, 70, 70), 1)

    # Paste onto frame
    h, w = out.shape[:2]
    x2 = min(px + pw, w)
    y2 = min(py + ph, h)
    out[py:y2, px:x2] = panel[:y2 - py, :x2 - px]
    return out


# ─── Comparison grid ─────────────────────────────────────────────────────────

def make_comparison_grid(frames: List[np.ndarray],
                         labels: List[str],
                         cols: int = 2) -> np.ndarray:
    """
    Stack a list of annotated frames into a single grid image.
    All frames are resized to match the first frame's size.
    """
    if not frames:
        return np.zeros((100, 100, 3), dtype=np.uint8)

    h, w = frames[0].shape[:2]
    rows = []
    for i in range(0, len(frames), cols):
        row_frames = frames[i:i + cols]
        # Pad row if needed
        while len(row_frames) < cols:
            row_frames.append(np.zeros((h, w, 3), dtype=np.uint8))

        # Add label to each frame
        labelled = []
        for j, (f, lbl) in enumerate(zip(row_frames, labels[i:i + cols])):
            f = cv2.resize(f, (w, h))
            cv2.putText(f, lbl, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            labelled.append(f)

        rows.append(np.hstack(labelled))

    return np.vstack(rows)


# ─── Plot utilities ───────────────────────────────────────────────────────────

def save_result_plot(metrics_history: dict, out_path: str) -> None:
    """
    Save a multi-panel plot of training/evaluation metrics over time.

    Args:
        metrics_history: dict of {metric_name: [values_over_time]}
        out_path:        .png file path to save
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed — skipping plot.")
        return

    keys   = list(metrics_history.keys())
    n_cols = min(3, len(keys))
    n_rows = (len(keys) + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(6 * n_cols, 4 * n_rows))
    axes = np.array(axes).flatten()

    for ax, key in zip(axes, keys):
        vals = metrics_history[key]
        ax.plot(vals, linewidth=1.5, color="#00c878")
        ax.set_title(key, fontsize=11)
        ax.set_xlabel("Step / Epoch")
        ax.grid(alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    for ax in axes[len(keys):]:
        ax.set_visible(False)

    fig.patch.set_facecolor("#111111")
    for ax in axes[:len(keys)]:
        ax.set_facecolor("#1a1a1a")
        ax.tick_params(colors="white")
        ax.title.set_color("white")
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        for spine in ax.spines.values():
            spine.set_edgecolor("#444444")

    plt.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"Plot saved → {out_path}")


# ─── Internal ─────────────────────────────────────────────────────────────────

def _put_label(frame: np.ndarray, text: str, x: int, y: int, color: tuple) -> None:
    """Draw a filled label box with text above a bounding box."""
    (tw, th), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
    y_top = max(y - th - 6, 0)
    cv2.rectangle(frame, (x, y_top), (x + tw + 4, y_top + th + 5), color, -1)
    cv2.putText(frame, text, (x + 2, y_top + th + 1),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
