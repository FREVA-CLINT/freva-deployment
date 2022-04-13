"""CLI to interact with running services."""
from __future__ import annotations
import argparse
from getpass import getuser
from pathlib import Path
import shlex
from subprocess import run
import sys
from tempfile import TemporaryDirectory

from ..utils import download_data_from_nextcloud, logger


def parse_args(args: list[str]) -> argparse.Namespace:
    """Consturct command line argument parser."""
    app = argparse.ArgumentParser(
        prog="freva-service",
        description="Interact with installed freva services.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    app.add_argument(
        "command",
        type=str,
        choices=("start", "stop", "restart"),
        help="The start|stop|restart command for the service",
    )
    app.add_argument("project_name", type=str, help="Name of the project")
    app.add_argument(
        "--services",
        type=str,
        nargs="+",
        default=["solr", "db", "web"],
        choices=["web", "db", "solr"],
        help="The services to be started|stopped|restarted",
    )
    app.add_argument(
        "--user", "-u", type=str, help="connect as this user", default=None
    )
    argsp = app.parse_args(args)
    if "db" in argsp.services:
        argsp.services.append("vault")
    return argsp


YAML_TASK = """---
- hosts: {group}
  vars:
    ansible_python_interpreter: {python_env}
  tasks:
  - name: {command}ing {service} service on {hosts}
    shell: systemctl {command} {project_name}-{service}.service
    become: yes
"""

YAML_INVENTORY = """
{group}:
    hosts: {hosts}
"""


def _create_playbook(
    project_name: str,
    command: str,
    services: list[str],
    config: dict[str, dict[str, str]],
) -> tuple[str, str]:
    """Create a ansible playbook for given services."""
    playbooks: list[str] = []
    inventory: list[str] = []
    for service in services:
        python_env = config[service]["ansible_python_interpreter"]
        hosts = config[service]["hosts"]
        group = project_name.replace("-", "_") + "_" + service
        playbooks.append(
            YAML_TASK.format(
                python_env=python_env,
                project_name=project_name,
                service=service,
                command=command,
                group=group,
                hosts=hosts,
            )
        )
        inventory.append(
            YAML_INVENTORY.format(
                hosts=hosts,
                project_name=project_name,
                service=service,
                group=group,
            )
        )
    return "\n".join(playbooks), "\n".join(inventory)


def _get_playbook_for_project(
    project_name: str,
    command: str,
    services: list[str],
    config: dict[str, dict[str, str]],
) -> tuple[str, str]:
    return _create_playbook(project_name, command, services, config)


def cli(argv: list[str] | None = None) -> None:
    """Run command line interface."""
    argv = argv or sys.argv[1:]
    argp = parse_args(argv)
    user = argp.user or getuser()
    cfg = download_data_from_nextcloud()
    if argp.project_name.lower() == "all":
        project_names = list(cfg.keys())
    else:
        project_names = [argp.project_name]
    playbooks, inventory = [], []
    for project_name in project_names:
        try:
            config = cfg[project_name]
        except KeyError:
            logger.error("poject name %s not defined", project_name)
            continue
        try:
            p_book, i_nventory = _get_playbook_for_project(
                project_name, argp.command, argp.services, config
            )
            playbooks.append(p_book)
            inventory.append(i_nventory)
        except KeyError as error:
            logger.error(error.__str__())
            continue
    if not playbooks:
        return
    with TemporaryDirectory() as temp_dir:
        inventory_file = Path(temp_dir) / "inventory.yaml"
        task_file = Path(temp_dir) / "tasks.yaml"
        with open(inventory_file, "w") as f_obj:
            f_obj.write("\n".join(inventory))
        with open(task_file, "w") as f_obj:
            f_obj.write("\n".join(playbooks))
        cmd = shlex.split(
            f"ansible-playbook -u {user} --ask-pass --ask-become -i "
            f"{inventory_file} {task_file}"
        )
        run(cmd, check=True)
