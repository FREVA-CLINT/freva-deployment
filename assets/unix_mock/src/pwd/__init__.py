"""Simulation of the pwd unix library."""

import os

import pywintypes
import win32api
import win32security


class struct_passwd:
    def __init__(
        self, pw_name, pw_passwd, pw_uid, pw_gid, pw_gecos, pw_dir, pw_shell
    ):
        self.pw_name = pw_name
        self.pw_passwd = pw_passwd
        self.pw_uid = pw_uid
        self.pw_gid = pw_gid
        self.pw_gecos = pw_gecos
        self.pw_dir = pw_dir
        self.pw_shell = pw_shell


def getpwnam(username):
    """Return the password database entry for the given user name."""

    try:
        user_info = win32security.LookupAccountName(None, username)
        sid, domain, account_type = user_info
        user_sid = win32security.ConvertSidToStringSid(sid)
        user_profile_path = win32api.GetUserProfileDirectory(sid)

        return struct_passwd(
            pw_name=username,
            pw_passwd="x",
            pw_uid=user_sid,
            pw_gid=None,  # Windows does not use gid
            pw_gecos="",
            pw_dir=user_profile_path,
            pw_shell=None,  # Windows does not use shell
        )
    except win32security.error:
        raise KeyError(f"getpwnam(): name not found: '{username}'") from None


def getpwuid(uid):
    """Return the password database entry for the given numeric user ID."""

    try:
        sid = win32security.ConvertStringSidToSid(uid)
        user_info = win32security.LookupAccountSid(None, sid)
        username, domain, account_type = user_info
        user_profile_path = win32api.GetUserProfileDirectory(sid)

        return struct_passwd(
            pw_name=username,
            pw_passwd="x",
            pw_uid=sid,
            pw_gid=None,  # Windows does not use gid
            pw_gecos="",
            pw_dir=user_profile_path,
            pw_shell=None,  # Windows does not use shell
        )
    except win32security.error:
        raise KeyError(f"getpwuid(): uid not found: '{uid}'") from None


def getpwall():
    """Return a list of all available password database entries, in arbitrary order."""
    users = []
    try:
        logon_sessions = win32security.LsaEnumerateLogonSessions()
        for luid in logon_sessions:
            session_data = win32security.LsaGetLogonSessionData(luid)
            username = session_data["UserName"]
            if username:
                users.append(getpwnam(username))
    except win32security.error:
        pass
    return users
