#!/usr/bin/env python3
"""Setup script for packaging freva deployment."""

from pathlib import Path
import re
import urllib.request
from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install
import sys
from typing import List, Tuple


THIS_DIR = Path(__file__).parent
CONFIG_DIR = Path("freva") / "deployment"
ASSET_DIR = THIS_DIR / "assets"


INSTALL_REQUIRES = [
    "appdirs",
    "npyscreen",
    "numpy",
    "PyMySQL",
    "PyYAML",
    "rich",
    "toml",
    "tomlkit",
    "requests",
]


def find_version(*parts):
    vers_file = read(*parts)
    match = re.search(r'^__version__ = "(\d+.\d+.\d+)"', vers_file, re.M)
    if match is not None:
        return match.group(1)
    raise RuntimeError("Unable to find version string.")


def download_assets() -> None:
    """Download additional assets."""
    assets = [
        (
            ASSET_DIR / "config" / "evaluation_system.conf.tmpl",
            "https://raw.githubusercontent.com/FREVA-CLINT/freva/main/assets/evaluation_system.conf",
        )
    ]
    for path, url in assets:
        urllib.request.urlretrieve(url, filename=str(path))


def prepare_config(develop_cmd: bool = False) -> None:
    """Create the freva config dir in loacal user directory."""
    import appdirs

    download_assets()
    user_config_dir = Path(appdirs.user_config_dir()) / CONFIG_DIR
    user_data_dir = Path(appdirs.user_data_dir()) / CONFIG_DIR
    for cfg_path in (user_config_dir, user_data_dir):
        cfg_path.mkdir(exist_ok=True, parents=True)
    inventory_file = user_config_dir / "inventory.toml"
    inventory_asset = ASSET_DIR / "config" / "inventory.toml"
    with inventory_asset.open() as f:
        if inventory_file.is_symlink():
            inventory_file.unlink()
        if not inventory_file.exists() and develop_cmd is False:
            with inventory_file.open("w") as w:
                w.write(f.read())
        elif develop_cmd is True:
            inventory_file.unlink(missing_ok=True)
            inventory_file.symlink_to(inventory_asset)
    for datafile in ASSET_DIR.rglob("*"):
        new_path = user_data_dir / datafile.relative_to(ASSET_DIR)
        if datafile.is_dir():
            continue
        new_path.parent.mkdir(exist_ok=True, parents=True)
        with datafile.open() as f:
            new_path.unlink(missing_ok=True)
            if develop_cmd is False:
                with new_path.open("w") as w:
                    w.write(f.read())
            else:
                new_path.symlink_to(datafile)


class InstallCommand(install):
    """Customized setuptools install command."""

    def run(self):
        install.run(self)
        prepare_config(develop_cmd=False)


class DevelopCommand(develop):
    """Customized setuptools install command."""

    def run(self):
        develop.run(self)
        prepare_config(develop_cmd=True)


def read(*parts: str) -> str:
    """Read the content of a file."""
    with THIS_DIR.joinpath(*parts).open() as f:
        return f.read()


def get_packages() -> List[str]:
    """Get the packages needed to install."""
    plf = sys.platform
    if plf.startswith("win") or plf.startswith("cygwin") or plf.startswith("ms"):
        return INSTALL_REQUIRES
    INSTALL_REQUIRES.append("ansible")
    return INSTALL_REQUIRES


def get_data_files() -> List[Tuple[str, List[str]]]:
    dirs = [d for d in ASSET_DIR.rglob("*") if d.is_dir()]
    data_files = []
    for d in dirs:
        target_dir = Path("share") / "freva" / "deployment" / d.relative_to(ASSET_DIR)
        add_files = [str(f.relative_to(THIS_DIR)) for f in d.rglob("*") if f.is_file()]
        if add_files:
            data_files.append((str(target_dir), add_files))
    return data_files


setup(
    name="freva_deployment",
    version=find_version("src", "freva_deployment", "__init__.py"),
    author="Martin Bergemann",
    author_email="martin.bergemann@dkrz.de",
    maintainer="Martin Bergemann",
    url="https://github.com/FREVA-CLINT/freva.git",
    description="Deploy freva and its services on different machines.",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    include_package_data=True,
    data_files=get_data_files(),
    license="GPLv3",
    project_urls={
        "Documentation": "https://freva-deployment.readthedocs.io/en/latest/",
        "Issues": "https://github.com/FREVA-CLINT/freva/issues",
        "Source": "https://github.com/FREVA-CLINT/freva",
    },
    packages=find_packages("src"),
    package_dir={"": "src"},
    cmdclass={
        "develop": DevelopCommand,
        "install": InstallCommand,
    },
    entry_points={
        "console_scripts": [
            "deploy-freva-cmd = freva_deployment.cli:deploy",
            "deploy-freva-map = freva_deployment.cli:server_map",
            "freva-service = freva_deployment.cli:service",
            "freva-migrate = freva_deployment.cli:migrate",
            "deploy-freva = freva_deployment.ui.deployment_tui:tui",
        ]
    },
    setup_requires=["appdirs"],
    install_requires=get_packages(),
    extras_require={
        "docs": [
            "furo",
            "sphinx",
            "nbsphinx",
            "recommonmark",
            "sphinx_rtd_theme",
            "ipython",  # For nbsphinx syntax highlighting
            "sphinxcontrib_github_alt",
        ],
        "test": ["mypy", "black", "types-toml", "types-PyMySQL"],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
    ],
)
