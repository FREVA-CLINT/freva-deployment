"""Command line interface for the deployment."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

from freva_deployment import __version__
from ..deploy import DeployFactory
from ..utils import config_dir, set_log_level, guess_map_server


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Consturct command line argument parser."""

    ap = argparse.ArgumentParser(
        prog="deploy-freva-cmd",
        description="Deploy freva and its services on different machines.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument(
        "--server-map",
        type=str,
        default=None,
        help=(
            "Hostname of the service mapping the freva server "
            "archtiecture, Note: you can create a server map by "
            "running the deploy-freva-map command"
        ),
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
        default=["db", "solr", "web", "core"],
        choices=["web", "core", "db", "solr"],
        help="The services/code stack to be deployed",
    )
    ap.add_argument(
        "--ask-pass",
        help="Connect to server via ssh passwd instead of public key.",
        action="store_true",
        default=False,
    )
    ap.add_argument(
        "-v", "--verbose", action="count", help="Verbosity level", default=0
    )
    ap.add_argument(
        "-V",
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=__version__),
    )
    return ap.parse_args()


def cli(argv: list[str] | None = None) -> None:
    """Run the command line interface."""
    args = parse_args(argv)
    if args.server_map:
        server_map = guess_map_server(args.server_map, mandatory=False)
    else:
        server_map = ""
    set_log_level(args.verbose)
    with DeployFactory(
        steps=args.steps,
        config_file=args.config,
    ) as DF:
        DF.play(server_map, args.ask_pass, args.verbose)


if __name__ == "__main__":
    cli(sys.argv[1:])
