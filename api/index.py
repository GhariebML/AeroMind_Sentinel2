import os
import sys
from pathlib import Path

# Add the project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dashboard.app import app

# This is the entry point for Vercel
app = app
