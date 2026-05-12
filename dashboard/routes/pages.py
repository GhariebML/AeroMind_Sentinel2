"""
dashboard/routes/pages.py — HTML page routes.
"""

from flask import Blueprint, send_file, redirect
from pathlib import Path

pages_bp = Blueprint("pages", __name__)

_DASHBOARD_DIR = Path(__file__).resolve().parent.parent
_ROOT = _DASHBOARD_DIR.parent


def _send_html(name: str):
    path = _DASHBOARD_DIR / name
    if not path.exists():
        return f"<h1>404 — {name} not found</h1>", 404
    return send_file(str(path), mimetype="text/html")


@pages_bp.route("/")
def index():
    return _send_html("index.html")


@pages_bp.route("/swarm")
def swarm_dashboard():
    return _send_html("swarm.html")


@pages_bp.route("/tactical")
def tactical_dashboard():
    return send_file(_ROOT / "docs" / "aeromind_dashboard.html")


@pages_bp.route("/report")
def report_page():
    return _send_html("report.html")


@pages_bp.route("/gallery")
def gallery_page():
    return _send_html("gallery.html")


@pages_bp.route("/training")
def training_page():
    return _send_html("training.html")


@pages_bp.route("/plan")
def plan_page():
    return _send_html("plan.html")


@pages_bp.route("/demo")
def demo_page():
    return redirect("/#demo")
