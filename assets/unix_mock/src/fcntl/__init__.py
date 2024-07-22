"""Simulation of the unix lib fcntl."""

import msvcrt
import os
import struct
from ctypes import c_char

import pywintypes
import wcwidth as ww
import win32api
import win32con
import win32file

LOCK_SH = 0  # Shared lock
LOCK_EX = 1  # Exclusive lock
LOCK_NB = 2  # Non-blocking
LOCK_UN = 3  # Unlock
F_SETFL = 4
F_GETFL = 3
F_GETFD = 4


def wcwidth(text):
    return ww.wcwidth(text)


def wcswidth(text, num=None):
    return ww.wcswidth(text)


def fcntl(fd, cmd, arg=0):
    """Perform the operation `cmd` on file descriptor fd.

    The values used for `cmd` are operating system dependent, and are available
    as constants in the fcntl module, using the same names as used in
    the relevant C header files.  The argument arg is optional, and
    defaults to 0; it may be an int or a string.  If arg is given as a string,
    the return value of fcntl is a string of that length, containing the
    resulting value put in the arg buffer by the operating system.  The length
    of the arg string is not allowed to exceed 1024 bytes.  If the arg given
    is an integer or if none is specified, the result value is an integer
    corresponding to the return value of the fcntl call in the C code.
    """
    handle = msvcrt.get_osfhandle(fd)
    if cmd == F_GETFL:
        flags = win32file.GetFileType(handle)
        return flags
    if cmd == F_SETFL:
        if arg & os.O_NONBLOCK:
            win32file.SetFileAttributes(handle, win32con.FILE_FLAG_OVERLAPPED)
        else:
            win32file.SetFileAttributes(handle, win32con.FILE_ATTRIBUTE_NORMAL)
    else:
        raise NotImplementedError(
            f"Command {cmd} not implemented in this fcntl simulation."
        )
    return None


def lockf(fd, cmd, length=0, start=0, whence=os.SEEK_SET):
    """A wrapper around the fcntl() locking calls.

    `fd` is the file descriptor of the file to lock or unlock, and operation is one
    of the following values:

        LOCK_UN - unlock
        LOCK_SH - acquire a shared lock
        LOCK_EX - acquire an exclusive lock

    When operation is LOCK_SH or LOCK_EX, it can also be bitwise ORed with
    LOCK_NB to avoid blocking on lock acquisition.  If LOCK_NB is used and the
    lock cannot be acquired, an OSError will be raised and the exception will
    have an errno attribute set to EACCES or EAGAIN (depending on the operating
    system -- for portability, check for either value).

    `len` is the number of bytes to lock, with the default meaning to lock to
    EOF.  `start` is the byte offset, relative to `whence`, to that the lock
    starts.  `whence` is as with fileobj.seek(), specifically:

        0 - relative to the start of the file (SEEK_SET)
        1 - relative to the current buffer position (SEEK_CUR)
        2 - relative to the end of the file (SEEK_END)
    """
    handle = msvcrt.get_osfhandle(fd)
    overlapped = pywintypes.OVERLAPPED()
    overlapped.Offset = start

    if cmd == LOCK_SH:
        # Shared lock
        flags = win32con.LOCKFILE_FAIL_IMMEDIATELY if LOCK_NB else 0
        win32file.LockFileEx(handle, flags, 0, length, overlapped)
    elif cmd == LOCK_EX:
        # Exclusive lock
        flags = win32con.LOCKFILE_EXCLUSIVE_LOCK | (
            win32con.LOCKFILE_FAIL_IMMEDIATELY if LOCK_NB else 0
        )
        win32file.LockFileEx(handle, flags, 0, length, overlapped)
    elif cmd == LOCK_UN:
        # Unlock
        win32file.UnlockFileEx(handle, 0, length, overlapped)
    else:
        raise NotImplementedError(
            f"Command {cmd} not implemented in this lockf simulation."
        )


def ioctl(fd, request, arg=0, mutable_flag=True):
    """Perform the operation `request` on file descriptor `fd`.

    The values used for `request` are operating system dependent, and are available
    as constants in the fcntl or termios library modules, using the same names as
    used in the relevant C header files.

    The argument `arg` is optional, and defaults to 0; it may be an int or a
    buffer containing character data (most likely a string or an array).

    If the argument is a mutable buffer (such as an array) and if the
    mutate_flag argument (which is only allowed in this case) is true then the
    buffer is (in effect) passed to the operating system and changes made by
    the OS will be reflected in the contents of the buffer after the call has
    returned.  The return value is the integer returned by the ioctl system
    call.

    If the argument is a mutable buffer and the mutable_flag argument is false,
    the behavior is as if a string had been passed.

    If the argument is an immutable buffer (most likely a string) then a copy
    of the buffer is passed to the operating system and the return value is a
    string of the same length containing whatever the operating system put in
    the buffer.  The length of the arg buffer in this case is not allowed to
    exceed 1024 bytes.

    If the arg given is an integer or if none is specified, the result value is
    an integer corresponding to the return value of the ioctl call in the C
    code.
    """
    handle = msvcrt.get_osfhandle(fd)
    if mutable_flag:
        arg_buf = bytearray(arg)
    else:
        arg_buf = bytes(arg)
    buf = (c_char * len(arg_buf)).from_buffer(arg_buf)
    win32api.DeviceIoControl(handle, request, buf, None)
    return buf
