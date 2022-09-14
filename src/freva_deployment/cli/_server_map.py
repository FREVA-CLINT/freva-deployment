"""CLI to interact with running services."""
from __future__ import annotations
import argparse
from getpass import getuser
import json
import logging
from pathlib import Path
import shlex
from subprocess import run
import sys
from tempfile import NamedTemporaryFile

import appdirs
from numpy import sign

from freva_deployment import __version__
from ..utils import asset_dir, logger


def parse_args(args: list[str]) -> argparse.Namespace:
    """Consturct command line argument parser."""
    app = argparse.ArgumentParser(
        prog="deploy-freva-map",
        description="Create service that maps the freva server architecture.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    app.add_argument(
        "servername",
        type=str,
        help="The server name where the infrastructure mapping service is deployed",
    )
    app.add_argument(
        "--port",
        type=int,
        help="The port the service is listing to",
        default=6111,
    )
    app.add_argument(
        "--wipe",
        default=False,
        action="store_true",
        help="Delete any existing data.",
    )
    app.add_argument(
        "--user",
        default=None,
        type=str,
        help="Username to log on to the target server.",
    )
    app.add_argument(
        "--python-path",
        default="/usr/bin/python",
        type=Path,
        help="Path to the default python3 interpreter on the target machine.",
    )
    app.add_argument(
        "-v", "--verbose", action="count", help="Verbosity level", default=0
    )
    app.add_argument(
        "-V",
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=__version__),
    )
    argsp = app.parse_args(args)
    return argsp


YAML_INVENTORY = """
freva_map:
    hosts: {hosts}
    vars:
        ansible_python_interpreter: {python_path}
        port: {port}
        asset_dir: {asset_dir}
        wipe: {wipe}
"""


INPT_MSG = (
    "You should only deploy the server map once per domain/institution."
    " Are you sure you want to continue"
)


def cli(argv: list[str] | None = None) -> None:
    """Run command line interface."""
    argv = argv or sys.argv[1:]
    argp = parse_args(argv)
    user = argp.user or getuser()
    playbook = asset_dir / "playbooks" / "server-map-playbook.yml"
    logger.critical(INPT_MSG)
    logger.setLevel(max(logging.INFO - 10 * argp.verbose, logging.DEBUG))
    answer = input("Continue? [y|N]: ")
    verbosity = sign(argp.verbose) * "-" + argp.verbose * "v"
    if answer.lower() not in ("yes", "y"):
        logger.debug("Exiting routine.")
        return
    with NamedTemporaryFile() as inventory_file:
        inventory = YAML_INVENTORY.format(
            hosts=argp.servername,
            python_path=argp.python_path,
            port=argp.port,
            asset_dir=asset_dir,
            wipe=str(argp.wipe).lower(),
        )
        logger.debug(inventory)
        with open(inventory_file.name, "w") as f_obj:
            f_obj.write(inventory)
        cmd = shlex.split(
            f"ansible-playbook {verbosity} -u {user} --ask-pass --ask-become -i "
            f"{inventory_file.name} {playbook}"
        )
        run(cmd, check=True)
        cache_dir = Path(appdirs.user_cache_dir()) / "freva-deployment"
        host_name = f"{argp.servername}:{argp.port}"
        try:
            with (cache_dir / "freva_deployment.json").open("r") as f_obj:
                config = json.load(f_obj)
        except (FileNotFoundError, IOError, json.JSONDecodeError):
            config = {}
        config["server_map"] = host_name
        with (cache_dir / "freva_deployment.json").open("w") as f_obj:
            json.dump(config, f_obj)
