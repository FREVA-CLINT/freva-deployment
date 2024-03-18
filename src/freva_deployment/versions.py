"""Define the version of the microservices."""

import json
from pathlib import Path
from typing import Dict, List


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
    return steps
