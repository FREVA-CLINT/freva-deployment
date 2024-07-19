# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all
from pathlib import Path
import re
import sys
import sys
import locale

import mock

if sys.platform.lower().startswith("win"):
    cowsay = ("pyinstaller/cowsay.exe", "bin")
    hiddenimports = ["cryptography", "ansible_pylibssh", "windows-curses"]
else:
    cowsay = ("pyinstaller/cowsay", "bin")
    hiddenimports = ["cryptography", "ansible_pylibssh"]

datas = [
    ("assets/share/freva/deployment", "freva_deployment/assets"),
    ("src/freva_deployment/versions.json", "freva_deployment"),
    ("src/freva_deployment/callback_plugins", "freva_deployment/callback_plugins"),
    cowsay,
]
binaries = []
tmp_ret = collect_all("ansible")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]
tmp_ret = collect_all("ansible_collections")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

a = Analysis(
    ["pyinstaller/pyinstaller-deploy-freva.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pycrypto", "PyInstaller", "cowsay"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="deploy-freva",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["docs/_static/freva_owl.ico"],
)
