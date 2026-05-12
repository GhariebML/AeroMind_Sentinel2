"""
scripts/run_demo.py
Live AirSim demonstration — runs the full pipeline in real time:
  AirSim frame → YOLOv8 detect → BoT-SORT track → PPO navigate → OpenCV HUD

Usage:
    python scripts/run_demo.py --scenario dense_urban
    python scripts/run_demo.py --mock          # no AirSim required
    python scripts/run_demo.py --record        # saves video to experiments/results/
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import cv2
import yaml
from loguru import logger


# ─── CLI ─────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="AeroMind AI Live Demo")
    p.add_argument("--config",       default="configs/config.yaml")
    p.add_argument("--scenario",     default="dense_urban",
                   choices=["dense_urban", "highway", "parking_lot",
                            "airport_apron", "campus", "mixed_terrain"])
    p.add_argument("--det-weights",  default="models/detection/best.pt")
    p.add_argument("--reid-weights", default="models/reid/reid_best.pt")
    p.add_argument("--rl-weights",   default="models/rl/ppo_final.zip")
    p.add_argument("--mock",         action="store_true",
                   help="Run without AirSim, using synthetic data")
    p.add_argument("--record",       action="store_true",
                   help="Save annotated video to experiments/results/demo_<scenario>.mp4")
    p.add_argument("--max-frames",   type=int, default=0,
                   help="Stop after N frames (0 = run until Esc)")
    p.add_argument("--display",      action="store_true", default=True,
                   help="Show OpenCV window")
    return p.parse_args()


# ─── System loader ────────────────────────────────────────────────────────────

def load_system(cfg: dict, args: argparse.Namespace):
    """Instantiate all pipeline components."""
    from src.detection.detector  import AerialDetector
    from src.tracking.tracker    import BotSortTracker, ReIDModule
    from src.navigation.rl_controller import RLNavigationController
    from src.simulation.airsim_env    import AerialTrackingEnv

    logger.info("Loading detection model ...")
    detector = AerialDetector({**cfg["detection"], "weights": args.det_weights})

    logger.info("Loading Re-ID module ...")
    reid_cfg = {**cfg["reid"], "weights": args.reid_weights}
    reid     = ReIDModule(reid_cfg)

    logger.info("Building BoT-SORT tracker ...")
    tracker = BotSortTracker(cfg["tracking"], reid_module=reid)

    logger.info("Building Gymnasium environment ...")
    env = AerialTrackingEnv(cfg, detector=detector, tracker=tracker)

    logger.info("Loading PPO navigation controller ...")
    controller = RLNavigationController(cfg, env=env)
    rl_path = ROOT / args.rl_weights
    if rl_path.exists():
        controller.load(str(rl_path))
        logger.info(f"PPO weights loaded from {rl_path}")
    else:
        logger.warning("RL weights not found — using random policy for demo.")
        controller.build(env=env)

    return detector, tracker, controller, env


# ─── HUD overlay ─────────────────────────────────────────────────────────────

# Colour palette (BGR) — deterministic per track ID
_PALETTE = np.array([
    [0, 255, 128], [255, 80, 0],  [0, 150, 255], [255, 255, 0],
    [200, 0, 255], [0, 200, 200], [255, 120, 120], [120, 255, 200],
], dtype=np.uint8)


def track_color(track_id: int):
    c = _PALETTE[track_id % len(_PALETTE)]
    return int(c[0]), int(c[1]), int(c[2])


def draw_tracks(frame: np.ndarray, tracks, detector_frame: np.ndarray) -> np.ndarray:
    """Draw bounding boxes + track IDs on the frame."""
    out = frame.copy()
    for t in tracks:
        x1, y1, x2, y2 = t.bbox.astype(int)
        color = track_color(t.id)
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)

        label = f"ID:{t.id} {t.class_name} {t.confidence:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        cv2.rectangle(out, (x1, max(y1 - th - 6, 0)), (x1 + tw + 4, max(y1, th + 6)),
                      color, -1)
        cv2.putText(out, label, (x1 + 2, max(y1 - 4, th + 2)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
    return out


def draw_hud(frame: np.ndarray, info: dict, scenario: str) -> np.ndarray:
    """Render the metrics HUD panel in the top-left corner."""
    out   = frame.copy()
    h, w  = out.shape[:2]
    panel = np.zeros((140, 280, 3), dtype=np.uint8)
    panel[:] = (20, 20, 20)
    cv2.rectangle(panel, (0, 0), (279, 139), (0, 200, 100), 1)

    lines = [
        f"AeroMind AI Demo",
        f"Scenario : {scenario}",
        f"Tracks   : {info.get('n_tracks', 0):3d}",
        f"MOTA     : {info.get('mota', 0)*100:5.1f}%",
        f"Energy   : {info.get('energy_J', 0):6.1f} J",
        f"Battery  : {info.get('battery', 1)*100:5.1f}%",
        f"FPS      : {info.get('fps', 0):5.1f}",
    ]
    for i, line in enumerate(lines):
        color = (0, 220, 100) if i == 0 else (200, 200, 200)
        cv2.putText(panel, line, (6, 16 + i * 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, color, 1)

    # Battery bar
    batt = max(0.0, min(1.0, info.get("battery", 1.0)))
    bar_color = (0, 200, 50) if batt > 0.3 else (0, 60, 220)
    cv2.rectangle(panel, (6, 125), (6 + int(268 * batt), 135), bar_color, -1)
    cv2.rectangle(panel, (6, 125), (274, 135), (80, 80, 80), 1)

    out[10:150, 10:290] = panel
    return out


# ─── Main demo loop ───────────────────────────────────────────────────────────

def run_demo(cfg: dict, args: argparse.Namespace) -> None:
    detector, tracker, controller, env = load_system(cfg, args)

    # JPEG frames for browser-compatible MJPEG streaming (no codec needed)
    frames_dir = None
    if args.record:
        frames_dir = ROOT / "experiments" / "results" / f"frames_{args.scenario}"
        frames_dir.mkdir(parents=True, exist_ok=True)
        for old in frames_dir.glob("*.jpg"):
            old.unlink()
        logger.info(f"Saving frames → {frames_dir}")

    logger.info("=" * 60)
    logger.info(f"  AeroMind AI Live Demo | scenario={args.scenario}")
    logger.info(f"  Mock mode : {args.mock}")
    logger.info("  Press [Esc] to quit | [s] to save screenshot")
    logger.info("=" * 60)

    obs, _ = env.reset()
    frame_idx   = 0
    fps_timer   = time.perf_counter()
    fps_history = []
    cumulative_info = {"mota": 0.0, "energy_J": 0.0, "battery": 1.0, "fps": 0.0}

    while True:
        t0 = time.perf_counter()

        # PPO action
        action = controller.predict(obs, deterministic=True)

        # Environment step
        obs, reward, terminated, truncated, step_info = env.step(action)

        # Get rendered frame
        raw_frame = env.render()
        if raw_frame is None or raw_frame.size == 0:
            raw_frame = np.zeros((640, 640, 3), dtype=np.uint8)

        # Collect active tracks from the env's last perception run
        # (the env exposes the frame via render(); tracks are tracked internally)
        tracks = env._last_tracks

        # Draw tracks
        annotated = draw_tracks(raw_frame, tracks, raw_frame)

        # FPS
        t1  = time.perf_counter()
        fps = 1.0 / max(t1 - t0, 1e-6)
        fps_history.append(fps)
        if len(fps_history) > 30:
            fps_history.pop(0)

        cumulative_info.update({
            "n_tracks": step_info.get("n_tracks", 0),
            "energy_J": step_info.get("energy_consumed", 0.0),
            "battery":  step_info.get("battery_remaining", 1.0),
            "fps":      np.mean(fps_history),
        })

        # Draw HUD
        final = draw_hud(annotated, cumulative_info, args.scenario)

        # Display
        if args.display:
            cv2.imshow("AeroMind AI Demo", final)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:       # Esc
                break
            elif key == ord("s"):
                ss_path = ROOT / "experiments" / "results" / f"screenshot_{frame_idx:05d}.jpg"
                cv2.imwrite(str(ss_path), final)
                logger.info(f"Screenshot saved → {ss_path}")

        # Write JPEG frame for MJPEG streaming
        if frames_dir is not None:
            cv2.imwrite(str(frames_dir / f"{frame_idx:05d}.jpg"), final, [cv2.IMWRITE_JPEG_QUALITY, 85])

        # Logging
        if frame_idx % 30 == 0:
            logger.info(
                f"Frame {frame_idx:05d} | "
                f"tracks={step_info.get('n_tracks',0):3d} | "
                f"energy={step_info.get('energy_consumed',0):.1f}J | "
                f"battery={step_info.get('battery_remaining',1)*100:.1f}% | "
                f"fps={fps:.1f} | reward={reward:.2f}"
            )

        frame_idx += 1

        if (args.max_frames > 0 and frame_idx >= args.max_frames):
            logger.info(f"Reached max frames ({args.max_frames}). Stopping.")
            break

        if terminated or truncated:
            logger.info("Episode ended — resetting environment.")
            obs, _ = env.reset()

    # Cleanup
    cv2.destroyAllWindows()
    if frames_dir is not None:
        n = len(list(frames_dir.glob('*.jpg')))
        logger.success(f"Saved {n} JPEG frames → {frames_dir}")

    logger.success(f"Demo complete | total frames={frame_idx}")


# ─── Entry ───────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    with open(ROOT / args.config) as f:
        cfg = yaml.safe_load(f)

    if not args.mock:
        logger.info("Connecting to AirSim — make sure Unreal Engine is running.")
        logger.info(f"AirSim settings: configs/airsim_settings.json")
        logger.info("Use --mock to run without AirSim.\n")

    run_demo(cfg, args)


if __name__ == "__main__":
    main()
