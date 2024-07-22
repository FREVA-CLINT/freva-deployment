"""Download and extract cowsay binary from an archive."""

import argparse
import os
import tarfile
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlretrieve


def reporthook(count, block_size, total_size):
    if count == 0:
        return
    frac = count * block_size / total_size
    percent = int(100 * frac)
    bar = "#" * int(frac * 40)
    msg = "Downloading: [{0:<{1}}] | {2}% Completed".format(bar, 40, round(percent, 2))
    print(msg, end="\r", flush=True)
    if frac >= 1:
        print()


class CowsayExtractor:
    def __init__(self, url: str):
        self.url = url
        self.script_dir = Path(__file__).parent
        self.temp_file = None

    def __enter__(self):
        """Create a temporary file and prepare for extraction."""
        self.temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(self.url).suffix
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close and delete the temporary file."""
        if self.temp_file:
            self.temp_file.close()

    def download_file(self) -> Path:
        """Download the archive from the specified URL.

        Returns
        -------
        Path
            The path to the downloaded archive.
        """
        urlretrieve(self.url, filename=self.temp_file.name, reporthook=reporthook)
        return Path(self.temp_file.name)

    def extract_cowsay(self, archive_path: Path) -> Path:
        """Extract the cowsay binary from a ZIP or TAR.GZ archive.

        Parameters
        ----------
        archive_path : Path
            The path to the archive file from which to extract the binary.

        Returns
        -------
        Path: Path to extracted executable.
        """
        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as archive:
                for member in archive.namelist():
                    if member in ["cowsay", "cowsay.exe"]:
                        archive.extract(member, path=self.script_dir)
                        extracted_path = self.script_dir / member
                        break
        elif archive_path.suffix == ".gz":
            with tarfile.open(archive_path, "r:gz") as archive:
                for member in archive.getmembers():
                    if member.name in ["cowsay", "cowsay.exe"]:
                        archive.extract(member, path=self.script_dir)
                        extracted_path = self.script_dir / member.name
                        break
        else:
            raise ValueError("Unsupported archive format. Must be .zip or .tar.gz.")
        if extracted_path.suffix != ".exe" and os.name != "nt":
            try:
                os.chmod(extracted_path, 0o755)
            except OSError:
                print(f"Failed to set executable bit on {extracted_path}")

    def run(self) -> None:
        """Main function to download and extract the cowsay binary."""
        archive_path = self.download_file()
        self.extract_cowsay(archive_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download and extract cowsay binary from an archive."
    )
    parser.add_argument(
        "url",
        type=str,
        help="URL of the ZIP or TAR.GZ file containing cowsay.",
    )
    args = parser.parse_args()

    with CowsayExtractor(args.url) as extractor:
        extractor.run()
