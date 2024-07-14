"""Ansible runner interaction."""

import json
import os
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any, Dict, List, Optional, Union

import yaml
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner

from .error import DeploymentError
from .logger import logger


def run_command_with_spinner(
    command: list, env: dict, text: str
) -> subprocess.CompletedProcess:
    console = Console(stderr=True)
    spinner = Spinner("weather", text=text)

    with Live(spinner, refresh_per_second=3, console=console):
        try:
            result = subprocess.run(
                command, env=env, capture_output=True, text=True
            )
        except KeyboardInterrupt:
            spinner.update(text=text + " [yellow]canceled[/yellow]")
            raise KeyboardInterrupt("User interrupted execution") from None

        if result.returncode == 0:
            spinner.update(text=text + " [green]ok[/green]")
        else:
            spinner.update(text=text + " [red]failed[/red]")
            print(result.stdout)
    return result


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
        self.ansible_config_file = str(self.parent_dir / "ansible.cfg")

    def create_config(self, **kwargs: str) -> None:
        """Create an ansible config."""
        with open(self.ansible_config_file, "w", encoding="utf-8") as stream:
            stream.write("[defaults]\n")
            for key, value in kwargs.items():
                stream.write(f"{key} = {value}\n")

    def create_playbook(self, content: List[Dict[str, Any]]) -> str:
        """Dump the content of a playbook into the playbook file."""
        for nn, step in enumerate(content):
            host = step["hosts"]
            for tt, task in enumerate(step["tasks"]):
                try:
                    content[nn]["tasks"][tt][
                        "name"
                    ] = f"{host} - {task['name']}"
                except KeyError:
                    pass
        content_str = yaml.safe_dump(content)
        self.playbook_file.write_text(content_str)
        return content_str

    @property
    def inventory_file(self) -> Path:
        """Define the location of the inventory file."""
        return self.project_dir / "hosts"

    @property
    def playbook_file(self) -> Path:
        """Define the location of the playbook file."""
        return self.project_dir / "playbook.yaml"

    def write_to_tempfile(self, content: str) -> str:
        """
        Write the given content to a temporary file and return the file path.
        """
        temp_file = NamedTemporaryFile(
            dir=self.parent_dir, delete=False, mode="w", suffix=".yml"
        )
        temp_file.write(content)
        temp_file.close()
        return temp_file.name

    def convert_to_file(
        self, content: Union[Path, str, List[Any], Dict[str, Any]]
    ) -> str:
        """
        Convert inventory input to a file path. If it is already a path, return it.
        If it is a string or list of dicts, write it to a temporary file and return the path.
        """
        if isinstance(content, Path):
            return str(content)
        if isinstance(content, str):
            if os.path.isfile(content):
                return content
            else:
                return self.write_to_tempfile(content)
        elif isinstance(content, (list, dict)):
            content_str = yaml.dump(json.loads(json.dumps(content)))
            return self.write_to_tempfile(content_str)
        else:
            raise ValueError("Invalid inventory format")

    def run_ansible_playbook(
        self,
        playbook: Union[str, Path, List[Any], Dict[str, Any]],
        inventory: Union[str, Path, List[Any], Dict[str, Any]],
        envvars: Optional[Dict[str, str]] = None,
        extravars: Optional[Dict[str, str]] = None,
        cmdline: Optional[str] = None,
        verbosity: int = 0,
        passwords: Optional[Dict[str, str]] = None,
        hide_output: bool = False,
        text: str = "Running playbook ...",
        output: str = "",
    ) -> None:
        """
        Run an Ansible playbook using subprocess.

        Parameters:
        playbook_path (str): Path to the playbook.
        inventory_path (str): Path to the inventory file.
        envvars (Optional[Dict[str, str]]): Environment variables to set for Ansible.
        extravars (Optional[Dict[str, str]]): Extra variables to pass to Ansible.
        cmdline (Optional[str]): Extra command line arguments for Ansible.
        verbosity (int): Verbosity level for Ansible output.
        hide_output (bool): Hide stdout and stderr if True, show only on failure.

        Raises:
        DeploymentError: If the Ansible playbook execution fails.
        """
        playbook_path = self.convert_to_file(playbook)
        inventory_path = self.convert_to_file(inventory)
        passwords = passwords or {}
        extravars = extravars or {}
        envvars = envvars or {}
        # Prepare the command
        command = ["ansible-playbook", playbook_path, "-i", inventory_path]

        # Set environment variables
        env = os.environ.copy()
        for key, passwd in passwords.items():
            envvars[key.upper()] = passwd
            extravars[key] = f'{{{{ lookup("env", "{key.upper()}") }}}}'

        env.update(envvars)
        # Add extra variables
        for key, value in extravars.items():
            command.append(f"-e {key}='{value}'")

        # Add command line arguments
        if cmdline:
            command.extend(cmdline.split())

        # Add verbosity
        if verbosity > 0:
            command.append("-" + "v" * verbosity)
        logger.debug("Running ansible command %s", " ".join(command))
        # Run the command
        if hide_output and verbosity == 0:
            result = run_command_with_spinner(command, env, text)
        else:
            result = subprocess.run(
                command, env=env, capture_output=False, text=True
            )

        # Determine if the command was successful
        success = result.returncode == 0
        # Raise an error if the playbook execution failed
        if not success:
            raise DeploymentError("Deployment failed!")
