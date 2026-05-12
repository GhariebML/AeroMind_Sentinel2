"""Export AeroMind Sentinel highway events for the web dashboard.

This script is the bridge between live/model output and the hackathon dashboard.
It accepts either:

1. A JSON file containing already-normalized highway events, or
2. No input, in which case it writes a realistic demo event file.

The dashboard reads `experiments/results/highway_events.json` first. If that file
exists, `/api/highway/events` returns it as `source=live_model`; otherwise the
API falls back to built-in mock data.

Example:
    python scripts/export_highway_events.py
    python scripts/export_highway_events.py --input experiments/results/model_tracks.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "experiments" / "results" / "highway_events.json"

EVENT_WEIGHTS = {
    "accident": 95,
    "stopped_vehicle": 72,
    "congestion": 58,
    "pedestrian_on_highway": 88,
    "blocked_lane": 80,
    "emergency_vehicle": 45,
}


def classify_severity(score: int) -> str:
    if score >= 85:
        return "critical"
    if score >= 70:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def calculate_highway_risk(event: dict[str, Any]) -> int:
    event_type = event.get("type", "congestion")
    base = EVENT_WEIGHTS.get(event_type, 35)
    confidence = max(0.0, min(float(event.get("confidence", 0.5)), 1.0))
    speed = float(event.get("speed", 0))
    lane = str(event.get("lane", "unknown"))
    score = base + confidence * 18 - 15
    if event_type == "stopped_vehicle" and speed < 5:
        score += 10
    if event_type == "pedestrian_on_highway":
        score += 8
    score += -8 if "shoulder" in lane.lower() else 4
    return int(max(0, min(round(score), 100)))


def normalize_event(raw: dict[str, Any], index: int) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    event = {
        "id": str(raw.get("id", f"live-{index:03d}")),
        "type": raw.get("type", infer_event_type(raw)),
        "confidence": float(raw.get("confidence", raw.get("score", 0.82))),
        "trackId": str(raw.get("trackId", raw.get("track_id", f"TRK-{index:03d}"))),
        "position": raw.get("position", {"x": raw.get("x", 40 + index * 8), "y": raw.get("y", 50)}),
        "speed": float(raw.get("speed", 0)),
        "lane": str(raw.get("lane", "Lane 2")),
        "timestamp": str(raw.get("timestamp", now)),
        "source": "live_model",
    }
    event["riskScore"] = int(raw.get("riskScore", calculate_highway_risk(event)))
    event["severity"] = str(raw.get("severity", classify_severity(event["riskScore"])))
    return event


def infer_event_type(raw: dict[str, Any]) -> str:
    label = str(raw.get("label", raw.get("class_name", "vehicle"))).lower()
    speed = float(raw.get("speed", 0))
    if "accident" in label or "crash" in label:
        return "accident"
    if "pedestrian" in label or "person" in label:
        return "pedestrian_on_highway"
    if "blocked" in label or "debris" in label or "obstacle" in label:
        return "blocked_lane"
    if "emergency" in label or "ambulance" in label or "police" in label:
        return "emergency_vehicle"
    if speed < 5:
        return "stopped_vehicle"
    return "congestion"


def demo_events() -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc).isoformat()
    return [
        {"id": "live-001", "type": "accident", "confidence": 0.9, "trackId": "INC-219", "position": {"x": 58, "y": 48}, "speed": 0, "lane": "Lane 3", "timestamp": now},
        {"id": "live-002", "type": "stopped_vehicle", "confidence": 0.93, "trackId": "CAR-104", "position": {"x": 34, "y": 62}, "speed": 0, "lane": "Lane 2", "timestamp": now},
        {"id": "live-003", "type": "blocked_lane", "confidence": 0.86, "trackId": "OBJ-510", "position": {"x": 25, "y": 55}, "speed": 0, "lane": "Lane 1", "timestamp": now},
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Export AeroMind Sentinel highway events.")
    parser.add_argument("--input", type=Path, help="Optional JSON model output file.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if args.input and args.input.exists():
        data = json.loads(args.input.read_text(encoding="utf-8"))
        raw_events = data.get("events", data) if isinstance(data, dict) else data
    else:
        raw_events = demo_events()

    events = [normalize_event(event, index) for index, event in enumerate(raw_events, start=1)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"source": "live_model", "events": events}, indent=2), encoding="utf-8")
    print(f"Wrote {len(events)} highway event(s) to {args.output}")


if __name__ == "__main__":
    main()
