"""
scripts/collect_reid_crops.py
Phase 2 Prep — Extract Re-ID identity crops from tracked AirSim sequences.

Reads frames from data/raw/, runs detection + tracking, and saves per-identity
cropped images to data/reid/{train,val}/{identity_id}/{frame}.jpg.

Usage:
    python scripts/collect_reid_crops.py --config configs/config.yaml
    python scripts/collect_reid_crops.py --mock --crops 400
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import cv2
import numpy as np
import yaml
from loguru import logger


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Extract Re-ID crops — AeroMind AI Phase 2 Prep")
    p.add_argument("--config",    default="configs/config.yaml")
    p.add_argument("--source",    default="data/raw",
                   help="Source directory of collected frames")
    p.add_argument("--out",       default="data/reid",
                   help="Output directory for identity crops")
    p.add_argument("--min-crops", type=int, default=8,
                   help="Minimum crops per identity to keep")
    p.add_argument("--max-crops", type=int, default=64,
                   help="Maximum crops per identity to save")
    p.add_argument("--val-split", type=float, default=0.2)
    p.add_argument("--mock",      action="store_true",
                   help="Generate synthetic crops without real frames")
    p.add_argument("--crops",     type=int, default=0,
                   help="Total synthetic crops to generate (mock mode)")
    return p.parse_args()


# ─── Synthetic crop generator ────────────────────────────────────────────────

def generate_mock_crops(n_identities: int = 60,
                        n_per_id: int = 16) -> dict:
    """Returns {identity_id: [crop_array, ...]} with distinct colour signatures."""
    rng = np.random.default_rng(0)
    crops = defaultdict(list)
    for pid in range(n_identities):
        base = rng.integers(30, 220, 3).astype(np.uint8)
        for k in range(n_per_id):
            crop = np.tile(base, (256, 128, 1)).astype(np.uint8)
            noise = rng.integers(-25, 25, crop.shape, dtype=np.int16)
            crop  = np.clip(crop.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            crops[pid].append(crop)
    return dict(crops)


# ─── Real crop extraction ─────────────────────────────────────────────────────

def extract_crops_from_sequence(frames_dir: Path, cfg: dict) -> dict:
    """
    Run detector + tracker on saved frame sequences.
    Returns {track_id: [crop_array, ...]} dict.
    """
    from src.detection.detector import AerialDetector
    from src.tracking.tracker   import BotSortTracker, ReIDModule

    detector = AerialDetector(cfg["detection"])
    reid     = ReIDModule(cfg["reid"])
    tracker  = BotSortTracker(cfg["tracking"], reid_module=reid)

    crops_by_id: dict = defaultdict(list)
    img_paths = sorted(frames_dir.glob("**/*.jpg"))

    logger.info(f"Processing {len(img_paths)} frames from {frames_dir} ...")
    for idx, img_path in enumerate(img_paths):
        frame_bgr = cv2.imread(str(img_path))
        if frame_bgr is None:
            continue
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        detections = detector.detect(frame_rgb)
        tracks     = tracker.update(detections, frame_rgb)

        for t in tracks:
            x1, y1, x2, y2 = t.bbox.astype(int)
            x1, y1 = max(x1, 0), max(y1, 0)
            x2, y2 = min(x2, frame_rgb.shape[1]), min(y2, frame_rgb.shape[0])
            if x2 - x1 < 10 or y2 - y1 < 10:
                continue
            crop = frame_rgb[y1:y2, x1:x2]
            crop = cv2.resize(crop, (128, 256))
            crops_by_id[t.id].append(crop)

        if idx % 100 == 0:
            logger.info(f"  {idx}/{len(img_paths)} frames | "
                        f"{len(crops_by_id)} identities tracked")

    return dict(crops_by_id)


# ─── Save crops ───────────────────────────────────────────────────────────────

def save_crops(crops_by_id: dict, out_dir: Path,
               min_crops: int, max_crops: int, val_split: float) -> None:
    """Persist crops to disk in Market-1501-style structure."""
    train_dir = out_dir / "train"
    val_dir   = out_dir / "val"
    train_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)

    n_identities = 0
    n_train = n_val = 0

    for pid, crop_list in crops_by_id.items():
        if len(crop_list) < min_crops:
            continue

        # Cap at max_crops
        if len(crop_list) > max_crops:
            crop_list = crop_list[:max_crops]

        n_val_crops = max(1, int(len(crop_list) * val_split))
        val_crops   = crop_list[:n_val_crops]
        train_crops = crop_list[n_val_crops:]

        pid_str = f"{pid:06d}"
        for split_dir, split_crops in [(train_dir, train_crops), (val_dir, val_crops)]:
            (split_dir / pid_str).mkdir(exist_ok=True)
            for k, crop in enumerate(split_crops):
                dst = split_dir / pid_str / f"{k:04d}.jpg"
                cv2.imwrite(str(dst), cv2.cvtColor(crop, cv2.COLOR_RGB2BGR))

        n_train += len(train_crops)
        n_val   += len(val_crops)
        n_identities += 1

    logger.success(
        f"Saved {n_train} train + {n_val} val crops "
        f"across {n_identities} identities → {out_dir}"
    )


# ─── Entry ───────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    with open(ROOT / args.config) as f:
        cfg = yaml.safe_load(f)

    out_dir  = ROOT / args.out
    src_dir  = ROOT / args.source

    logger.info("=" * 60)
    logger.info("  AeroMind AI Re-ID Crop Extraction")
    logger.info(f"  Source     : {src_dir}")
    logger.info(f"  Output     : {out_dir}")
    logger.info(f"  Min crops  : {args.min_crops}")
    logger.info(f"  Mock mode  : {args.mock}")
    logger.info("=" * 60)

    if args.mock:
        n_ids = max(1, (args.crops or 480) // 16)
        crops = generate_mock_crops(n_identities=n_ids, n_per_id=16)
        logger.info(f"Mock: generated {sum(len(v) for v in crops.values())} "
                    f"crops across {len(crops)} identities")
    else:
        if not src_dir.exists() or not any(src_dir.rglob("*.jpg")):
            logger.error(f"No frames found in {src_dir}. "
                         "Run collect_data.py first, or use --mock.")
            sys.exit(1)
        crops = extract_crops_from_sequence(src_dir, cfg)

    save_crops(crops, out_dir, args.min_crops, args.max_crops, args.val_split)


if __name__ == "__main__":
    main()
