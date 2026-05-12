import os
import glob

replacements = [
    ("AIC-4 Drone Tracking System", "AeroMind Autonomous Drone OS"),
    ("AIC-4 Drone Tracking Dashboard", "AeroMind AI Surveillance Platform"),
    ("AIC-4 Drone Tracking", "AeroMind AI Surveillance Platform"),
    ("AIC-4 Aerial Tracking", "AeroMind AI"),
    ("AIC-4 Live Demo", "AeroMind AI Live Demo"),
    ("AIC-4 Simulation", "AeroMind AI Simulation"),
    ("AIC-4", "AeroMind AI"),
    ("AIC4", "AeroMind AI"),
    ("Mohamed Gharieb © Military Technical College", "AeroMind Technologies | The Brain of Next-Gen Drones"),
    ("Mohamed Gharieb", "AeroMind Technologies"),
]

paths = ['scripts/**/*.py', 'dashboard/**/*.html', 'dashboard/**/*.py', 'docs/**/*.md', 'src/**/*.py', 'README.md', 'README_AIRSIM.md', 'tests/**/*.py', 'setup/**/*.py', '*.bat', 'Makefile']

files_to_check = []
for p in paths:
    files_to_check.extend(glob.glob(p, recursive=True))

for f in files_to_check:
    if not os.path.isfile(f): continue
    
    with open(f, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read()
        
    new_content = content
    for old, new in replacements:
        new_content = new_content.replace(old, new)
        
    if new_content != content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f"Updated {f}")
