import os
import re
import locale
import sys

import mock
from rich import print as pprint


def main():
    """Run the main tui."""
    from freva_deployment.cli import main_cli

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")
    for exe in ("cowsay", "cowsay.exe"):
        cow_exe = os.path.join(path, exe)
        if os.path.isfile(cow_exe):
            os.environ["ANSIBLE_COW_PATH"] = os.path.join(exe)
            break
    os.environ["PATH"] = path + os.pathsep + os.environ["PATH"]
    main_cli()


if __name__ == "__main__":
    sys.argv[0] = re.sub(r"(-script\.pyw|\.exe)?$", "", sys.argv[0])
    try:
        locale.setlocale(locale.LC_ALL, "")
        dummy, encoding = locale.getlocale()
    except (locale.Error, ValueError):
        encoding = "unknown"
    if (encoding or "unknown").lower() not in ("utf-8", "utf8"):
        pprint(
            f"[red][b]WARNING[/b] - Your locale encoding is {encoding} "
            "Ansible might not work correctly. Consider changing your "
            "locale encoding (LC_ALL) to UTF-8[/red]"
        )
    with mock.patch("locale.getlocale", lambda: ("utf-8", "utf-8")):
        with mock.patch("sys.getfilesystemencoding", lambda: "utf-8"):
            main()
