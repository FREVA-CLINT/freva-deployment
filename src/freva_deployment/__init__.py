from urllib.request import urlretrieve

__version__ = "2309.0.1"
FREVA_PYTHON_VERSION = "3.11"
AVAILABLE_PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12"]
AVAILABLE_CONDA_ARCHS = [
    "Linux-x86_64",
    "Linux-aarch64",
    "Linux-ppc64le",
    "Linux-s390x",
    "MacOSX-x86_64",
]


def download_auxiliry_data():
    """Download any data that needs to be downloaded."""

    def reporthook(count, block_size, total_size):
        if count == 0:
            return
        frac = count * block_size / total_size
        percent = int(100 * frac)
        bar = "#" * int(frac * 40)
        msg = "Downloading: [{0:<{1}}] | {2}% Completed".format(
            bar, 40, round(percent, 2)
        )
        print(msg, end="\r", flush=True)
        if frac >= 1:
            print()

    urls = {
        "https://raw.githubusercontent.com/FREVA-CLINT/"
        "freva/main/assets/evaluation_system.conf": (
            "assets/share/freva/deployment/config/evaluation_system.conf.tmpl"
        )
    }

    for source, target in urls.items():
        urlretrieve(source, filename=target, reporthook=reporthook)


if __name__ == "__main__":
    download_auxiliry_data()
