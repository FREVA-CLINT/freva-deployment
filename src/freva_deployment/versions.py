"""Define the version of the microservices."""

import json
from pathlib import Path

minimum_version = json.loads(
    (Path(__file__).parent / "versions.json").read_text()
)
