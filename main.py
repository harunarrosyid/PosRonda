"""
PosRonda Hub v4.4.8 - Main Launcher
Autonomous CCTV Multi-Camera Hub & Streaming Engine
Kompatibel penuh dengan pemanggilan 'python main.py' maupun 'python run.py'.
"""
import sys
import os

# Tambahkan src dan modul internal ke sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
POSRONDA_DIR = os.path.join(SRC_DIR, "posronda")
for p in [SRC_DIR, POSRONDA_DIR, os.path.join(POSRONDA_DIR, "core"), os.path.join(POSRONDA_DIR, "network"), os.path.join(POSRONDA_DIR, "ui"), os.path.join(POSRONDA_DIR, "utils")]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

from posronda.main import main

if __name__ == "__main__":
    main()
