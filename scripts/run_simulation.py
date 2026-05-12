"""
scripts/run_simulation.py
━━━━━━━━━━━━━━━━━━━━━━━━━
Full AeroMind AI simulation loop.

  AirSim frame → YOLOv8 detect → BoT-SORT track → PPO navigate → HUD → JPEG frames

Usage:
    python scripts/run_simulation.py                       # connect to AirSim
    python scripts/run_simulation.py --mock                # rich synthetic mode
    python scripts/run_simulation.py --mock --record       # write frames for dashboard
    python scripts/run_simulation.py --scenario highway    # choose scenario
    python scripts/run_simulation.py --max-frames 300      # stop after N frames

Dashboard integration:
    The dashboard POST /api/sim/start launches this with --mock --record.
    Write experiments/results/.sim_stop to terminate gracefully.
    Live telemetry → experiments/results/sim_telemetry.json (updated ~1 Hz).
"""
from __future__ import annotations

import argparse, json, math, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import cv2, numpy as np, yaml
from loguru import logger

STOP_SENTINEL = ROOT / "experiments" / "results" / ".sim_stop"
TELEMETRY_FILE = ROOT / "experiments" / "results" / "sim_telemetry.json"


# ─── CLI ──────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="AeroMind AI AirSim Simulation Runner")
    p.add_argument("--config",    default="configs/config.yaml")
    p.add_argument("--scenario",  default="dense_urban",
                   choices=["dense_urban","highway","parking_lot",
                             "airport_apron","campus","mixed_terrain"])
    p.add_argument("--det-weights",  default="models/detection/best.pt")
    p.add_argument("--reid-weights", default="models/reid/reid_best.pt")
    p.add_argument("--rl-weights",   default="models/rl/ppo_final.zip")
    p.add_argument("--mock",      action="store_true",
                   help="Run without AirSim — use animated synthetic frames")
    p.add_argument("--record",    action="store_true",
                   help="Save JPEG frames for MJPEG dashboard stream")
    p.add_argument("--max-frames",type=int, default=0,
                   help="Stop after N frames (0 = run indefinitely)")
    p.add_argument("--display",   action="store_true",
                   help="Show OpenCV window (desktop only)")
    p.add_argument("--online",    action="store_true",
                   help="Enable real-time online adaptation")
    return p.parse_args()


# ─── Colour palette ───────────────────────────────────────────────────────────

_PAL = np.array([
    [0,200,120],[255,80,0],[0,150,255],[220,220,0],
    [180,0,255],[0,200,200],[255,120,120],[120,255,200],
], dtype=np.uint8)

def _track_color(tid: int):
    c = _PAL[tid % len(_PAL)]
    return int(c[0]), int(c[1]), int(c[2])


# ─── Annotate frame ───────────────────────────────────────────────────────────

def annotate(frame: np.ndarray, tracks, info: dict, scenario: str) -> np.ndarray:
    """Draw bounding boxes, track IDs, trajectory trails and HUD."""
    out = frame.copy()
    h, w = out.shape[:2]

    # Track history for trails (module-level dict)
    hist = annotate._hist
    for t in tracks:
        x1, y1, x2, y2 = t.bbox.astype(int)
        col = _track_color(t.id)
        # Trail
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        hist.setdefault(t.id, []).append((cx, cy))
        if len(hist[t.id]) > 20:
            hist[t.id] = hist[t.id][-20:]
        pts = hist[t.id]
        for i in range(1, len(pts)):
            alpha = i / len(pts)
            tc = tuple(int(c * alpha) for c in col)
            cv2.line(out, pts[i-1], pts[i], tc, 1)
        # BBox
        cv2.rectangle(out, (x1, y1), (x2, y2), col, 2)
        label = f"ID:{t.id} {t.class_name} {t.confidence:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
        cv2.rectangle(out, (x1, max(y1-th-6,0)), (x1+tw+4, max(y1,th+6)), col, -1)
        cv2.putText(out, label, (x1+2, max(y1-3, th+2)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0,0,0), 1)

    # HUD panel
    panel_h, panel_w = 170, 290
    panel = np.zeros((panel_h, panel_w, 3), dtype=np.uint8)
    panel[:] = (15, 20, 30)
    cv2.rectangle(panel, (0,0), (panel_w-1, panel_h-1), (0,200,120), 1)

    mode_tag = "AIRSIM" if not info.get("mock") else "MOCK"
    lines = [
        f"AeroMind AI  Aerial Tracking  [{mode_tag}]",
        f"Scenario : {scenario}",
        f"Tracks   : {info.get('n_tracks',0):3d}",
        f"MOTA est : {info.get('mota',0)*100:5.1f}%",
        f"Energy   : {info.get('energy_J',0):6.1f} J",
        f"Battery  : {info.get('battery',1)*100:5.1f}%",
        f"FPS      : {info.get('fps',0):5.1f}",
        f"Reward   : {info.get('reward',0):+6.2f}",
    ]
    for i, ln in enumerate(lines):
        col = (0,220,100) if i == 0 else (190,200,210)
        cv2.putText(panel, ln, (6, 16+i*19),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, col, 1)
    # Battery bar
    batt = max(0.0, min(1.0, info.get("battery", 1.0)))
    bc = (0,200,50) if batt > 0.3 else (0,60,220)
    cv2.rectangle(panel, (6, panel_h-14), (6+int((panel_w-14)*batt), panel_h-6), bc, -1)
    cv2.rectangle(panel, (6, panel_h-14), (panel_w-8, panel_h-6), (80,80,80), 1)

    out[10:10+panel_h, 10:10+panel_w] = panel
    return out

annotate._hist: dict = {}


# ─── Telemetry writer ─────────────────────────────────────────────────────────

def write_telemetry(info: dict, scenario: str, frame_idx: int) -> None:
    payload = {
        "frame":      frame_idx,
        "scenario":   scenario,
        "timestamp":  time.time(),
        **info,
    }
    TELEMETRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TELEMETRY_FILE, "w") as f:
        json.dump(payload, f)

def write_tracks(tracks, frame_idx: int) -> None:
    track_list = []
    for t in tracks:
        track_list.append({
            "id": t.id,
            "class_name": t.class_name,
            "confidence": float(t.confidence),
            "bbox": [float(x) for x in t.bbox]
        })
    payload = {"frame": frame_idx, "timestamp": time.time(), "tracks": track_list}
    track_file = ROOT / "experiments" / "results" / "sim_tracks.json"
    with open(track_file, "w") as f:
        json.dump(payload, f)


# ─── Component loader ─────────────────────────────────────────────────────────

def load_pipeline(cfg: dict, args):
    """Load detector, tracker, PPO controller and Gymnasium env."""
    from src.tracking.tracker          import BotSortTracker, ReIDModule
    from src.navigation.rl_controller  import RLNavigationController
    from src.simulation.airsim_env     import AerialTrackingEnv

    if args.mock:
        # In mock mode skip the real detector — SyntheticScene provides GT bboxes
        # directly into BoT-SORT, giving ~10x better FPS with perfect tracking
        logger.info("Mock mode: skipping YOLOv8 detector load (using SyntheticScene GT)")
        detector = None
    else:
        from src.detection.detector import AerialDetector
        det_w = str(ROOT / args.det_weights)
        det_cfg = {**cfg["detection"], "weights": det_w}
        logger.info("Loading detector …")
        detector = AerialDetector(det_cfg)

    # Re-ID (lightweight, always load)
    reid_w = str(ROOT / args.reid_weights)
    logger.info("Loading Re-ID module …")
    reid = ReIDModule({**cfg["reid"], "weights": reid_w})

    # Tracker
    logger.info("Building BoT-SORT tracker …")
    tracker = BotSortTracker(cfg["tracking"], reid_module=reid)

    # Environment (handles AirSim connection internally)
    logger.info("Building Gymnasium environment …")
    env = AerialTrackingEnv(cfg, detector=detector, tracker=tracker)

    # PPO controller
    logger.info("Loading PPO controller …")
    ctrl = RLNavigationController(cfg, env=env)
    rl_path = ROOT / args.rl_weights
    if rl_path.exists():
        ctrl.load(str(rl_path))
        logger.success(f"PPO weights loaded from {rl_path}")
    else:
        logger.warning("PPO weights not found — building with random policy.")
        ctrl.build(env=env)

    # Online adaptation components
    online_components = None
    if args.online:
        from src.models.temporal_encoder import TemporalStateEncoder
        from src.control.rt_controller    import RealTimeFlightController
        from src.rewards.rt_reward       import RealTimeRewardComputer
        
        logger.info("Initializing Online Adaptation Layer …")
        encoder = TemporalStateEncoder(state_dim=83, hidden_dim=128, seq_len=10)
        # Wrap the base controller's model in the real-time flight controller
        rt_ctrl = RealTimeFlightController(ctrl.model, learning_rate=1e-4)
        reward_fn = RealTimeRewardComputer()
        online_components = (encoder, rt_ctrl, reward_fn)

    return detector, tracker, ctrl, env, online_components



# ─── Main loop ────────────────────────────────────────────────────────────────

def run(cfg: dict, args) -> None:
    # Clear any previous stop sentinel
    STOP_SENTINEL.unlink(missing_ok=True)

    # Frames output directory
    frames_dir = None
    if args.record:
        frames_dir = ROOT / "experiments" / "results" / f"frames_{args.scenario}"
        frames_dir.mkdir(parents=True, exist_ok=True)
        for old in frames_dir.glob("*.jpg"):
            try:
                old.unlink(missing_ok=True)
            except Exception:
                pass
        logger.info(f"Recording frames → {frames_dir}")

    detector, tracker, ctrl, env, online_comp = load_pipeline(cfg, args)
    encoder, rt_ctrl, reward_fn = online_comp if online_comp else (None, None, None)

    logger.info("=" * 60)
    logger.info(f"  AeroMind AI Simulation  |  scenario={args.scenario}")
    logger.info(f"  Mock={args.mock}  |  Record={args.record}")
    logger.info("  Stop: Ctrl-C  or  touch experiments/results/.sim_stop")
    logger.info("=" * 60)

    obs, _ = env.reset()
    fps_hist: list[float] = []
    cumulative = {
        "mock": args.mock,
        "n_tracks": 0, "mota": 0.0, "energy_J": 0.0,
        "battery": 1.0, "fps": 0.0, "reward": 0.0,
    }

    frame_idx = 0
    try:
        while True:
            # Stop-file sentinel (dashboard can stop gracefully)
            if STOP_SENTINEL.exists():
                logger.info("Stop sentinel detected — shutting down.")
                STOP_SENTINEL.unlink(missing_ok=True)
                break

            t0 = time.perf_counter()

            # Action selection
            if args.online:
                encoder.push(obs)
                # Note: rt_ctrl handles internal state conversion/prediction
                action = rt_ctrl.act(obs)
            else:
                action = ctrl.predict(obs, deterministic=True)
                
            prev_obs = obs
            obs, reward, terminated, truncated, info = env.step(action)
            
            # Online adaptation update
            if args.online:
                # Map info to the reward computer's expected telemetry format
                telemetry = {
                    "active_tracks": info.get("n_tracks", 0),
                    "id_switches":   info.get("id_switches", 0),
                    "speed":        info.get("velocity_magnitude", 0.0),
                    "path_length":   info.get("distance_traveled", 0.0),
                    "delta_altitude": info.get("altitude_change", 0.0),
                    "dt":           0.05,
                    "lidar_distances": info.get("lidar", []),
                    "target_distances": info.get("target_distances", [])
                }
                rt_reward = reward_fn.compute(telemetry)
                rt_ctrl.observe(prev_obs, action, rt_reward, obs, terminated or truncated)
                reward = rt_reward # Override for HUD display

            # Raw frame from environment
            raw = env.render()
            if raw is None or raw.size == 0:
                raw = np.zeros((640, 640, 3), dtype=np.uint8)

            # Perception (use cached results from the step update to avoid double-updating tracker)
            tracks = env._last_tracks

            # FPS
            fps = 1.0 / max(time.perf_counter() - t0, 1e-6)
            fps_hist.append(fps)
            if len(fps_hist) > 30:
                fps_hist.pop(0)

            cumulative.update({
                "n_tracks": info.get("n_tracks", 0),
                "energy_J": info.get("energy_consumed", 0.0),
                "battery":  info.get("battery_remaining", 1.0),
                "fps":      float(np.mean(fps_hist)),
                "reward":   float(reward),
                # Rough MOTA estimate from track hit rate
                "mota":     min(1.0, info.get("n_tracks", 0) / max(
                    len(env._prev_tracks) + info.get("n_tracks", 0), 1)),
            })

            # Annotate
            final = annotate(raw, tracks, cumulative, args.scenario)

            # Write JPEG frame
            if frames_dir is not None:
                cv2.imwrite(
                    str(frames_dir / f"{frame_idx:06d}.jpg"),
                    cv2.cvtColor(final, cv2.COLOR_RGB2BGR),
                    [cv2.IMWRITE_JPEG_QUALITY, 82],
                )

            # Display
            if args.display:
                cv2.imshow("AeroMind AI Simulation", cv2.cvtColor(final, cv2.COLOR_RGB2BGR))
                key = cv2.waitKey(1) & 0xFF
                if key == 27:
                    break

            # Telemetry and Tracks (update every ~1 s = every ~fps frames)
            if frame_idx % max(1, int(cumulative["fps"])) == 0:
                write_telemetry(cumulative, args.scenario, frame_idx)
                write_tracks(tracks, frame_idx)

            # Console log every 30 frames
            if frame_idx % 30 == 0:
                logger.info(
                    f"[{frame_idx:06d}]  tracks={info.get('n_tracks',0):3d}  "
                    f"energy={info.get('energy_consumed',0):.1f}J  "
                    f"batt={info.get('battery_remaining',1)*100:.1f}%  "
                    f"fps={fps:.1f}  reward={reward:+.2f}"
                )

            frame_idx += 1
            if args.max_frames > 0 and frame_idx >= args.max_frames:
                logger.info(f"Max frames ({args.max_frames}) reached.")
                break

            if terminated or truncated:
                logger.info("Episode ended — resetting environment.")
                obs, _ = env.reset()
                annotate._hist.clear()

    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    finally:
        if args.display:
            cv2.destroyAllWindows()
        # Final telemetry
        cumulative["stopped"] = True
        write_telemetry(cumulative, args.scenario, frame_idx)
        n_frames = len(list(frames_dir.glob("*.jpg"))) if frames_dir else frame_idx
        logger.success(f"Simulation complete | frames={frame_idx}  written={n_frames}")


# ─── Entry ────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    cfg_path = ROOT / args.config
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)

    if not args.mock:
        logger.info("Connecting to AirSim — Unreal Engine must be running.")
        logger.info("Use --mock to run without AirSim.")

    run(cfg, args)


if __name__ == "__main__":
    main()
