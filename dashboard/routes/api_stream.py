"""
dashboard/routes/api_stream.py — MJPEG streaming and test/eval runner routes.
"""
from __future__ import annotations
import sys, subprocess, os
import time as _time
from datetime import datetime
from pathlib import Path
from flask import Blueprint, Response, jsonify
import dashboard.database as db

api_stream_bp = Blueprint("api_stream", __name__)
_ROOT = Path(__file__).resolve().parent.parent.parent
IS_VERCEL = any(os.environ.get(k) for k in ["VERCEL", "VERCEL_ENV", "VERCEL_URL", "AWS_LAMBDA_FUNCTION_NAME"])

def _read_json(path, default=None):
    import json
    try:
        if path.exists():
            with open(path, encoding="utf-8") as f: return json.load(f)
    except Exception: pass
    return default if default is not None else {}

def _iter_frames_live():
    try:
        import cv2, numpy as np
    except ImportError:
        while True:
            yield b"--frame\r\nContent-Type: text/plain\r\n\r\nOpenCV not available\r\n"
            _time.sleep(2.0)
        return
    import numpy as np
    last_dir, frame_list, frame_idx = None, [], 0
    def _placeholder():
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(img, "AeroMind AI — Simulation Ready", (60, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 200, 120), 2)
        cv2.putText(img, "Click START to launch the pipeline", (90, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 160, 255), 1)
        _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return buf.tobytes()
    while True:
        best_dir, best_mtime = None, 0.0
        try:
            for d in (_ROOT / "experiments" / "results").glob("frames_*/"):
                mt = d.stat().st_mtime
                if mt > best_mtime: best_mtime, best_dir = mt, d
        except Exception: pass
        if best_dir and best_dir != last_dir:
            try: frame_list = sorted(best_dir.glob("*.jpg")); frame_idx = 0; last_dir = best_dir
            except Exception: frame_list = []
        if frame_list:
            frame_idx = frame_idx % len(frame_list)
            try: yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_list[frame_idx].read_bytes() + b"\r\n"
            except Exception: pass
            frame_idx += 1; _time.sleep(1.0 / 15)
        else:
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + _placeholder() + b"\r\n"
            _time.sleep(2.0)

@api_stream_bp.route("/api/stream/live")
def api_stream_live():
    return Response(_iter_frames_live(), mimetype="multipart/x-mixed-replace; boundary=frame")

@api_stream_bp.route("/api/stream/<scenario>")
def api_stream(scenario: str):
    return Response(_iter_frames_live(), mimetype="multipart/x-mixed-replace; boundary=frame")

@api_stream_bp.route("/api/stream")
def api_stream_default():
    return api_stream("dense_urban")

@api_stream_bp.route("/api/framecount/<scenario>")
def api_framecount(scenario: str):
    d = _ROOT / "experiments" / "results" / f"frames_{scenario}"
    n = len(list(d.glob("*.jpg"))) if d.exists() else 0
    return jsonify({"count": n, "ready": n > 0, "scenario": scenario})

@api_stream_bp.route("/api/telemetry")
def api_telemetry():
    if IS_VERCEL:
        import random
        return jsonify({"step": int(_time.time() % 1000), "n_tracks": random.randint(3, 8),
            "fps": random.uniform(28.5, 32.0), "pos_x": random.uniform(-50, 50),
            "pos_y": random.uniform(-50, 50), "pos_z": random.uniform(10, 25),
            "battery_pct": 100 - ((_time.time() % 3600) / 60)})
    data = _read_json(_ROOT / "experiments" / "results" / "swarm_telemetry.json", default={"drones": [], "targets": []})
    return jsonify(data)

@api_stream_bp.route("/api/sim/tracks")
def api_sim_tracks():
    if IS_VERCEL:
        return jsonify({"tracks": []})
    data = _read_json(_ROOT / "experiments" / "results" / "sim_tracks.json", default={"tracks": []})
    return jsonify(data)

@api_stream_bp.route("/api/runtest")
def api_runtest():
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v", "--tb=no", "-q"],
            capture_output=True, text=True, cwd=str(_ROOT), timeout=60)
        lines = r.stdout.strip().splitlines()
        passed = sum(1 for l in lines if " PASSED" in l)
        failed = sum(1 for l in lines if " FAILED" in l)
        skipped = sum(1 for l in lines if " SKIPPED" in l)
        summary = next((l for l in reversed(lines) if "passed" in l or "failed" in l), "")
        db.log_event(f"Tests: {passed} passed, {failed} failed — {summary}",
            level="INFO" if not failed else "WARNING", component="tests")
        return jsonify({"passed": passed, "failed": failed, "skipped": skipped,
            "summary": summary, "exit_code": r.returncode, "lines": lines[-30:]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_stream_bp.route("/api/runeval")
def api_runeval():
    try:
        r = subprocess.run([sys.executable, "scripts/evaluate.py", "--config", "configs/config.yaml", "--mock"],
            capture_output=True, text=True, cwd=str(_ROOT), timeout=120)
        results = _read_json(_ROOT / "experiments" / "results" / "eval_results.json", default={})
        if results.get("summary"): db.save_eval(results["summary"], source="evaluate.py")
        return jsonify({"exit_code": r.returncode, "results": results, "stderr_tail": r.stderr.strip().splitlines()[-10:]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
