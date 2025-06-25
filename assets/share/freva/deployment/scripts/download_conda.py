#!/usr/bin/env python3
import argparse
import platform
import tarfile
import urllib.request as req
from pathlib import Path
from tempfile import NamedTemporaryFile


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


def _url_retrieve(conda_url: str, target: str) -> None:
    print("Retrieving conda install script: {}".format(conda_url))
    try:
        req.urlretrieve(
            str(conda_url),
            filename=target,
            reporthook=reporthook,
        )
    except Exception as error:
        print(error)


def _mamba_forge(dest_dir: Path) -> None:
    target = dest_dir / "conda.sh"
    _url_retrieve(
        "https://github.com/conda-forge/miniforge/releases/latest/"
        f"download/Miniforge3-{platform.system()}-{platform.machine()}.sh",
        str(target),
    )
    target.chmod(0o755)


def _micromamba(dest_dir: Path) -> None:
    system = platform.system().lower()
    plt = platform.machine()
    target = dest_dir / "bin" / "micromamba"
    if system != "linux":
        raise ValueError("Only Linux based deployment is supported.")
    if plt.startswith("x86"):
        plt = "64"
    with NamedTemporaryFile(suffix=".tar") as temp_f:
        _url_retrieve(
            f"https://micro.mamba.pm/api/micromamba/linux-{plt}/latest",
            temp_f.name,
        )
        with tarfile.open(temp_f.name, mode="r:bz2") as tar:
            member = tar.getmember("bin/micromamba")
            print("🔧 Extracting: bin/micromamba")
            tar.extract(member, path=str(dest_dir))
    target.chmod(0o755)


def download(mamba: str = "micromamba", dest_dir: Path = Path("/tmp")) -> None:
    """Download the conda forge install script."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    if "forge" in mamba:
        _mamba_forge(dest_dir)
    else:
        _micromamba(dest_dir)


def _cli() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "target_path", type=Path, help="Where to download the mamba exe."
    )
    parser.add_argument(
        "--type",
        "-t",
        type=str,
        default="micromamba",
        choices=("micromamba", "mambaforge"),
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = _cli()
    download(args.type, args.target_path)
