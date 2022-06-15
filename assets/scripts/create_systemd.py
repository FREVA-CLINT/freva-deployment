#!/usr/bin/env python3
import argparse
import shutil
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
        ExecStart="{container_cmd} start -a {container_name}",
        ExecStop="{container_cmd} stop {container_name}",
        Restart="no",
    ),
    Install=dict(WantedBy="default.target"),
)


def parse_args() -> Tuple[str, List[str], bool]:
    """Parse the commandline arguments."""

    app = argparse.ArgumentParser(
        prog=sys.argv[0], description="Create a new systemd unit."
    )
    app.add_argument(
        "unit_name", type=str, help="Name of the systemd unit that is created."
    )
    app.add_argument(
        "--enable", action="store_true", default=False, help="Enable this unit."
    )
    app.add_argument("--requires", type=str, nargs="+", default=[])
    args = app.parse_args()
    return args.unit_name, args.requires, args.enable


def _parse_dict(tmp_dict: Dict[str, Dict[str, str]]) -> str:
    systemd_unit = ""
    for section, keys in tmp_dict.items():
        systemd_unit += "[{}]\n".format(section)
        for key, values in keys.items():
            systemd_unit += "{} = {}\n".format(key, values)
    return systemd_unit


def load_unit(unit: str, content: str, enable: bool = True) -> None:
    """Load a given systemd unit."""
    with open("/etc/systemd/system/{}.service".format(unit), "w") as f_obj:
        f_obj.write(content)
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    if enable:
        subprocess.run(["systemctl", "enable", unit], check=True)
    subprocess.run(["systemctl", "restart", unit], check=True)


def create_unit(unit_name: str, requires: List[str], enable: bool) -> None:
    """Create the systemd unit."""
    container_cmd = shutil.which("podman") or shutil.which("docker")
    if container_cmd is None:
        raise ValueError("Docker or podman must be installed on the host.")
    if "docker" in container_cmd:
        SYSTEMD_TMPL["Unit"]["Requires"] = "docker.service"
        SYSTEMD_TMPL["Unit"]["After"] += " docker.service"
    for key in "ExecStop", "ExecStart":
        SYSTEMD_TMPL["Service"][key] = SYSTEMD_TMPL["Service"][key].format(
            container_cmd=container_cmd, container_name=unit_name
        )
    for service in requires:
        for key in ("After", "Requires"):
            try:
                SYSTEMD_TMPL["Unit"][key] += " {}.service".format(service)
            except KeyError:
                SYSTEMD_TMPL["Unit"][key] = " {}.service".format(service)
    load_unit(unit_name, _parse_dict(SYSTEMD_TMPL), enable)


if __name__ == "__main__":
    create_unit(*parse_args())
