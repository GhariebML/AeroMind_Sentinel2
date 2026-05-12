"""
scripts/collect_data.py
Phase 0 — Data Collection from AirSim.

Flies the drone through all configured environments, captures top-down RGB
frames, and saves them alongside YOLO-format bounding box annotations.

Usage:
    python scripts/collect_data.py --config configs/config.yaml
    python scripts/collect_data.py --mock --frames 200
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import cv2
import numpy as np
import yaml
from loguru import logger


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="AeroMind AI Data Collection from AirSim")
    p.add_argument("--config",   default="configs/config.yaml")
    p.add_argument("--frames",   type=int, default=0,
                   help="Frames per environment (0 = from config)")
    p.add_argument("--mock",     action="store_true",
                   help="Generate synthetic frames without AirSim")
    p.add_argument("--out",      default="data",
                   help="Root output dir (raw/ and annotations/ subdirs created)")
    return p.parse_args()


# ─── YOLO label writer ────────────────────────────────────────────────────────

def write_yolo_label(label_path: Path, bboxes: list, img_w: int, img_h: int) -> None:
    """Write YOLO-format .txt label file (class cx cy w h, normalised)."""
    lines = []
    for cls_id, x1, y1, x2, y2 in bboxes:
        cx = ((x1 + x2) / 2) / img_w
        cy = ((y1 + y2) / 2) / img_h
        bw = (x2 - x1) / img_w
        bh = (y2 - y1) / img_h
        lines.append(f"{cls_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
    label_path.write_text("\n".join(lines))


# ─── Mock data generator ─────────────────────────────────────────────────────

def generate_mock_frame(frame_idx: int, env_name: str) -> tuple:
    """Return (rgb_frame, list_of_bbox_annotations)."""
    rng = np.random.default_rng(frame_idx)
    h, w = 640, 640

    # Background: tiled top-down road/field
    base_colors = {
        "dense_urban":  (60, 70, 60),
        "highway":      (80, 80, 80),
        "parking_lot":  (90, 90, 90),
        "airport_apron":(100, 100, 90),
        "campus":       (50, 80, 50),
        "mixed_terrain":(70, 80, 60),
    }
    bg = np.full((h, w, 3), base_colors.get(env_name, (70, 70, 70)), dtype=np.uint8)
    noise = rng.integers(-15, 15, bg.shape, dtype=np.int16)
    frame = np.clip(bg.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Objects: small rectangles simulating top-down vehicles / pedestrians
    n_objects = rng.integers(3, 20)
    annotations = []
    class_sizes = {0: (25, 15), 1: (10, 10), 2: (40, 40)}  # vehicle, pedestrian, aircraft
    class_colors = {0: (0, 120, 200), 1: (200, 120, 0), 2: (200, 0, 100)}

    for _ in range(n_objects):
        cls = int(rng.integers(0, 3))
        bw, bh = class_sizes[cls]
        bw += int(rng.integers(-5, 5))
        bh += int(rng.integers(-5, 5))
        x1 = int(rng.integers(0, w - bw))
        y1 = int(rng.integers(0, h - bh))
        x2 = x1 + bw
        y2 = y1 + bh
        cv2.rectangle(frame, (x1, y1), (x2, y2), class_colors[cls], -1)
        annotations.append((cls, x1, y1, x2, y2))

    return frame, annotations


# ─── Main collection loop ─────────────────────────────────────────────────────

def collect(cfg: dict, args: argparse.Namespace) -> None:
    target_frames = args.frames or cfg["detection"]["training"]["target_frames"]
    environments  = cfg["airsim"]["environments"]
    per_env       = max(1, target_frames // len(environments))

    # Directory layout
    base   = ROOT / args.out
    raw_dir = base / "raw"
    ann_dir = base / "annotations"
    for env_name in environments:
        (raw_dir / env_name).mkdir(parents=True, exist_ok=True)
        (ann_dir / env_name).mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("  AeroMind AI Phase 0: Data Collection")
    logger.info(f"  Environments : {environments}")
    logger.info(f"  Frames/env   : {per_env}")
    logger.info(f"  Mock mode    : {args.mock}")
    logger.info("=" * 60)

    if not args.mock:
        from src.simulation.airsim_env import AirSimClient
        client = AirSimClient(
            ip=cfg["airsim"]["ip"],
            port=cfg["airsim"]["port"],
            camera_name=cfg["airsim"]["camera_name"],
        )

    total_saved = 0
    stats: dict = {}

    for env_name in environments:
        logger.info(f"\n── Collecting: {env_name} ──")
        env_raw = raw_dir / env_name
        env_ann = ann_dir / env_name
        n_saved = 0

        for i in range(per_env):
            if args.mock:
                frame, ann_list = generate_mock_frame(total_saved + i, env_name)
            else:
                try:
                    frame = client.get_frame()
                    # When AirSim + an object detection model is present, use it;
                    # otherwise record un-annotated frames for manual labelling.
                    ann_list = []
                except Exception as e:
                    logger.warning(f"Frame capture failed: {e} — skipping.")
                    continue

            # Save frame
            frame_name = f"{env_name}_{i:06d}"
            img_path   = env_raw / f"{frame_name}.jpg"
            cv2.imwrite(str(img_path), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

            # Save YOLO label
            lbl_path = env_ann / f"{frame_name}.txt"
            write_yolo_label(lbl_path, ann_list, frame.shape[1], frame.shape[0])

            n_saved += 1
            total_saved += 1

            if i % 100 == 0:
                logger.info(f"  [{env_name}] {i}/{per_env} frames saved ...")

            # Throttle to AirSim frame rate
            if not args.mock:
                time.sleep(1.0 / cfg["airsim"]["frame_rate"])

        stats[env_name] = n_saved
        logger.info(f"  ✓ {n_saved} frames saved for {env_name}")

    # Train / val / test split & symlink into processed/
    logger.info("\nSplitting into train/val/test ...")
    _create_processed_split(cfg, base, environments)

    # Summary
    logger.success(f"\nData collection complete!")
    logger.info(f"  Total frames : {total_saved}")
    for env, n in stats.items():
        logger.info(f"    {env:<20}: {n} frames")
    logger.info(f"  Output dir   : {base}")


def _create_processed_split(cfg: dict, base: Path, environments: list) -> None:
    """Create processed/images/{train,val,test} with copied images."""
    import shutil
    split = cfg["detection"]["training"]["dataset_split"]
    raw_dir = base / "raw"
    ann_dir = base / "annotations"

    for split_name in ("train", "val", "test"):
        (base / "processed" / "images" / split_name).mkdir(parents=True, exist_ok=True)
        (base / "processed" / "labels" / split_name).mkdir(parents=True, exist_ok=True)

    for env_name in environments:
        imgs = sorted((raw_dir / env_name).glob("*.jpg"))
        n    = len(imgs)
        if n == 0:
            continue

        n_train = int(n * split[0])
        n_val   = int(n * split[1])

        splits = {
            "train": imgs[:n_train],
            "val":   imgs[n_train:n_train + n_val],
            "test":  imgs[n_train + n_val:],
        }

        for split_name, split_imgs in splits.items():
            img_dst = base / "processed" / "images" / split_name
            lbl_dst = base / "processed" / "labels" / split_name
            for img_path in split_imgs:
                lbl_path = ann_dir / env_name / (img_path.stem + ".txt")
                shutil.copy2(img_path, img_dst / img_path.name)
                if lbl_path.exists():
                    shutil.copy2(lbl_path, lbl_dst / lbl_path.name)

    logger.info("  Processed split created in data/processed/")


def main():
    args = parse_args()
    with open(ROOT / args.config) as f:
        cfg = yaml.safe_load(f)
    collect(cfg, args)


if __name__ == "__main__":
    main()
