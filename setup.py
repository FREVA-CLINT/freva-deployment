#!/usr/bin/env python3
"""Setup script for packaging freva deployment."""

from pathlib import Path
from setuptools import setup, find_packages

THIS_DIR = Path(__file__).parent
CONFIG_DIR = Path("freva") / "deployment"
ASSET_DIR = THIS_DIR / "assets"


def prepare_config() -> None:
    """Create the freva config dir in loacal user directory."""
    import appdirs

    paths = {}
    for attr in ("user_config_dir", "user_data_dir"):
        usr_path = Path(getattr(appdirs, attr)()) / CONFIG_DIR
        usr_path.mkdir(exist_ok=True, parents=True)
        paths[attr] = usr_path
    inventory_file = paths["user_config_dir"] / "inventory.toml"
    with (ASSET_DIR / "config" / "inventory.toml").open() as f:
        if not inventory_file.exists():
            with (paths["user_config_dir"] / "inventory.toml").open("w") as w:
                w.write(f.read())
    for datafile in ASSET_DIR.rglob("*"):
        new_path = paths["user_data_dir"] / datafile.relative_to(ASSET_DIR)
        if datafile.is_dir():
            continue
        new_path.parent.mkdir(exist_ok=True, parents=True)
        with datafile.open() as f:
            with new_path.open("w") as w:
                w.write(f.read())


def read(*parts: str) -> str:
    """Read the content of a file."""
    with THIS_DIR.joinpath(*parts).open() as f:
        return f.read()


setup(
    name="freva_deployment",
    version="2022.02",
    author="Martin Bergemann",
    author_email="martin.bergemann@dkrz.de",
    maintainer="Martin Bergemann",
    url="https://gitlab.dkrz.de/freva/deployment.git",
    description="Deploy freva and its services on different machines.",
    long_description=read("README.md"),
    license="GPLv3",
    packages=find_packages("src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "deploy-freva = freva_deployment.cli:cli",
            "deploy-freva-tui = freva_deployment.ui.deployment_tui:tui",
        ]
    },
    install_requires=[
        "appdirs",
        "npyscreen",
        "pyyml",
        "rich",
        "toml",
        "tomlkit",
    ],
    extras_require={
        'docs': [
              'sphinx',
              'nbsphinx',
              'recommonmark',
              'sphinx_rtd_theme',
              'ipython',  # For nbsphinx syntax highlighting
              'sphinxcontrib_github_alt',
              ],
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
prepare_config()
