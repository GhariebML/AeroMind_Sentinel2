"""
setup/setup_environment.py
━━━━━━━━━━━━━━━━━━━━━━━━━━
AeroMind AI DroneTracking — One-command environment setup.

Installs all Python dependencies, deploys AirSim settings.json,
and prints a colour-coded status report.

Usage:
    python setup/setup_environment.py
    python setup/setup_environment.py --skip-install   # check only
"""
from __future__ import annotations

import argparse
import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ── Ensure vendor/ is on path so airsim + msgpackrpc shim are available ───────
_VENDOR = ROOT / "vendor"
if str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

# ─── ANSI colours (work on Windows 10+ with ENABLE_VIRTUAL_TERMINAL_PROCESSING)
os.system("")   # enable ANSI on Windows
G  = "\033[92m"   # green
R  = "\033[91m"   # red
Y  = "\033[93m"   # yellow
B  = "\033[94m"   # blue
W  = "\033[97m"   # white bold
DIM = "\033[2m"
RST = "\033[0m"

def ok(msg):  print(f"  {G}[OK]{RST}  {msg}")
def err(msg): print(f"  {R}[!!]{RST}  {msg}")
def warn(msg):print(f"  {Y}[WW]{RST}  {msg}")
def info(msg):print(f"  {B}[..]{RST}  {msg}")
def hdr(msg): print(f"\n{W}{msg}{RST}")


# ─── Package install groups --------------------------------------------------─

CORE_PACKAGES = [
    # (pip_name,        import_name,   description)
    ("numpy>=1.24",     "numpy",       "NumPy"),
    ("scipy>=1.10",     "scipy",       "SciPy"),
    ("opencv-python",   "cv2",         "OpenCV"),
    ("Pillow",          "PIL",         "Pillow"),
    ("pyyaml",          "yaml",        "PyYAML"),
    ("loguru",          "loguru",      "Loguru"),
    ("rich",            "rich",        "Rich"),
    ("tqdm",            "tqdm",        "TQDM"),
]

DL_PACKAGES = [
    ("torch>=2.0",            "torch",          "PyTorch"),
    ("torchvision>=0.15",     "torchvision",    "TorchVision"),
    ("ultralytics>=8.0",      "ultralytics",    "YOLOv8/Ultralytics"),
    ("stable-baselines3>=2.1","stable_baselines3","Stable-Baselines3"),
    ("gymnasium>=0.29",       "gymnasium",      "Gymnasium"),
    ("filterpy>=1.4",         "filterpy",       "FilterPy (Kalman)"),
    ("scipy>=1.10",           "scipy",          "SciPy (Hungarian)"),
]

AIRSIM_PACKAGES = [
    ("msgpack-rpc-python",    "msgpackrpc",     "msgpack-rpc (AirSim RPC)"),
    ("sahi>=0.11",            "sahi",           "SAHI (sliced inference)"),
]

EVAL_PACKAGES = [
    ("motmetrics>=1.4",       "motmetrics",     "MOT Metrics (MOTA/IDF1)"),
    ("pandas>=2.0",           "pandas",         "Pandas"),
    ("matplotlib>=3.7",       "matplotlib",     "Matplotlib"),
]

FLASK_PACKAGES = [
    ("flask>=3.0",            "flask",          "Flask"),
]


def is_installed(import_name: str) -> bool:
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False


def install_package(pip_name: str) -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", pip_name, "--quiet"],
        capture_output=True, text=True
    )
    return result.returncode == 0


def install_group(group: list[tuple], group_name: str, do_install: bool) -> dict:
    hdr(f"  {group_name}")
    status = {}
    for pip_name, import_name, desc in group:
        if is_installed(import_name):
            ok(f"{desc:<36} already installed")
            status[import_name] = True
        elif do_install:
            info(f"Installing {desc} ...")
            success = install_package(pip_name)
            if success and is_installed(import_name):
                ok(f"{desc:<36} installed OK")
                status[import_name] = True
            else:
                err(f"{desc:<36} FAILED  →  pip install {pip_name}")
                status[import_name] = False
        else:
            err(f"{desc:<36} NOT installed  →  pip install {pip_name}")
            status[import_name] = False
    return status


def install_airsim_client(do_install: bool) -> bool:
    """Install AirSim Python client from GitHub PythonClient source."""
    hdr("  AirSim Python Client")
    if is_installed("airsim"):
        ok(f"{'airsim':<36} already installed")
        return True

    if not do_install:
        err(f"{'airsim':<36} NOT installed")
        info("Run: python setup/setup_environment.py  (without --skip-install)")
        return False

    # Try PyPI first (may fail on newer Python)
    info("Trying PyPI airsim 1.8.1 ...")
    r = subprocess.run(
        [sys.executable, "-m", "pip", "install", "airsim", "--quiet"],
        capture_output=True, text=True
    )
    if r.returncode == 0 and is_installed("airsim"):
        ok(f"{'airsim':<36} installed from PyPI ✓")
        return True

    warn("PyPI install failed — installing from GitHub source ...")
    info("Cloning microsoft/AirSim PythonClient (this may take ~2 min) ...")
    r2 = subprocess.run(
        [sys.executable, "-m", "pip", "install",
         "airsim @ git+https://github.com/microsoft/AirSim.git#subdirectory=PythonClient",
         "--quiet"],
        capture_output=True, text=True, timeout=300
    )
    if r2.returncode == 0 and is_installed("airsim"):
        ok(f"{'airsim':<36} installed from GitHub ✓")
        return True

    err("AirSim install failed via both PyPI and GitHub.")
    info("Manual install:")
    info("  git clone https://github.com/microsoft/AirSim.git")
    info("  cd AirSim/PythonClient && pip install -e .")
    return False


def deploy_settings() -> bool:
    """Copy configs/airsim_settings.json → Documents/AirSim/settings.json"""
    hdr("  AirSim Settings Deployment")
    src = ROOT / "configs" / "airsim_settings.json"
    dst_dir = Path.home() / "Documents" / "AirSim"
    dst = dst_dir / "settings.json"

    if not src.exists():
        err(f"Source not found: {src}")
        return False

    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    ok(f"settings.json → {dst}")
    return True


def check_airsim_env() -> bool:
    """Check if AirSim Blocks binary is present."""
    hdr("  AirSim Environment Binary")
    env_dir = ROOT / "airsim_envs"
    blocks  = env_dir / "Blocks" / "Blocks.exe"
    nh      = env_dir / "AirSimNH" / "AirSimNH.exe"
    if blocks.exists():
        ok(f"Blocks.exe found → {blocks}")
        return True
    if nh.exists():
        ok(f"AirSimNH.exe found → {nh}")
        return True
    warn("No AirSim environment binary found.")
    info(f"Download one:  python setup/download_airsim_env.py")
    info(f"  or manually: https://github.com/microsoft/AirSim/releases/tag/v1.8.1")
    return False


def verify_project_files() -> bool:
    hdr("  Project Files")
    required = [
        ("src/simulation/airsim_env.py",    "AirSim Gymnasium environment"),
        ("src/detection/detector.py",        "YOLOv8 detector"),
        ("src/tracking/tracker.py",          "BoT-SORT tracker"),
        ("src/navigation/rl_controller.py",  "PPO navigation agent"),
        ("scripts/run_simulation.py",        "Simulation runner"),
        ("scripts/check_airsim.py",          "AirSim diagnostic"),
        ("dashboard/app.py",                 "Flask dashboard"),
        ("configs/config.yaml",              "Master config"),
        ("configs/airsim_settings.json",     "AirSim settings"),
        ("yolov8m.pt",                       "YOLOv8m pretrained weights"),
    ]
    all_ok = True
    for rel, desc in required:
        p = ROOT / rel
        if p.exists():
            size = p.stat().st_size
            ok(f"{desc:<38} {DIM}({size/1024:.0f} KB){RST}")
        else:
            err(f"{desc:<38} MISSING: {rel}")
            all_ok = False
    return all_ok


def print_summary(results: dict) -> None:
    hdr("=" * 60)
    print(f"\n  AeroMind AI Environment Setup — Summary")
    print(f"  {'─'*50}")

    all_pass = all(results.values())
    for name, passed in results.items():
        icon = f"{G}[OK]{RST}" if passed else f"{R}[!!]{RST}"
        print(f"    {icon}  {name}")

    print()
    if all_pass:
        print(f"  {G}All checks passed!{RST} Ready to run.\n")
        print(f"  {W}Quick start:{RST}")
        print(f"    1.  {Y}launch_airsim.bat{RST}        — start AirSim Blocks binary")
        print(f"    2.  {Y}launch_dashboard.bat{RST}     — start Flask dashboard")
        print(f"    3.  Open http://localhost:5000/demo → click ▶ Start Simulation")
        print()
        print(f"  {W}Or, mock mode (no AirSim needed):{RST}")
        print(f"    python scripts/run_simulation.py --mock --record")
    else:
        print(f"  {Y}Some checks failed.{RST} See above for details.\n")
        print(f"  Re-run:  python setup/setup_environment.py")
    print()


def main():
    p = argparse.ArgumentParser(description="AeroMind AI Environment Setup")
    p.add_argument("--skip-install", action="store_true",
                   help="Check status only, don't install anything")
    args = p.parse_args()
    do_install = not args.skip_install

    print(f"\n{'='*60}")
    print(f"  AeroMind AI DroneTracking — Environment Setup")
    print(f"  Python {sys.version.split()[0]}  |  {'Check only' if not do_install else 'Install mode'}")
    print(f"{'='*60}")

    results = {}

    # Core
    s = install_group(CORE_PACKAGES,    "Core (NumPy, OpenCV, YAML …)",  do_install)
    results["Core packages"]       = all(s.values())

    # Deep learning
    s = install_group(DL_PACKAGES,      "Deep Learning (Torch, YOLO, SB3 …)", do_install)
    results["DL packages"]         = all(s.values())

    # AirSim
    results["AirSim Python client"] = install_airsim_client(do_install)

    # AirSim extras
    s = install_group(AIRSIM_PACKAGES,  "AirSim extras (msgpack-rpc, sahi)", do_install)
    results["AirSim extras"]       = all(s.values())

    # Evaluation
    s = install_group(EVAL_PACKAGES,    "Evaluation (MOT metrics, plotting)", do_install)
    results["Evaluation packages"] = all(s.values())

    # Flask
    s = install_group(FLASK_PACKAGES,   "Dashboard (Flask)",               do_install)
    results["Flask dashboard"]     = all(s.values())

    # Settings
    results["AirSim settings.json"]  = deploy_settings()

    # Binaries
    results["AirSim binary (opt.)"]  = check_airsim_env()

    # Project files
    results["Project source files"]  = verify_project_files()

    print_summary(results)


if __name__ == "__main__":
    main()
