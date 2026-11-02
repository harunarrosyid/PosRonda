"""
setup_cython.py - Kompilasi modul inti PosRonda menjadi C Extension (.pyd / .so)
"""
import sys
import os
from setuptools import setup, find_packages
from setuptools.extension import Extension

try:
    from Cython.Build import cythonize
except ImportError:
    print("[ERROR] Cython belum terpasang. Jalankan: pip install cython setuptools")
    sys.exit(1)

src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

extensions = [
    Extension(
        "posronda.core.license_manager",
        ["src/posronda/core/license_manager.py"],
    ),
    Extension(
        "posronda.core.stream_engine",
        ["src/posronda/core/stream_engine.py"],
    ),
]

setup(
    name="posronda-core",
    version="4.4.2",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            'language_level': "3",
            'always_allow_keywords': True,
        }
    ),
)
