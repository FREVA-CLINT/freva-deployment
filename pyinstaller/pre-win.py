import locale
import os
from pathlib import Path
import re
import sys

repr_pwd = """
try:
    import pwd
except ImportError:
"""

if sys.platform.lower().startswith("win"):
    getlocale = locale.getlocale
    getfilesystemencoding = sys.getfilesystemencoding
    locale.getlocale = lambda: ("utf-8", "utf-8")
    sys.getfilesystemencoding = lambda: "utf-8"
    os.get_blocking = lambda x: True
    try:
        import ansible

        ansible_cli_path = Path(ansible.__file__).parent / "cli" / "__init__.py"
        ansible_temp_path = Path(ansible.__file__).parent / "template" / "__init__.py"
    finally:
        sys.getfilesystemencoding = getfilesystemencoding
        locale.getlocale = getlocale
    ansible_cli_path.write_text(
        re.sub("raise SystemExit", "print", ansible_cli_path.read_text())
    )
    for source_file in Path(ansible.__file__).parent.rglob("*.py"):
        source = source_file.read_text()
        if "from pwd import getpwnam, getpwuid" in source:
            source = source.replace("from pwd import getpwnam, getpwuid", "import pwd")
            source = source.replace("getpwnam", "pwd.getpwnam")
            source = source.replace("getpwuid", "pwd.getpwuid")

        for mod, repr_ in (("fcntl", repr_fcntl), ("pwd", repr_pwd)):
            source_file.write_text(re.sub(f"import {mod}", repr_, source))
else:
    import PyInstaller.depend.bindepend

    bindepend = Path(PyInstaller.depend.bindepend.__file__)
    bindepend.write_text(
        re.sub(
            "encoding='utf-8',",
            "encoding='utf-8', errors='ignore',",
            bindepend.read_text(),
        )
    )
