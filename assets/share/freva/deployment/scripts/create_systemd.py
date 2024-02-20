#!/usr/bin/env python3
import argparse
from pathlib import Path
import os
import shlex
import sys
import subprocess
from typing import Dict, List, Tuple

SYSTEMD_TMPL = dict(
    Unit=dict(
        Description="Start/Stop freva services containers",
        After="network-online.target",
    ),
    Service=dict(
        TimeoutStartSec="35s",
        TimeoutStopSec="35s",
        ExecStartPre='/bin/sh -c "{delete_command}"',
        ExecStart='/bin/sh -c "{container_cmd} {container_args}"',
        ExecStop='/bin/sh -c "{delete_command}"',
        Restart="no",
    ),
    Install=dict(WantedBy="default.target"),
)


def parse_args() -> Tuple[str, str, List[str], bool]:
    """Parse the commandline arguments."""

    app = argparse.ArgumentParser(
        prog=sys.argv[0], description="Create a new systemd unit."
    )
    app.add_argument("name", type=str, help="Set the container name")
    app.add_argument(
        "--enable",
        action="store_true",
        default=False,
        help="Enable this unit.",
    )
    app.add_argument("--requires", type=str, nargs="+", default=[])
    args, other = app.parse_known_args()
    enable = args.enable
    if os.environ.get("DEBUG", "false").lower() == "true":
        enable = False
    return " ".join(other), args.name, args.requires, enable


def _parse_dict(tmp_dict: Dict[str, Dict[str, str]]) -> str:
    systemd_unit = ""
    for section, keys in tmp_dict.items():
        systemd_unit += "[{}]\n".format(section)
        for key, values in keys.items():
            systemd_unit += "{}={}\n".format(key, values)
    return systemd_unit


def load_unit(unit: str, content: str, enable: bool = True) -> None:
    """Load a given systemd unit."""
    files = (
        "/etc/systemd/system/{}.service".format(unit),
        "~/.local/share/systemd/user/{}.service".format(unit),
    )
    flags = ("", "--user")
    for file, flag in zip(files, flags):
        out_file = Path(file).expanduser()
        try:
            out_file.parent.mkdir(exist_ok=True, parents=True)
            with out_file.open(mode="w", encoding="utf-8") as f_obj:
                f_obj.write(content)
        except PermissionError:
            continue
        cmd = ["systemctl"]
        if flag:
            cmd += [flag]

        subprocess.run(cmd + ["daemon-reload"], check=True)
        if enable:
            subprocess.run(cmd + ["enable", unit], check=True)
        subprocess.run(cmd + ["restart", unit], check=True)
        return


def get_container_cmd(args: str) -> Tuple[str, str]:
    """Get the correct container command for the system."""
    path = os.environ.get("PATH", "") + ":" + "/usr/local/bin"
    env = os.environ.copy()
    env["PATH"] = path
    cmd = ["/tmp/docker-or-podman", "--print-only"] + shlex.split(args)
    res = subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        env=env,
    )
    out = res.stdout.decode().split()
    if out:
        return out[0], " ".join(out[1:])
    return "", ""


def create_unit(
    args: str, unit: str, requires: List[str], enable: bool
) -> None:
    """Create the systemd unit."""
    container_cmd, container_args = get_container_cmd(args)
    cmd = args.split()
    if "compose" in cmd and "up" in cmd:
        new_cmd = []
        for word in cmd:
            if word == "up":
                new_cmd.append("down")
            elif word not in ("-d", "--detach"):
                new_cmd.append(word)
        _, delete_command = get_container_cmd(" ".join(new_cmd))
    else:
        _, delete_command = get_container_cmd("rm -f {}".format(unit))
    if delete_command:
        delete_command = "{} {}".format(container_cmd, delete_command)
    else:
        delete_command = ""
    if "docker" in container_cmd:
        SYSTEMD_TMPL["Unit"]["Requires"] = "docker.service"
        SYSTEMD_TMPL["Unit"]["After"] += " docker.service"
    for key in ("ExecStart",):
        SYSTEMD_TMPL["Service"][key] = SYSTEMD_TMPL["Service"][key].format(
            container_cmd=container_cmd,
            container_args=container_args,
            unit=unit,
        )
    for key in ("ExecStartPre", "ExecStop"):
        SYSTEMD_TMPL["Service"][key] = SYSTEMD_TMPL["Service"][key].format(
            delete_command=delete_command
        )
    for service in requires:
        for key in ("After", "Requires"):
            try:
                SYSTEMD_TMPL["Unit"][key] += " {}.service".format(service)
            except KeyError:
                SYSTEMD_TMPL["Unit"][key] = " {}.service".format(service)
    load_unit(unit, _parse_dict(SYSTEMD_TMPL), enable)


if __name__ == "__main__":
    create_unit(*parse_args())
