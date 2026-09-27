# -*- mode: python ; coding: utf-8 -*-
"""Ejecutable único, sin consola. No altera el motor científico."""

import os

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

spec_dir = os.path.dirname(os.path.abspath(SPEC))
root = os.path.dirname(spec_dir)

a = Analysis(
    [os.path.join(spec_dir, "present_entry.py")],
    pathex=[os.path.join(root, "src")],
    binaries=[],
    datas=collect_data_files("matplotlib"),
    hiddenimports=collect_submodules("go_mb")
    + [
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
        "matplotlib.backends.backend_tkagg",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "IPython", "notebook"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Simulacion_GO_AC",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
