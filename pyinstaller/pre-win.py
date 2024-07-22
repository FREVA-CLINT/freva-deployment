import locale
import os
import re
import sys
from pathlib import Path

if sys.platform.lower().startswith("win"):
    getlocale = locale.getlocale
    getfilesystemencoding = sys.getfilesystemencoding
    locale.getlocale = lambda: ("utf-8", "utf-8")
    sys.getfilesystemencoding = lambda: "utf-8"
    os.get_blocking = lambda x: True
    try:
        import ansible

        ansible_cli_path = (
            Path(ansible.__file__).parent / "cli" / "__init__.py"
        )
    finally:
        sys.getfilesystemencoding = getfilesystemencoding
        locale.getlocale = getlocale
    ansible_cli_path.write_text(
        re.sub("raise SystemExit", "print", ansible_cli_path.read_text())
    )
    for inp_file in Path(ansible.__file__).parent.rglob("*.py"):
        content = inp_file.read_text(encoding="utf-8")
        write = False
        for call in ("isatty", "get_blocking"):
            if f"os.{call}" in content:
                write = True
                if "import os, tty" not in content:
                    content = content.replace("import os", "import os, tty")
                content = content.replace(f"os.{call}", f"tty.{call}")
        if write:
            inp_file.write_text(content, encoding="utf-8")
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
