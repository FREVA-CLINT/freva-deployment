# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all
from tempfile import NamedTemporaryFile
from pathlib import Path
import re
import sys
import shutil


def run_build(command, script, binaries=None, datas=None, hiddenimports=None):
    a = Analysis(
        [script],
        pathex=[],
        binaries=binaries or [],
        datas=datas or [],
        hiddenimports=hiddenimports or [],
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        excludes=["pycrypto", "cowsay"],
        noarchive=False,
        #optimize=0,
    )
    pyz = PYZ(a.pure)

    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name=command,
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


def build_freva_deploy():
    bins = []
    for bin in ("mysqldump",):
        exe = shutil.which(bin)
        if exe:
            bins.append((exe, "bin"))

    if sys.platform.lower().startswith("win"):
        cowsay = ("pyinstaller/cowsay.exe", "bin")
        hiddenimports = [
            "cryptography",
            "ansible_pylibssh",
            "windows-curses",
            "pwd",
            "fcntl",
        ]
    else:
        cowsay = ("pyinstaller/cowsay", "bin")
        hiddenimports = ["cryptography", "ansible_pylibssh"]

    datas = [
        ("assets/share/freva/deployment", "freva_deployment/assets"),
        ("src/freva_deployment/versions.json", "freva_deployment"),
        (
            "src/freva_deployment/callback_plugins",
            "freva_deployment/callback_plugins",
        ),
    ]
    binaries = bins + [cowsay]
    tmp_ret = collect_all("ansible")
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
    tmp_ret = collect_all("ansible_collections")
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
    run_build(
        "deploy-freva",
        os.path.join("pyinstaller", "pyinstaller-deploy-freva.py"),
        binaries,
        datas,
        hiddenimports,
    )


def build_metadata_crawler(
    git_url="gitlab.dkrz.de/freva/metadata-crawler-source.git",
):
    token = os.getenv("METADATA_CRAWLER_TOKEN", "")
    user = os.getenv("GITLABUSER", "")
    if token and user:
        url = f"git+https://{user}:{token}@{git_url}"
    else:
        url = f"git+https://{git_url}"
    from pip._internal.cli.main import main as install

    install(["install", url])
    with NamedTemporaryFile(suffix=".spec") as temp_f:
        with open(temp_f.name, "w", encoding="utf-8") as stream:
            stream.write("from metadata_crawler.cli import cli\n\n")
            stream.write('if __name__ == "__main__":\n   cli()')
        run_build("data-crawler", temp_f.name)


build_freva_deploy()
if not sys.platform.lower().startswith("win"):
    build_metadata_crawler()
