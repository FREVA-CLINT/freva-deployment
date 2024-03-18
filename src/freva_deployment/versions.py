"""Define the version of the microservices."""

import json
from pathlib import Path
from typing import Dict, List

from rich.prompt import Prompt


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
    for service, min_version in minimum_version.items():
        min_version = minimum_version[service].strip("v")
        version = detected_versions.get(service, "").strip("v") or "0.0.0"
        if version < min_version:
            steps.append(service)
        elif version > min_version:
            # We do have a problem: an installed version has a higher version
            # the the defined minium version, possibly the deployment
            # software is outdated.
            answ = (
                Prompt.ask(
                    f"The installed version for {service} is higher"
                    " than the min. defined version.\nThere might be"
                    " a chance that the current deployment software"
                    " is outdated.\nIf you cotinue you will "
                    f"[b]downgrade[/b] {service} from "
                    f"{version} to {min_version}. "
                    "\nDo you want to continue \\[y|N]"
                ).lower()
                or "n"
            )
            if answ[0] == "y":
                steps.append(service)
            else:
                raise SystemExit(1)
    return steps
