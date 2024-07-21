import locale
import os
from pathlib import Path
import re
import sys

repr_pwd = """
try:
    import pwd
except ImportError:
    import os
    import win32api
    import win32security
    import pywintypes

    class pwd:
        class struct_passwd:
            def __init__(self, pw_name, pw_passwd, pw_uid, pw_gid, pw_gecos, pw_dir, pw_shell):
                self.pw_name = pw_name
                self.pw_passwd = pw_passwd
                self.pw_uid = pw_uid
                self.pw_gid = pw_gid
                self.pw_gecos = pw_gecos
                self.pw_dir = pw_dir
                self.pw_shell = pw_shell

        @staticmethod
        def getpwnam(username):
            try:
                user_info = win32security.LookupAccountName(None, username)
                sid, domain, account_type = user_info
                user_sid = win32security.ConvertSidToStringSid(sid)
                user_profile_path = win32api.GetUserProfileDirectory(sid)

                return pwd.struct_passwd(
                    pw_name=username,
                    pw_passwd='x',
                    pw_uid=user_sid,
                    pw_gid=None,  # Windows does not use gid
                    pw_gecos='',
                    pw_dir=user_profile_path,
                    pw_shell=None  # Windows does not use shell
                )
            except win32security.error:
                raise KeyError(f"getpwnam(): name not found: '{username}'")

        @staticmethod
        def getpwuid(uid):
            try:
                sid = win32security.ConvertStringSidToSid(uid)
                user_info = win32security.LookupAccountSid(None, sid)
                username, domain, account_type = user_info
                user_profile_path = win32api.GetUserProfileDirectory(sid)

                return pwd.struct_passwd(
                    pw_name=username,
                    pw_passwd='x',
                    pw_uid=sid,
                    pw_gid=None,  # Windows does not use gid
                    pw_gecos='',
                    pw_dir=user_profile_path,
                    pw_shell=None  # Windows does not use shell
                )
            except win32security.error:
                raise KeyError(f"getpwuid(): uid not found: '{uid}'")

        @staticmethod
        def getpwall():
            users = []
            try:
                logon_sessions = win32security.LsaEnumerateLogonSessions()
                for luid in logon_sessions:
                    session_data = win32security.LsaGetLogonSessionData(luid)
                    username = session_data['UserName']
                    if username:
                        users.append(pwd.getpwnam(username))
            except win32security.error:
                pass
            return users
"""

repr_fcntl = """
try:
    import fcntl
except ImportError:
    import os
    import struct
    import msvcrt
    import pywintypes
    import win32file
    import win32con
    import win32api
    from ctypes import c_char

    class fcntl:
        LOCK_SH = 0  # Shared lock
        LOCK_EX = 1  # Exclusive lock
        LOCK_NB = 2  # Non-blocking
        LOCK_UN = 3  # Unlock
        F_SETFL  = 4
        F_GETFL = 3
        F_GETFD = 4


        @staticmethod
        def fcntl(fd, cmd, arg=0):
            handle = msvcrt.get_osfhandle(fd)
            if cmd == fcntl.F_GETFL:
                flags = win32file.GetFileType(handle)
                return flags
            elif cmd == fcntl.F_SETFL:
                if arg & os.O_NONBLOCK:
                    win32file.SetFileAttributes(handle, win32con.FILE_FLAG_OVERLAPPED)
                else:
                    win32file.SetFileAttributes(handle, win32con.FILE_ATTRIBUTE_NORMAL)
            else:
                raise NotImplementedError(f"Command {cmd} not implemented in this fcntl simulation.")

        @staticmethod
        def lockf(fd, cmd, length=0, start=0, whence=os.SEEK_SET):
            handle = msvcrt.get_osfhandle(fd)
            overlapped = pywintypes.OVERLAPPED()
            overlapped.Offset = start

            if cmd == fcntl.LOCK_SH:
                # Shared lock
                flags = win32con.LOCKFILE_FAIL_IMMEDIATELY if fcntl.LOCK_NB else 0
                win32file.LockFileEx(
                    handle,
                    flags,
                    0,
                    length,
                    overlapped
                )
            elif cmd == fcntl.LOCK_EX:
                # Exclusive lock
                flags = win32con.LOCKFILE_EXCLUSIVE_LOCK | (win32con.LOCKFILE_FAIL_IMMEDIATELY if fcntl.LOCK_NB else 0)
                win32file.LockFileEx(
                    handle,
                    flags,
                    0,
                    length,
                    overlapped
                )
            elif cmd == fcntl.LOCK_UN:
                # Unlock
                win32file.UnlockFileEx(
                    handle,
                    0,
                    length,
                    overlapped
                )
            else:
                raise NotImplementedError(f"Command {cmd} not implemented in this lockf simulation.")

        @staticmethod
        def ioctl(fd, request, arg=0, mutable_flag=True):
            handle = msvcrt.get_osfhandle(fd)
            if mutable_flag:
                arg_buf = bytearray(arg)
            else:
                arg_buf = bytes(arg)
            buf = (c_char * len(arg_buf)).from_buffer(arg_buf)
            win32api.DeviceIoControl(handle, request, buf, None)
            return buf
"""

if not sys.platform.lower().startswith("win"):
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
        for mod, repr_ in (("fcntl", repr_fcntl), ("pwd", repr_pwd)):
            source_file.write_text(
                re.sub(f"import {mod}", repr_, source_file.read_text())
            )
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
