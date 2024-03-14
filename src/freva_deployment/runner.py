"""Ansible runner interaction."""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Union

import yaml


class RunnerDir(TemporaryDirectory):
    """Define and create the Ansible runner directory."""

    def __init__(self) -> None:

        super().__init__(prefix="AnsibleRunner")
        self.parent_dir = Path(self.name)
        self.env_dir = self.parent_dir / "env"
        self.inventory_dir = self.parent_dir / "inventory"
        self.project_dir = self.parent_dir / "project"
        for _dir in (self.env_dir, self.inventory_dir, self.project_dir):
            _dir.mkdir(exist_ok=True, parents=True)

    def create_playbook(self, content: List[Dict[str, Any]]) -> str:
        """Dump the content of a playbook into the playbook file."""
        with (self.playbook_file).open("w") as stream:
            yaml.dump(content, stream)
        return self.playbook_file.read_text()

    @property
    def inventory_file(self) -> Path:
        """Define the location of the inventory file."""
        return self.project_dir / "hosts"

    @property
    def playbook_file(self) -> Path:
        """Define the location of the playbook file."""
        return self.project_dir / "playbook.yaml"
