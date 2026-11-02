# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_all

base_dir = os.path.dirname(os.path.abspath(SPEC))
src_dir = os.path.join(base_dir, "src")

datas = [('config.json', '.')]
binaries = []
hiddenimports = [
    'posronda',
    'posronda.main',
    'posronda.core',
    'posronda.core.config_manager',
    'posronda.core.license_manager',
    'posronda.core.stream_engine',
    'posronda.ui',
    'posronda.ui.settings_dialog',
    'posronda.network',
    'posronda.network.onvif_scanner',
    'posronda.network.youtube_manager',
    'posronda.network.notifier',
    'posronda.utils',
    'posronda.utils.check_env',
    'googleapiclient',
    'googleapiclient.discovery',
    'google_auth_oauthlib',
    'google_auth_oauthlib.flow',
    'google.auth.transport.requests',
    'PIL',
    'PIL.ImageTk',
    'cv2',
    'numpy',
    'requests',
    'urllib3'
]

# Kumpulkan modul dependensi penting
for pkg in ['googleapiclient', 'google_auth_oauthlib', 'cv2', 'PIL']:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

a = Analysis(
    ['run.py'],
    pathex=[src_dir, base_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'pandas', 'IPython', 'notebook'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PosRonda',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # False = Windowed GUI (Bebas jendela hitam CMD)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
