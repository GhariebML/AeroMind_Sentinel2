"""
setup/download_airsim_env.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Downloads a pre-built AirSim environment binary from GitHub Releases.
Extracts to airsim_envs/<env_name>/ inside the project.

Available environments:
  blocks        Blocks.zip         ~280 MB  (simplest, recommended)
  airsimnh      AirSimNH.zip       ~760 MB  (small urban neighborhood)
  city          CityEnviron.zip    ~1.5 GB  (large city, needs good GPU)

Usage:
    python setup/download_airsim_env.py                       # downloads Blocks
    python setup/download_airsim_env.py --env airsimnh
    python setup/download_airsim_env.py --list                # show all options
"""
from __future__ import annotations

import argparse
import os
import sys
import zipfile
from pathlib import Path
from urllib.request import urlretrieve, urlopen
from urllib.error import URLError

ROOT    = Path(__file__).resolve().parent.parent
ENV_DIR = ROOT / "airsim_envs"

# GitHub release v1.8.1-windows — last stable AirSim release for Windows
BASE_URL = "https://github.com/microsoft/AirSim/releases/download/v1.8.1-windows"

ENVIRONMENTS = {
    "blocks": {
        "filename": "Blocks.zip",
        "url":      f"{BASE_URL}/Blocks.zip",
        "exe":      "Blocks/WindowsNoEditor/Blocks.exe",
        "size_mb":  280,
        "desc":     "Lightweight blocks scene (recommended for development)",
    },
    "airsimnh": {
        "filename": "AirSimNH.zip",
        "url":      f"{BASE_URL}/AirSimNH.zip",
        "exe":      "AirSimNH/WindowsNoEditor/AirSimNH.exe",
        "size_mb":  760,
        "desc":     "Small urban neighborhood — good for aerial tracking",
    },
    "city": {
        "filename": "CityEnviron.zip",
        "url":      f"{BASE_URL}/CityEnviron.zip",
        "exe":      "CityEnviron/WindowsNoEditor/CityEnviron.exe",
        "size_mb":  1500,
        "desc":     "Large city environment (needs GPU with 6+ GB VRAM)",
    },
}

os.system("")  # enable ANSI on Windows
G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; B = "\033[94m"; RST = "\033[0m"


def parse_args():
    p = argparse.ArgumentParser(description="AirSim environment downloader")
    p.add_argument("--env",  default="blocks", choices=list(ENVIRONMENTS),
                   help="Environment to download (default: blocks)")
    p.add_argument("--list", action="store_true", help="List available environments")
    p.add_argument("--force", action="store_true", help="Re-download even if exists")
    return p.parse_args()


def list_envs():
    print(f"\n  {B}Available AirSim Environments{RST}\n")
    for key, info in ENVIRONMENTS.items():
        print(f"    {G}{key:<12}{RST}  {info['desc']}")
        print(f"             Size: ~{info['size_mb']} MB")
        print(f"             URL:  {info['url']}\n")


def progress_hook(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        pct  = min(100, downloaded * 100 // total_size)
        done = pct // 2
        bar  = "=" * done + " " * (50 - done)
        mb   = downloaded / (1024*1024)
        total_mb = total_size / (1024*1024)
        print(f"\r  [{bar}] {pct:3d}%  {mb:.0f}/{total_mb:.0f} MB", end="", flush=True)


def download(env_key: str, force: bool) -> Path:
    info = ENVIRONMENTS[env_key]
    ENV_DIR.mkdir(parents=True, exist_ok=True)

    zip_path  = ENV_DIR / info["filename"]
    exe_path  = ENV_DIR / info["exe"]

    if exe_path.exists() and not force:
        print(f"  {G}[OK]{RST}  Already downloaded: {exe_path}")
        return exe_path

    # Download
    print(f"\n  {B}Downloading {info['filename']} (~{info['size_mb']} MB)…{RST}")
    print(f"  URL: {info['url']}\n")
    try:
        urlretrieve(info["url"], zip_path, reporthook=progress_hook)
        print()  # newline after progress bar
    except URLError as e:
        print(f"\n  {R}Download failed: {e}{RST}")
        print("  Check your internet connection or download manually:")
        print(f"  {info['url']}")
        sys.exit(1)

    # Extract
    print(f"\n  {B}Extracting {info['filename']}…{RST}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        total = len(zf.namelist())
        for i, member in enumerate(zf.namelist()):
            zf.extract(member, ENV_DIR)
            pct = (i+1)*100//total
            print(f"\r  Extracting… {pct}%", end="", flush=True)
    print()

    # Remove zip to save space
    zip_path.unlink()
    print(f"  {G}[OK]{RST}  Extracted -> {ENV_DIR / env_key.capitalize()}")

    return ENV_DIR / info["exe"]


def write_launcher(exe_path: Path) -> Path:
    """Write run_airsim.bat next to the executable."""
    bat = exe_path.parent / "run_airsim.bat"
    settings_dst = Path.home() / "Documents" / "AirSim" / "settings.json"
    bat.write_text(
        f"@echo off\n"
        f"echo Starting AirSim {exe_path.stem}...\n"
        f"echo Settings: {settings_dst}\n"
        f'start "" "{exe_path}" -windowed -ResX=1280 -ResY=720\n'
        f"echo AirSim started. Connect with: python scripts/check_airsim.py\n"
        f"pause\n",
        encoding="utf-8"
    )
    return bat


def main():
    args = parse_args()

    if args.list:
        list_envs()
        return

    print(f"\n{'='*60}")
    print(f"  AeroMind AI — AirSim Environment Downloader")
    print(f"{'='*60}")

    exe = download(args.env, args.force)
    bat = write_launcher(exe)

    print(f"\n  {G}Done!{RST}")
    print(f"  Executable : {exe}")
    print(f"  Launcher   : {bat}")
    print(f"\n  {Y}Next steps:{RST}")
    print(f"    1. Run launcher:  {bat}")
    print(f"    2. Wait for UE4 to start (first launch may take 60+ s)")
    print(f"    3. Run: python scripts/check_airsim.py")
    print(f"    4. Run: python scripts/run_simulation.py --scenario dense_urban")
    print()


if __name__ == "__main__":
    main()
