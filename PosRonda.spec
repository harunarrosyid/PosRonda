# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

datas = [('config.json', '.')]
binaries = []
hiddenimports = [
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
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'pandas'],
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
