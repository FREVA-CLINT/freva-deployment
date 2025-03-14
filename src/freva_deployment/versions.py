"""Define the version of the microservices."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from rich import print as pprint
from rich.prompt import Prompt


class VersionAction(argparse._VersionAction):
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Any,
        option_string=None,
    ):
        version = self.version or "%(prog)s"
        pprint(version % {"prog": parser.prog or sys.argv[1]})
        parser.exit()


def display_versions() -> str:
    """Get all service versions for display."""
    minimum_version = json.loads(
        (Path(__file__).parent / "versions.json").read_text()
    )
    lookup = {
        "freva_rest": "freva-rest API",
        "core": "freva-core",
        "solr": "apache-solr",
        "web": "webUI",
    }
    versions = ""
    for service, version in minimum_version.items():
        service_name = lookup.get(service, service)
        versions += f"\n   [b][green]{service_name}[/b][/green] {version}"
    return versions


def get_steps_from_versions(detected_versions: Dict[str, str]) -> List[str]:
    """Decide on services the should be deployed, based on thier versions.

    Parameters
    ----------
    detected_versions: dict
        The versions that have been detected to be deployed.

    Returns
    -------
    list: A list of services that should be updated.
    """
    minimum_version = json.loads(
        (Path(__file__).parent / "versions.json").read_text()
    )
    steps = []
    lookup = {"solr": "freva_rest", "vault": "db"}
    no_ask_for_downgrade = ("solr", "db")
    for service, min_version in minimum_version.items():
        lookup.setdefault(service, service)
        min_version = minimum_version[service].strip("v")
        version = detected_versions.get(service, "").strip("v").strip()
        if service == "web" and not version:
            continue
        version = version or "0.0.0"
        if version < min_version:
            steps.append(lookup[service])
        elif version > min_version and service not in no_ask_for_downgrade:
            # We do have a problem: an installed version has a higher version
            # the the defined minium version, possibly the deployment
            # software is outdated.
            if os.environ.get("INTERACTIVE_DEPLOY", "1"):
                answ = (
                    Prompt.ask(
                        f"The installed version for [green]{service}[/green] is higher"
                        " than the min. defined version.\nThere might be"
                        " a chance that the current deployment software"
                        " is outdated.\nIf you continue you will "
                        f"[b]downgrade[/b] [green]{service}[/green] from "
                        f"{version} to {min_version}. "
                        "\nDo you want to continue \\[y|N]"
                    ).lower()
                    or "n"
                )
            else:
                answ = "n"
            if answ[0] == "y":
                steps.append(lookup[service])
            else:
                raise SystemExit(1)
    return steps
