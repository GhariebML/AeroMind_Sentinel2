"""
dashboard/app.py — AeroMind Sentinel Dashboard Server
=====================================================

Application factory that registers all route Blueprints.
Run:  python dashboard/app.py
Then: open http://localhost:5000
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from flask import Flask, send_file, send_from_directory

# ─── Path Setup ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

IS_VERCEL = any(os.environ.get(k) for k in ["VERCEL", "VERCEL_ENV", "VERCEL_URL", "AWS_LAMBDA_FUNCTION_NAME"])

# ─── Database ────────────────────────────────────────────────────────────────
import dashboard.database as db

DB_PATH = Path("/tmp/aeromind.db") if IS_VERCEL else ROOT / "experiments" / "results" / "aeromind.db"
db.init(DB_PATH)
db.log_event("Dashboard server initialized", component="server")


# ─── Application Factory ────────────────────────────────────────────────────

def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder=str(ROOT / "dashboard" / "static"))
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    # ── Static / download routes ─────────────────────────────────────────
    @app.route('/experiments/results/<path:filename>')
    def serve_results(filename):
        return send_file(str(ROOT / "experiments" / "results" / filename))

    @app.route('/download/<path:filename>')
    def download_file(filename):
        return send_from_directory(ROOT / "docs", filename, as_attachment=True)

    # ── Register Blueprints ──────────────────────────────────────────────
    from dashboard.routes.pages import pages_bp
    from dashboard.routes.api_core import api_core_bp
    from dashboard.routes.api_highway import api_highway_bp
    from dashboard.routes.api_sim import api_sim_bp
    from dashboard.routes.api_db import api_db_bp
    from dashboard.routes.api_stream import api_stream_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(api_core_bp)
    app.register_blueprint(api_highway_bp)
    app.register_blueprint(api_sim_bp)
    app.register_blueprint(api_db_bp)
    app.register_blueprint(api_stream_bp)

    return app


# ─── Entry Point ─────────────────────────────────────────────────────────────

app = create_app()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  AeroMind Sentinel — Project Dashboard")
    print("  http://localhost:5000")
    print(f"  Database: {DB_PATH}")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
