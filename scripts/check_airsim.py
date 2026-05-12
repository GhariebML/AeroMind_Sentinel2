"""
scripts/check_airsim.py  — AirSim connectivity diagnostic
Usage:
    python scripts/check_airsim.py [--ip 127.0.0.1] [--port 41451] [--save]
Exit 0 = AirSim reachable; Exit 1 = not reachable.
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Ensure vendored airsim + msgpackrpc shim are on path
_VENDOR = ROOT / "vendor"
if str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

import cv2, numpy as np
from loguru import logger


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--ip",     default="127.0.0.1")
    p.add_argument("--port",   default=41451, type=int)
    p.add_argument("--camera", default="front_center")
    p.add_argument("--save",   action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    sep = "=" * 54
    logger.info(sep)
    logger.info("  AeroMind AI  AirSim Connectivity Diagnostic")
    logger.info(sep)

    # 1. Package check
    try:
        import airsim
        logger.success("✓  airsim package found")
    except ImportError:
        logger.error("✗  airsim not installed  →  pip install airsim")
        sys.exit(1)

    # 2. TCP connection
    logger.info(f"   Connecting {args.ip}:{args.port} …")
    try:
        client = airsim.MultirotorClient(ip=args.ip, port=args.port)
        client.confirmConnection()
        logger.success(f"✓  Connected to AirSim at {args.ip}:{args.port}")
    except Exception as e:
        logger.error(f"✗  Cannot connect: {e}")
        logger.info("   Start Unreal Engine + AirSim binary first.")
        sys.exit(1)

    # 3. Drone state
    try:
        s   = client.getMultirotorState()
        pos = s.kinematics_estimated.position
        vel = s.kinematics_estimated.linear_velocity
        logger.success(
            f"✓  pos=({pos.x_val:.2f},{pos.y_val:.2f},{pos.z_val:.2f}) m  "
            f"vel=({vel.x_val:.2f},{vel.y_val:.2f},{vel.z_val:.2f}) m/s"
        )
    except Exception as e:
        logger.warning(f"   Drone state unavailable: {e}")

    # 4. Camera frame
    try:
        resp = client.simGetImages([
            airsim.ImageRequest(args.camera, airsim.ImageType.Scene, False, False)
        ])
        if resp and len(resp[0].image_data_uint8) > 0:
            img   = resp[0]
            frame = np.frombuffer(img.image_data_uint8, dtype=np.uint8).reshape(img.height, img.width, 3)
            logger.success(f"✓  Camera '{args.camera}' → {img.width}×{img.height}")
            if args.save:
                out = ROOT / "experiments" / "results" / "airsim_check.jpg"
                out.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(out), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                logger.success(f"   Frame saved → {out}")
        else:
            logger.warning("   Empty camera frame (UE may not be rendering).")
    except Exception as e:
        logger.warning(f"   Camera capture failed: {e}")

    # 5. Vehicles
    try:
        logger.success(f"✓  Vehicles: {client.listVehicles()}")
    except Exception:
        pass

    # 6. API control test
    try:
        client.enableApiControl(True)
        client.armDisarm(True)
        logger.success("✓  API control ENABLED")
        client.armDisarm(False)
        client.enableApiControl(False)
    except Exception as e:
        logger.warning(f"   API control check: {e}")

    logger.info(sep)
    logger.success("  AirSim check PASSED — ready to run simulation.")
    logger.info(sep)
    sys.exit(0)


if __name__ == "__main__":
    main()
