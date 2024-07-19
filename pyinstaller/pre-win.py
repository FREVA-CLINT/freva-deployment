import locale
import os
from pathlib import Path
import re
import sys

repr_pwd = """try:
    import pwds as pwd
except ImportError:

    class pwd:
        def __init__(self, *args, **kwargs):
            raise TypeError("NaA")
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
    ansible_temp_path.write_text(
        re.sub("import pwd", repr_pwd, ansible_temp_path.read_text())
    )
