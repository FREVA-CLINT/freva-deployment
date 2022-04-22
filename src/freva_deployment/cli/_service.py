"""CLI to interact with running services."""
from __future__ import annotations
import argparse
from getpass import getuser
from pathlib import Path
import shlex
from subprocess import run, PIPE
import requests
import sys
from tempfile import TemporaryDirectory

from rich.console import Console

from ..utils import (
    download_server_map,
    logger,
    set_log_level,
    ServiceInfo,
    get_setup_for_service,
    guess_map_server,
)


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
        choices=("start", "stop", "restart", "status"),
        help="The start|stop|restart|status command for the service",
    )
    app.add_argument(
        "project_name",
        type=str,
        help="Name of the project",
        default="all",
        nargs="?",
    )
    app.add_argument(
        "--server-map",
        type=str,
        default=None,
        help=(
            "Hostname of the service mapping the freva server "
            "archtiecture, Note: you can create a server map by "
            "running the deploy-freva-map command"
        ),
    )
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
    app.add_argument(
        "-v", "--verbose", action="count", help="Verbosity level", default=0
    )
    argsp = app.parse_args(args)
    if "db" in argsp.services:
        argsp.services.append("vault")
    return argsp


YAML_TASK = """---
- hosts: {group}
  vars:
    ansible_python_interpreter: {python_env}
    map_server: {map_server}
  tasks:
  - name: {command}ing {service} service on {hosts}
    shell: systemctl {command} {project_name}-{service}.service
    become: yes
"""
YAML_STATUS_TASK = """---
- hosts: {group}
  vars:
    ansible_python_interpreter: {python_env}
    container: {project_name}-{service}
  tasks:
  - name: {command} {service} service on {hosts}
    shell: curl -d "{{{{ item }}}}" {map_server}/{project_name}/{service} -X PUT
    with_items:
        - mem=$(docker stats --no-stream {{{{ container }}}} --no-trunc --format '{{% raw %}}{{{{.MemPerc}}}}{{% endraw %}}')
        - cpu=$(docker stats --no-stream {{{{ container }}}} --no-trunc --format '{{% raw %}}{{{{.CPUPerc}}}}{{% endraw %}}')
        - status=$(docker ps  -a --filter name={{{{ container }}}} --format '{{% raw %}}{{{{.Status}}}}{{% endraw %}}')
    become: yes

"""

YAML_INVENTORY = """
{group}:
    hosts: {hosts}
"""


def _get_playbook_for_project(
    map_server: str,
    project_name: str,
    command: str,
    services: list[str],
    config: list[ServiceInfo],
) -> tuple[str, str]:
    """Create a ansible playbook for given services."""
    playbooks: list[str] = []
    inventory: list[str] = []
    for service in services:
        python_env, hosts = get_setup_for_service(service, config)
        group = project_name.replace("-", "_") + "_" + service
        if command == "status":
            cmd = "checking"
            tmpl = YAML_STATUS_TASK
        else:
            cmd = command
            tmpl = YAML_TASK
        playbooks.append(
            tmpl.format(
                python_env=python_env,
                project_name=project_name,
                service=service,
                command=cmd,
                group=group,
                hosts=hosts,
                map_server=map_server,
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


def cli(argv: list[str] | None = None) -> None:
    """Run command line interface."""
    argv = argv or sys.argv[1:]
    argp = parse_args(argv)
    map_server = guess_map_server(argp.server_map)
    verbosity = set_log_level(argp.verbose)
    user = argp.user or getuser()
    cfg = download_server_map(map_server)
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
                map_server, project_name, argp.command, argp.services, config
            )
            playbooks.append(p_book)
            inventory.append(i_nventory)
        except (KeyError, AttributeError) as error:
            logger.error(error.__str__())
            continue
    if not playbooks:
        return
    with TemporaryDirectory() as temp_dir:
        inventory_file = Path(temp_dir) / "inventory.yaml"
        task_file = Path(temp_dir) / "tasks.yaml"
        logger.debug("\n".join(inventory))
        with open(inventory_file, "w") as f_obj:
            f_obj.write("\n".join(inventory))
        with open(task_file, "w") as f_obj:
            f_obj.write("\n".join(playbooks))
        logger.debug("\n".join(playbooks))
        cmd = shlex.split(
            f"ansible-playbook {verbosity} -u {user} --ask-pass --ask-become -i "
            f"{inventory_file} {task_file}"
        )
        if verbosity:
            run(cmd, check=True)
        else:
            run(cmd, check=True, stdout=PIPE)
    if argp.command == "status":
        con = Console()
        (
            header,
            std_out,
        ) = ["SERVICE", "MEM", "CPU", "STATUS"], []
        n_server_char = 0
        for project in project_names:
            for service in argp.services:
                status = requests.get(f"http://{map_server}/{project}/{service}").json()
                status_line = [f"{project}-{service}"]
                n_server_char = max(len(status_line[0]), n_server_char)
                for key in ("mem", "cpu", "status"):
                    status_line.append(status.get(key))
                std_out.append(status_line)
        format_row = "{:>12}" * (len(header) + 1)
        con.print(format_row.format("", *header), style="bold", markup=True)
        for line in std_out:
            con.print(format_row.format("", *line), markup=True)
