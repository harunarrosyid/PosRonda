"""
PosRonda v4.0 - Main Launcher
Autonomous CCTV Multi-Camera Hub & Streaming Engine
"""
import sys
import os

# Tambahkan src ke path utama aplikasi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from posronda.main import main

if __name__ == "__main__":
    main()
