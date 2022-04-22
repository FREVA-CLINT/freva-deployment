"""Command line interface for the deployment."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

from ..deploy import DeployFactory
from ..utils import config_dir, set_log_level, guess_map_server


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Consturct command line argument parser."""

    ap = argparse.ArgumentParser(
        prog="deploy-freva-cmd",
        description="Deploy freva and its services on different machines.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("project_name", type=str, help="Name of the project")
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
        default=["services", "web", "core"],
        choices=["services", "web", "core", "db", "solr", "backup"],
        help="The services/code stack to be deployed",
    )
    ap.add_argument(
        "--cert",
        "--cert_file",
        "--cert-file",
        type=Path,
        default=None,
        help="Path to public certificate file. If none is given, "
        "default, a file will be created.",
    )
    ap.add_argument(
        "--domain",
        type=str,
        help="Domain name of your organisation to create a uniq identifier.",
        default="dkrz",
    )
    ap.add_argument(
        "--wipe",
        action="store_true",
        default=False,
        help=(
            "This option will empty any pre-existing folders/docker volumes. "
            "(Useful for a truely fresh start)"
        ),
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
    args = ap.parse_args()
    services = {"services": ["db", "vault", "solr", "backup"]}
    steps = []

    for step in args.steps:
        try:
            steps += services[step]
        except KeyError:
            steps += [step]
    args.steps = steps
    return args


def cli(argv: list[str] | None = None) -> None:
    """Run the command line interface."""
    args = parse_args(argv)
    server_map = guess_map_server(args.server_map, mandatory=False)
    verebosity = set_log_level(args.verbose)
    with DeployFactory(
        args.project_name,
        steps=args.steps,
        cert_file=args.cert,
        config_file=args.config,
        ask_pass=args.ask_pass,
        wipe=args.wipe,
    ) as DF:
        DF.play(server_map, verebosity)


if __name__ == "__main__":
    cli(sys.argv[1:])
