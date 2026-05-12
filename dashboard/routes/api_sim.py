"""
dashboard/routes/api_sim.py — Simulation control API endpoints.
"""

from __future__ import annotations

import json
import os
import sys
import subprocess
import threading
import time as _time
from pathlib import Path

from flask import Blueprint, jsonify, request

import dashboard.database as db

api_sim_bp = Blueprint("api_sim", __name__)

_ROOT = Path(__file__).resolve().parent.parent.parent
IS_VERCEL = any(os.environ.get(k) for k in ["VERCEL", "VERCEL_ENV", "VERCEL_URL", "AWS_LAMBDA_FUNCTION_NAME"])

STOP_SENTINEL = _ROOT / "experiments" / "results" / ".sim_stop"
TELEMETRY_FILE = _ROOT / "experiments" / "results" / "sim_telemetry.json"
SIM_LOG_FILE = _ROOT / "experiments" / "results" / "sim_last.log"

_sim_proc: subprocess.Popen | None = None
_active_run: int | None = None
_tele_thread: threading.Thread | None = None
_tele_stop = threading.Event()
_last_tele_step: int | None = None


def _read_json(path: Path, default=None):
    try:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default if default is not None else {}


# ─── Background telemetry recorder ───────────────────────────────────────────

def _telemetry_recorder():
    """Background thread: writes telemetry snapshots to the DB."""
    global _last_tele_step
    while not _tele_stop.is_set():
        run_id = _active_run
        if run_id is not None:
            t = _read_json(TELEMETRY_FILE, default={})
            step = t.get("step")
            if t and step != _last_tele_step:
                try:
                    db.insert_telemetry(run_id, t)
                    _last_tele_step = step
                except Exception:
                    pass
        _tele_stop.wait(1.0)


def _start_tele_thread():
    global _tele_thread, _last_tele_step
    _tele_stop.clear()
    _last_tele_step = None
    _tele_thread = threading.Thread(target=_telemetry_recorder, daemon=True)
    _tele_thread.start()


def _stop_tele_thread():
    _tele_stop.set()
    if _tele_thread:
        _tele_thread.join(timeout=3)


# ─── Routes ──────────────────────────────────────────────────────────────────

@api_sim_bp.route("/api/sim/start", methods=["POST"])
def api_sim_start():
    global _active_run, _sim_proc

    body = request.get_json(silent=True) or {}
    scenario = body.get("scenario", "dense_urban")
    use_mock = body.get("mock", True)

    if IS_VERCEL:
        _active_run = 1
        return jsonify({"status": "started", "pid": 999, "scenario": scenario,
                        "mock": True, "run_id": 1, "note": "Vercel Mock Mode"})

    if _sim_proc and _sim_proc.poll() is None:
        STOP_SENTINEL.parent.mkdir(parents=True, exist_ok=True)
        STOP_SENTINEL.touch()
        try:
            _sim_proc.wait(timeout=5)
        except Exception:
            _sim_proc.kill()

    STOP_SENTINEL.unlink(missing_ok=True)
    SIM_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    run_id = db.create_run(scenario, use_mock)
    _active_run = run_id
    db.log_event(f"Simulation started — scenario={scenario} mock={use_mock} run_id={run_id}",
                 level="INFO", component="sim")

    cmd = [sys.executable, str(_ROOT / "scripts" / "run_simulation.py"),
           "--scenario", scenario, "--record"]
    if use_mock:
        cmd.append("--mock")

    try:
        log_fh = open(SIM_LOG_FILE, "w", buffering=1)
        _sim_proc = subprocess.Popen(cmd, cwd=str(_ROOT), stdout=log_fh, stderr=subprocess.STDOUT)
        _start_tele_thread()
        return jsonify({"status": "started", "pid": _sim_proc.pid,
                        "scenario": scenario, "mock": use_mock, "run_id": run_id})
    except Exception as e:
        db.log_event(f"Simulation failed to start: {e}", level="ERROR", component="sim")
        db.finish_run(run_id, "error", {})
        _active_run = None
        return jsonify({"status": "error", "error": str(e)}), 500


@api_sim_bp.route("/api/sim/stop", methods=["POST"])
def api_sim_stop():
    global _sim_proc, _active_run

    if IS_VERCEL:
        _active_run = None
        _sim_proc = None
        return jsonify({"status": "stopped", "note": "Vercel Mock Stop"})

    STOP_SENTINEL.parent.mkdir(parents=True, exist_ok=True)
    STOP_SENTINEL.touch()
    if _sim_proc and _sim_proc.poll() is None:
        try:
            _sim_proc.wait(timeout=6)
        except Exception:
            _sim_proc.kill()

    _stop_tele_thread()
    last_tele = _read_json(TELEMETRY_FILE, default={})
    if _active_run is not None:
        db.finish_run(_active_run, "stopped", last_tele)
        db.log_event(f"Simulation stopped — run_id={_active_run}", component="sim")
        _active_run = None

    _sim_proc = None
    STOP_SENTINEL.unlink(missing_ok=True)
    return jsonify({"status": "stopped"})


@api_sim_bp.route("/api/sim/weather", methods=["POST"])
def api_sim_weather():
    body = request.get_json(silent=True) or {}
    w = body.get("weather", "clear")
    wf = _ROOT / "experiments" / "results" / "weather_control.json"

    if IS_VERCEL:
        return jsonify({"status": "updated", "weather": w, "note": "Vercel Mock"})

    wf.parent.mkdir(parents=True, exist_ok=True)
    wf.write_text(json.dumps({"weather": w}))
    db.log_event(f"Weather set to: {w}", component="sim")
    return jsonify({"status": "ok", "weather": w})


@api_sim_bp.route("/api/sim/status")
def api_sim_status():
    global _active_run
    running = bool(_sim_proc and _sim_proc.poll() is None)

    if IS_VERCEL:
        running = True

    if not running and _active_run is not None:
        last_tele = _read_json(TELEMETRY_FILE, default={})
        _stop_tele_thread()
        db.finish_run(_active_run, "completed", last_tele)

        try:
            scenario = db.get_run(_active_run).get("scenario", "unknown")
            frames_dir = _ROOT / "experiments" / "results" / f"frames_{scenario}"
            if frames_dir.exists():
                frames = sorted(frames_dir.glob("*.jpg"))
                if frames:
                    final_frame = frames[-1]
                    db.add_capture(
                        file_path=str(final_frame.relative_to(_ROOT)),
                        scenario=scenario, run_id=_active_run, telemetry=last_tele,
                        title=f"Completed Run: {scenario}",
                        description="Auto-captured at end of simulation session.",
                    )
        except Exception as e:
            db.log_event(f"Auto-capture failed: {e}", level="WARNING", component="sim")

        db.log_event(f"Simulation completed — run_id={_active_run}", component="sim")
        _active_run = None

    telemetry = _read_json(TELEMETRY_FILE, default={})
    return jsonify({
        "running": running, "run_id": _active_run, "active_run": _active_run,
        "telemetry": telemetry if not IS_VERCEL else {
            "step": int(_time.time() % 1000), "n_tracks": 5, "fps": 30.0,
            "pos_x": 120.5 + (_time.time() % 10), "pos_y": -45.2 + (_time.time() % 5),
            "pos_z": 15.0 + (_time.time() % 2), "battery_pct": 98.2, "is_mock": True,
        },
    })


@api_sim_bp.route("/api/sim/log")
def api_sim_log():
    if SIM_LOG_FILE.exists():
        lines = SIM_LOG_FILE.read_text(errors="replace").splitlines()
        return jsonify({"lines": lines[-80:]})
    return jsonify({"lines": []})
