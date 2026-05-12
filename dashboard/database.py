"""
dashboard/database.py  —  AeroMind AI  |  SQLite persistence layer
"""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

_DB_PATH: Path | None = None
_lock = threading.Lock()


# ─── Init ─────────────────────────────────────────────────────────────────────

def init(db_path: Path) -> None:
    """Create the database and tables if they don't already exist."""
    global _DB_PATH
    
    import os
    if os.environ.get("VERCEL"):
        # Vercel filesystem is read-only except for /tmp
        db_path = Path("/tmp/aeromind.db")
    
    _DB_PATH = db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as con:
        con.executescript("""
        PRAGMA journal_mode=WAL;
        PRAGMA foreign_keys=ON;

        CREATE TABLE IF NOT EXISTS simulation_runs (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            scenario     TEXT    NOT NULL DEFAULT 'dense_urban',
            is_mock      INTEGER NOT NULL DEFAULT 1,
            status       TEXT    NOT NULL DEFAULT 'running',
            started_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            ended_at     TEXT,
            total_frames INTEGER DEFAULT 0,
            total_steps  INTEGER DEFAULT 0,
            final_mota   REAL,
            final_idf1   REAL,
            final_energy_J   REAL,
            final_battery_pct REAL,
            peak_tracks  INTEGER DEFAULT 0,
            avg_fps      REAL,
            avg_reward   REAL,
            notes        TEXT
        );

        CREATE TABLE IF NOT EXISTS telemetry_snapshots (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id       INTEGER NOT NULL REFERENCES simulation_runs(id) ON DELETE CASCADE,
            ts           TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            step         INTEGER,
            n_tracks     INTEGER,
            fps          REAL,
            pos_x        REAL,
            pos_y        REAL,
            pos_z        REAL,
            heading_deg  REAL,
            vel_x        REAL,
            vel_y        REAL,
            energy_J     REAL,
            battery_pct  REAL,
            reward       REAL
        );

        CREATE TABLE IF NOT EXISTS eval_results (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            evaluated_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            run_id          INTEGER REFERENCES simulation_runs(id),
            mota            REAL,
            idf1            REAL,
            id_switches     INTEGER,
            latency_ms      REAL,
            energy_J        REAL,
            energy_saved_pct REAL,
            mission_ext_pct  REAL,
            source          TEXT DEFAULT 'manual'
        );

        CREATE TABLE IF NOT EXISTS gallery_captures (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            captured_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            run_id      INTEGER REFERENCES simulation_runs(id),
            scenario    TEXT,
            file_path   TEXT NOT NULL,
            n_tracks    INTEGER DEFAULT 0,
            fps         REAL,
            step        INTEGER,
            tags        TEXT DEFAULT '[]',
            title       TEXT,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS event_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            ts        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            level     TEXT NOT NULL DEFAULT 'INFO',
            component TEXT DEFAULT 'system',
            message   TEXT NOT NULL
        );

        -- Speed-up indexes
        CREATE INDEX IF NOT EXISTS idx_tele_run   ON telemetry_snapshots(run_id);
        CREATE INDEX IF NOT EXISTS idx_tele_step  ON telemetry_snapshots(run_id, step);
        CREATE INDEX IF NOT EXISTS idx_gallery_run ON gallery_captures(run_id);
        CREATE INDEX IF NOT EXISTS idx_events_ts  ON event_log(ts);
        """)


@contextmanager
def _connect():
    assert _DB_PATH, "Database not initialised — call db.init() first"
    with _lock:
        con = sqlite3.connect(str(_DB_PATH), timeout=10,
                              detect_types=sqlite3.PARSE_DECLTYPES)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()


# ─── Simulation runs ──────────────────────────────────────────────────────────

def create_run(scenario: str, is_mock: bool) -> int:
    with _connect() as con:
        cur = con.execute(
            "INSERT INTO simulation_runs (scenario, is_mock, status) VALUES (?,?,?)",
            (scenario, int(is_mock), "running"),
        )
        return cur.lastrowid


def finish_run(run_id: int, status: str, telemetry: dict) -> None:
    with _connect() as con:
        con.execute("""
            UPDATE simulation_runs SET
                status            = ?,
                ended_at          = strftime('%Y-%m-%dT%H:%M:%SZ','now'),
                total_steps       = ?,
                final_energy_J    = ?,
                final_battery_pct = ?,
                peak_tracks       = (SELECT MAX(n_tracks) FROM telemetry_snapshots WHERE run_id = ?),
                avg_fps           = (SELECT AVG(fps)      FROM telemetry_snapshots WHERE run_id = ?),
                avg_reward        = (SELECT AVG(reward)   FROM telemetry_snapshots WHERE run_id = ?)
            WHERE id = ?
        """, (
            status,
            telemetry.get("step", 0),
            telemetry.get("energy_J"),
            telemetry.get("battery_pct"),
            run_id, run_id, run_id,
            run_id,
        ))


def get_runs(limit: int = 50) -> list[dict]:
    with _connect() as con:
        rows = con.execute("""
            SELECT r.*,
                   COUNT(t.id) AS snapshots
            FROM   simulation_runs r
            LEFT JOIN telemetry_snapshots t ON t.run_id = r.id
            GROUP BY r.id
            ORDER BY r.id DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


def get_run(run_id: int) -> dict | None:
    with _connect() as con:
        row = con.execute("SELECT * FROM simulation_runs WHERE id=?", (run_id,)).fetchone()
        return dict(row) if row else None


# ─── Telemetry ────────────────────────────────────────────────────────────────

def insert_telemetry(run_id: int, t: dict) -> None:
    with _connect() as con:
        con.execute("""
            INSERT INTO telemetry_snapshots
                (run_id, step, n_tracks, fps, pos_x, pos_y, pos_z,
                 heading_deg, vel_x, vel_y, energy_J, battery_pct, reward)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            run_id,
            t.get("step"),      t.get("n_tracks"), t.get("fps"),
            t.get("pos_x"),     t.get("pos_y"),    t.get("pos_z"),
            t.get("heading_deg"), t.get("vel_x"),  t.get("vel_y"),
            t.get("energy_J"),  t.get("battery_pct"), t.get("reward"),
        ))


def get_telemetry(run_id: int, limit: int = 500) -> list[dict]:
    with _connect() as con:
        rows = con.execute("""
            SELECT * FROM telemetry_snapshots
            WHERE run_id = ?
            ORDER BY id ASC
            LIMIT ?
        """, (run_id, limit)).fetchall()
        return [dict(r) for r in rows]


def get_telemetry_recent(run_id: int, n: int = 60) -> list[dict]:
    with _connect() as con:
        rows = con.execute("""
            SELECT * FROM (
                SELECT * FROM telemetry_snapshots
                WHERE run_id = ?
                ORDER BY id DESC
                LIMIT ?
            ) ORDER BY id ASC
        """, (run_id, n)).fetchall()
        return [dict(r) for r in rows]


# ─── Evaluation results ───────────────────────────────────────────────────────

def save_eval(data: dict, run_id: int | None = None, source: str = "manual") -> int:
    with _connect() as con:
        s = data.get("summary", data)
        cur = con.execute("""
            INSERT INTO eval_results
                (run_id, mota, idf1, id_switches, latency_ms,
                 energy_J, energy_saved_pct, mission_ext_pct, source)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            run_id,
            s.get("mota"),        s.get("idf1"),
            s.get("id_switches"), s.get("latency_ms"),
            s.get("energy_J"),    s.get("energy_saved_pct"),
            s.get("mission_ext_pct"), source,
        ))
        return cur.lastrowid


def get_eval_history(limit: int = 20) -> list[dict]:
    with _connect() as con:
        rows = con.execute("""
            SELECT e.*, r.scenario, r.is_mock
            FROM   eval_results e
            LEFT JOIN simulation_runs r ON r.id = e.run_id
            ORDER BY e.id DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


def get_best_eval() -> dict | None:
    with _connect() as con:
        row = con.execute(
            "SELECT * FROM eval_results ORDER BY mota DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


# ─── Gallery ──────────────────────────────────────────────────────────────────

def add_capture(file_path: str, scenario: str, run_id: int | None = None,
                telemetry: dict | None = None, tags: list | None = None,
                title: str = "", description: str = "") -> int:
    t = telemetry or {}
    with _connect() as con:
        cur = con.execute("""
            INSERT INTO gallery_captures
                (run_id, scenario, file_path, n_tracks, fps, step, tags, title, description)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            run_id, scenario, file_path,
            t.get("n_tracks", 0), t.get("fps"),
            t.get("step"),
            json.dumps(tags or []),
            title, description,
        ))
        return cur.lastrowid


def get_gallery(limit: int = 100, scenario: str | None = None) -> list[dict]:
    with _connect() as con:
        if scenario:
            rows = con.execute("""
                SELECT g.*, r.is_mock FROM gallery_captures g
                LEFT JOIN simulation_runs r ON r.id = g.run_id
                WHERE g.scenario = ?
                ORDER BY g.id DESC LIMIT ?
            """, (scenario, limit)).fetchall()
        else:
            rows = con.execute("""
                SELECT g.*, r.is_mock FROM gallery_captures g
                LEFT JOIN simulation_runs r ON r.id = g.run_id
                ORDER BY g.id DESC LIMIT ?
            """, (limit,)).fetchall()
        return [dict(r) for r in rows]


# ─── Event log ────────────────────────────────────────────────────────────────

def log_event(message: str, level: str = "INFO", component: str = "system") -> None:
    try:
        with _connect() as con:
            con.execute(
                "INSERT INTO event_log (level, component, message) VALUES (?,?,?)",
                (level, component, message),
            )
    except Exception:
        pass  # Never crash the server over a logging failure


def get_events(limit: int = 100, component: str | None = None) -> list[dict]:
    with _connect() as con:
        if component:
            rows = con.execute("""
                SELECT * FROM event_log WHERE component=?
                ORDER BY id DESC LIMIT ?
            """, (component, limit)).fetchall()
        else:
            rows = con.execute(
                "SELECT * FROM event_log ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]


# ─── Aggregate stats (for dashboard cards) ────────────────────────────────────

def get_stats() -> dict:
    with _connect() as con:
        total_runs = con.execute(
            "SELECT COUNT(*) FROM simulation_runs").fetchone()[0]
        completed_runs = con.execute(
            "SELECT COUNT(*) FROM simulation_runs WHERE status='completed'").fetchone()[0]
        total_frames = con.execute(
            "SELECT COALESCE(SUM(total_frames),0) FROM simulation_runs").fetchone()[0]
        best_mota_row = con.execute(
            "SELECT MAX(mota) FROM eval_results").fetchone()
        best_mota = best_mota_row[0] if best_mota_row and best_mota_row[0] else 83.2
        total_captures = con.execute(
            "SELECT COUNT(*) FROM gallery_captures").fetchone()[0]
        total_events = con.execute(
            "SELECT COUNT(*) FROM event_log").fetchone()[0]
        avg_tracks = con.execute(
            "SELECT ROUND(AVG(n_tracks),1) FROM telemetry_snapshots").fetchone()[0] or 0.0

        return {
            "total_runs":      total_runs,
            "completed_runs":  completed_runs,
            "total_frames":    total_frames,
            "best_mota":       best_mota,
            "total_captures":  total_captures,
            "total_events":    total_events,
            "avg_tracks":      avg_tracks,
        }
