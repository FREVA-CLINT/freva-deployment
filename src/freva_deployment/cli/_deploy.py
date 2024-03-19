"""Command line interface for the deployment."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich_argparse import ArgumentDefaultsRichHelpFormatter
from freva_deployment import __version__

from ..deploy import DeployFactory
from ..versions import display_versions, VersionAction
from ..utils import config_dir, set_log_level


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Consturct command line argument parser."""

    ap = argparse.ArgumentParser(
        prog="deploy-freva-cmd",
        description="Deploy freva and its services on different machines.",
        formatter_class=ArgumentDefaultsRichHelpFormatter,
    )
    ap.add_argument(
        "--config",
        "-c",
        type=Path,
        help="Path to ansible inventory file.",
        default=config_dir / "inventory.toml",
    )
    ap.add_argument(
        "--steps",
        type=str,
        nargs="+",
        default=["db", "databrowser", "web", "core"],
        choices=["web", "core", "db", "databrowser", "auto"],
        help=(
            "The services/code stack to be deployed. Use [it]auto[/it]"
            " to only deploy outdated services"
        ),
    )
    ap.add_argument(
        "--ask-pass",
        help="Connect to server via ssh passwd instead of public key.",
        action="store_true",
        default=False,
    )
    ap.add_argument(
        "--ssh-port",
        help="Set the ssh port, in 99.9%% of the cases this should be 22",
        type=int,
        default=22,
    )
    ap.add_argument(
        "-v", "--verbose", action="count", help="Verbosity level", default=0
    )
    ap.add_argument(
        "-l",
        "--local",
        help="Deploy services on the local machine, debug purpose.",
        action="store_true",
        default=False,
    )
    ap.add_argument(
        "-g",
        "--gen-keys",
        help="Generate public and private web certs, use with caution.",
        action="store_true",
        default=False,
    )
    ap.add_argument(
        "-V",
        "--version",
        action=VersionAction,
        version="%(prog)s [b]{version}[/b]{services}".format(
            version=__version__, services=display_versions()
        ),
    )
    return ap.parse_args()


def cli(argv: list[str] | None = None) -> None:
    """Run the command line interface."""
    args = parse_args(argv)
    set_log_level(args.verbose)
    with DeployFactory(
        steps=args.steps,
        config_file=args.config,
        local_debug=args.local,
        gen_keys=args.gen_keys,
    ) as DF:
        DF.play(args.ask_pass, args.verbose, ssh_port=args.ssh_port)


if __name__ == "__main__":
    cli(sys.argv[1:])
