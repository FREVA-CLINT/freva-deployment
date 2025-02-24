#!/usr/bin/env python3

import os
import platform
import stat
import sys
import urllib.request as req
from pathlib import Path


def reporthook(count: float, block_size: float, total_size: float) -> None:
    """Print the download status."""
    if count == 0:
        return
    frac = count * block_size / total_size
    percent = int(100 * frac)
    bars = "#" * int(frac * 40)
    msg = "Downloading: [{0:<{1}}] | {2}% Completed".format(
        bars, 40, round(percent, 2)
    )
    print(msg, end="\r", flush=True)
    if frac >= 1:
        print()


def download():
    """Download the conda forge install script."""
    try:
        dest_dir = Path(sys.argv[1])
    except IndexError:
        dest_dir = Path("/tmp")
    prefix = (
        "https://github.com/conda-forge/miniforge/releases/latest/"
        "download/Miniforge3"
    )
    conda_url = "{}-{}-{}.sh".format(
        prefix, platform.system(), platform.machine()
    )
    target = dest_dir / "conda.sh"
    print("Retrieving conda install script: {}".format(conda_url))
    try:
        req.urlretrieve(
            str(conda_url),
            filename=target,
            reporthook=reporthook,
        )
    except Exception as error:
        print(error)
    target.chmod(0o755)


if __name__ == "__main__":

    download()
