import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def build():
    print("="*60)
    print("  Building AeroMind AI Professional Launcher")
    print("="*60)
    
    # 1. Clean previous build
    print("\n[1/4] Cleaning previous builds...")
    if (ROOT / "build").exists():
        shutil.rmtree(ROOT / "build", ignore_errors=True)
    
    # 2. Run PyInstaller for the Launcher
    print("\n[2/4] Running PyInstaller...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed", # Don't open console window for the launcher
        "--name", "AeroMind AI_Launcher",
        "--icon", "NONE", # Can be replaced with a real icon
        str(ROOT / "aic4_launcher.py")
    ]
    
    subprocess.run(cmd, cwd=str(ROOT))
    
    print("\n[3/4] Build Complete!")
    exe_path = ROOT / "dist" / "AeroMind AI_Launcher.exe"
    if exe_path.exists():
        print(f"  --> Successfully created: {exe_path}")
        print("\nNote: For distribution to machines without Python, ")
        print("you must package an embedded Python environment.")
    else:
        print("  --> Build failed!")

if __name__ == "__main__":
    build()
