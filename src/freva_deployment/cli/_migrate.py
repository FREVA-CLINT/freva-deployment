"""CLI to assist with migrating the system."""
from __future__ import annotations
import argparse
from pathlib import Path
import shlex
import sys


def _migrate_db(old_path: Path, new_path: Path) -> None:
    print(old_path, new_path)


def _migrate_drs(old_path: Path, new_path: Path) -> None:
    print(old_path, new_path)


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Consturct command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="freva-migrate",
        description="Utilities to handle migrations from old freva systems.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-v", "--verbose", action="count", help="Verbosity level", default=0
    )
    subparsers = parser.add_subparsers(help="Migration commands:", required=True)
    db_parser = subparsers.add_parser(
        "database",
        description="Freva database migration",
        help="Use this command to migrate an existing freva database "
        "to a recently setup system.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    db_parser.add_argument("old-freva", type=Path, help="Path to old freva instance")
    db_parser.add_argument("new-freva", type=Path, help="Path to new freva instance")
    db_parser.set_defaults(apply_func=_migrate_db)
    drs_parser = subparsers.add_parser(
        "drs-config",
        description="Freva drs structure migration",
        help="Migrate old drs structure definitions to new toml style.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    drs_parser.add_argument(
        "old-freva",
        type=Path,
        help="Path to the old freva instance",
    )
    drs_parser.add_argument(
        "new-freva",
        type=Path,
        help="Path to the new freva instance",
    )
    drs_parser.set_defaults(apply_func=_migrate_drs)
    arg = parser.parse_args(argv)
    return arg


def cli() -> None:
    """Run the command line interface."""
    arg = parse_args(sys.argv[1:])
    arg.apply_func(arg.old_freva, arg.new_freva)
