import locale
import os
import re
import sys

from rich import print as pprint


def main():
    """Run the main tui."""
    from freva_deployment.cli import main_cli

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")
    for exe in ("cowsay", "cowsay.exe"):
        cow_exe = os.path.join(path, exe)
        if os.path.isfile(cow_exe):
            os.environ["ANSIBLE_COW_PATH"] = cow_exe
            break
    os.environ["PATH"] = os.environ["PATH"] + os.pathsep + path
    try:
        main_cli()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)


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
        locale.getlocale = lambda: ("UTF-8", "UTF-8")
        sys.getfilesystemencoding = lambda: "utf-8"
        os.environ["PYTHONIOENCODING"] = "utf-8"
        os.environ["LC_ALL"] = "C"
        os.environ["LANG"] = "C"
    main()
