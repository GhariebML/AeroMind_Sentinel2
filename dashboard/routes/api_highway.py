"""
dashboard/routes/api_highway.py — Highway-specific product API endpoints.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify

api_highway_bp = Blueprint("api_highway", __name__)

_ROOT = Path(__file__).resolve().parent.parent.parent
IS_VERCEL = any(os.environ.get(k) for k in ["VERCEL", "VERCEL_ENV", "VERCEL_URL", "AWS_LAMBDA_FUNCTION_NAME"])


def _read_json(path: Path, default=None):
    try:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default if default is not None else {}


@api_highway_bp.route("/api/highway/events")
def api_highway_events():
    """Return live model highway events when available, otherwise demo events."""
    live_events_file = _ROOT / "experiments" / "results" / "highway_events.json"
    if live_events_file.exists():
        data = _read_json(live_events_file, default={})
        events = data.get("events", data if isinstance(data, list) else [])
        return jsonify({
            "source": data.get("source", "live_model") if isinstance(data, dict) else "live_model",
            "events": events,
        })

    now = datetime.now().isoformat()
    return jsonify({
        "source": "mock",
        "events": [
            {"id": "evt-001", "type": "stopped_vehicle", "confidence": 0.91, "trackId": "CAR-104",
             "position": {"x": 34, "y": 62}, "speed": 0, "lane": "Lane 2", "timestamp": now,
             "riskScore": 87, "severity": "critical"},
            {"id": "evt-002", "type": "accident", "confidence": 0.88, "trackId": "INC-219",
             "position": {"x": 58, "y": 48}, "speed": 0, "lane": "Lane 3", "timestamp": now,
             "riskScore": 100, "severity": "critical"},
            {"id": "evt-003", "type": "congestion", "confidence": 0.84, "trackId": "ZONE-07",
             "position": {"x": 72, "y": 43}, "speed": 12, "lane": "All lanes", "timestamp": now,
             "riskScore": 62, "severity": "medium"},
            {"id": "evt-004", "type": "pedestrian_on_highway", "confidence": 0.79, "trackId": "PED-022",
             "position": {"x": 46, "y": 71}, "speed": 4, "lane": "Shoulder / Lane 1", "timestamp": now,
             "riskScore": 87, "severity": "critical"},
            {"id": "evt-005", "type": "blocked_lane", "confidence": 0.86, "trackId": "OBJ-510",
             "position": {"x": 25, "y": 55}, "speed": 0, "lane": "Lane 1", "timestamp": now,
             "riskScore": 84, "severity": "high"},
        ],
    })


@api_highway_bp.route("/api/highway/kpis")
def api_highway_kpis():
    """Return highway-specific product KPIs for the demo dashboard."""
    return jsonify({
        "incident_detection_time_sec": 15,
        "alert_generation_latency_ms": 45,
        "high_risk_zone_coverage_pct": 87,
        "congestion_detection_confidence_pct": 84,
        "emergency_response_support_score": 91,
        "technical_core": {
            "mota_pct": 83.2,
            "idf1_pct": 78.5,
            "energy_saved_pct": 34.8,
            "id_switches_per_1k": 11,
            "mission_duration_gain_pct": 72,
        },
    })
