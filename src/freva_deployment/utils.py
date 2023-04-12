"""Collection of utils for deployment."""
from __future__ import annotations
import hashlib
import logging
import json
from pathlib import Path
import pkg_resources
import re
from subprocess import PIPE
import sys
import shutil
from typing import Any, NamedTuple, cast
import warnings

import appdirs
import requests
from rich.console import Console
from rich.prompt import Prompt
import toml

logging.basicConfig(format="%(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("freva-deployment")

RichConsole = Console(markup=True, force_terminal=True)

config_text = """
### This is the global config file for the freva deployment
[general]
[variables]
### you can set here different *global* variables that are
### evaluatated in the deployment configurations. For example
### if you set here the variable USER = "foo" then you can
### use the this defined variable in the inventory file to
### set the ansible user: anisble_user="${USER}"

# USER="myusername"
# USER_GROUP = "myusergroup"
"""

password_prompt = (
    "[green]Choose[/] a [b]master password[/], this password will be used to:\n"
    "- create the [magenta]mysql root[/] password\n"
    "- set the [magenta]django admin[/] web password\n"
    "[b]Note:[/] Ideally this password can be shared amongst other [i]admins[/].\n"
    "[b][green]choose[/] master password[/]"
)

ServiceInfo = NamedTuple(
    "ServiceInfo", [("name", str), ("python_path", str), ("hosts", str)]
)


class AssetDir:
    this_module = "freva_deployment"

    def __init__(self):
        self._user_asset_dir = Path(appdirs.user_data_dir()) / "freva" / "deployment"
        self._user_config_dir = Path(appdirs.user_config_dir()) / "freva" / "deployment"

    @property
    def _central_asset_dir(self):
        distribution = pkg_resources.get_distribution(self.this_module)
        try:
            records = distribution.get_metadata("RECORD").splitlines()
        except FileNotFoundError:
            asset_dir = Path(distribution.module_path).parent / "assets"
            if asset_dir.is_dir():
                return asset_dir
            warnings.warn("Guessing asset dir location, this might fail")
            return Path(sys.exec_prefix) / "share" / "freva" / "deployment"
        try:
            inventory = [f.partition(",")[0] for f in records if "inventory.toml" in f][
                0
            ]
        except IndexError:
            warnings.warn("Guessing asset dir location, this might fail")
            return Path(sys.exec_prefix) / "share" / "freva" / "deployment"
        asset_path = (Path(distribution.module_path) / inventory).parent.parent
        return Path.resolve(asset_path)

    @property
    def asset_dir(self):
        if self._user_asset_dir.exists():
            return self._user_asset_dir
        return self._central_asset_dir

    @property
    def config_dir(self):
        inventory_file = self._user_config_dir / "inventory.toml"
        if inventory_file.exists():
            return self._user_config_dir
        self._user_config_dir.mkdir(exist_ok=True, parents=True)
        shutil.copy(self.asset_dir / "config" / "inventory.toml", inventory_file)
        return self._user_config_dir

    @property
    def config_file(self):
        cfg_file = self.config_dir / "freva-deployment.config"
        if not cfg_file.exists():
            cfg_file.parent.mkdir(exist_ok=True, parents=True)
            with cfg_file.open("w", encoding="utf-8") as f_obj:
                f_obj.write(config_text)
        return cfg_file


AD = AssetDir()
asset_dir = AD.asset_dir
config_dir = AD.config_dir
config_file = AD.config_file


def get_current_file_dir(inp_dir: str | Path, value: str) -> str:
    """Get a path with the CFD as a variable."""
    if "${CFD}" in value.upper() or "$CFD" in value.upper():
        value = value.replace("${CFD}", "$CFD")
        part_1, _, part_2 = value.partition("$CFD/")
        return str(Path(inp_dir, *Path(part_2).parts))
    return value


def _convert_dict(
    inp_dict: dict[str, str | dict[str, Any]],
    variables: dict[str, str],
    cfd: Path,
) -> None:
    for key, value in inp_dict.items():
        if isinstance(value, dict):
            _convert_dict(value, variables, cfd)
        elif isinstance(value, str):
            for varn, variable in variables.items():
                if f"${{{varn}}}" in value or f"${varn}" in value:
                    value = value.replace(f"${{{varn}}}", f"${varn}")
                    value = value.replace(f"${varn}", variable)
            inp_dict[key] = get_current_file_dir(cfd, value)


def load_config(inp_file: str | Path) -> dict[str, Any]:
    """Load the inventory toml file and replace all environment variables."""
    inp_file = Path(inp_file).expanduser().absolute()
    variables = cast(dict[str, str], toml.loads(config_file.read_text())["variables"])
    config = toml.loads(inp_file.read_text())
    _convert_dict(config, variables, inp_file.parent)
    return config


def guess_map_server(
    inp_server: str | None, default_port: int = 6111, mandatory: bool = True
) -> str:
    """Try to get the server name mapping the freva infrastructure.

    Parameters
    ----------
    inp_server: str | None
        Input server name, if None given, the code tries to read the
        the server name from a previous deployment setup.
    default_port: int, default: 6111
        The port to connect to
    mandatory: bool, default: True
        If mandatory is set and no server could be found an error is risen.

    Returns
    -------
    str: hostname of the server that runs the server map service

    Raises
    ------
    ValueError: If no server could be found a ValueError is raised.
    """
    inp_server = inp_server or ""
    if inp_server:
        host_name, _, port = inp_server.partition(":")
        port = port or str(default_port)
        return f"{host_name}:{port}"
    cache_dir = Path(appdirs.user_cache_dir()) / "freva-deployment"
    try:
        with (cache_dir / "freva_deployment.json").open() as f_obj:
            inp_server = cast(str, json.load(f_obj)["server_map"])
            host_name, _, port = inp_server.partition(":")
            port = port or str(default_port)
            return f"{host_name}:{port}"
    except (
        FileNotFoundError,
        IOError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
    ):
        pass
    if mandatory:
        raise ValueError(
            "You have to set the hostname to the services mapping "
            "the freva infrastructure using the --server-map flag."
        )
    return ""


def set_log_level(verbosity: int) -> None:
    """Set the log level of the logger."""
    logger.setLevel(max(logging.INFO - 10 * verbosity, logging.DEBUG))


def get_setup_for_service(service: str, setups: list[ServiceInfo]) -> tuple[str, str]:
    """Get the setup of a service configuration."""
    for setup in setups:
        if setup.name == service:
            return setup.python_path, setup.hosts
    raise KeyError("Service not found")


def read_db_credentials(
    cert_file: Path, db_host: str, port: int = 5002
) -> dict[str, str]:
    """Read database config."""
    with cert_file.open() as f_obj:
        key = "".join([k.strip() for k in f_obj.readlines() if not k.startswith("-")])
        sha = hashlib.sha512(key.encode()).hexdigest()
    url = f"http://{db_host}:{port}/vault/data/{sha}"
    return requests.get(url).json()


def download_server_map(
    server_map,
) -> dict[str, list[ServiceInfo]]:
    """Download server information from the service that stores the server arch.

    Parameters
    ----------
    server_map: str,
        The hostname holding the server archtiecture information.
    Returns
    -------
    dict[str, list[NamedTuple("service", [("name", str), ("python_path", str),
                                     ("hosts", str)])]]
    """
    info: dict[str, list[ServiceInfo]] = {}
    host, _, port = server_map.partition(":")
    port = port or "6111"
    req = requests.get(f"http://{host}:{port}")
    if req.status_code != 200:
        logger.error(req.json())
        return {}
    for proj, conf in req.json().items():
        info[cast(str, proj)] = [
            ServiceInfo(name=s, python_path=c[0], hosts=c[-1])
            for (s, c) in conf.items()
        ]
    return info


def upload_server_map(
    server_map: str,
    project_name: str,
    deployment_setup: dict[str, dict[str, str]],
) -> None:
    """Upload server information to service that stores server archtiecture.

    Parameters
    ----------
    server_map: str
        The hostname holding the server archtiecture information.
    project_name: str
        Name of the freva project
    deployment_setup: dict[str, str]
        Server names for each deployed service
    """
    _upload_data: dict[str, dict[str, str]] = {}
    for service, config in deployment_setup.items():
        _upload_data[service] = config
    host, _, port = server_map.partition(":")
    port = port or "6111"
    req_data = dict(config=toml.dumps(_upload_data))
    logger.debug("Uploading %s", req_data)
    req = requests.put(f"http://{host}:{port}/{project_name}", data=req_data)
    if req.status_code == 201:
        logger.info("Server information updated at %s", host)
    else:
        logger.error("Could not update server information %s", req.json())


def get_email_credentials() -> tuple[str, str]:
    """Read login credentials for email server.

    Returns
    =======
    tuple: username and password
    """

    msg = (
        "\nThe web will need login credentials to connect to the [b green]mail server [/]"
        "that has been set up.\nYou should now enter your [it]login credentials[/].\n"
        "[b]Note:[/]These credentials will be securely stored in an encrypted vault\n"
    )
    RichConsole.print(msg)
    username = Prompt.ask("[green b]Username[/] for mail server")
    password = Prompt.ask("[green b]Password[/] for mail server", password=True)
    return username, password


def get_passwd(min_characters: int = 8) -> str:
    """Create a secure pasword.

    Parameters
    ==========
    min_characters:
        The minimum lenght of the password (default 8)

    Returns
    =======
    str: The password
    """
    logger.info("Creating Password")
    msg = ""
    RichConsole
    while True:
        try:
            return _create_passwd(min_characters, msg)
        except ValueError as e:
            RichConsole.print(f"[red]{e.__str__()}[/]")
            msg = "[b red]re-enter[/] master password"


def _create_passwd(min_characters: int, msg: str = "") -> str:
    """Create passwords."""
    master_pass = Prompt.ask(msg or password_prompt, password=True)
    is_ok: bool = len(master_pass) > min_characters
    for check in ("[a-z]", "[A-Z]", "[0-9]"):
        if not re.search(check, master_pass):
            is_ok = False
            break
    is_safe: bool = len([True for c in "[_@$#$%^&*-!]" if c in master_pass]) > 0
    if is_ok is False or is_safe is False:
        raise ValueError(
            (
                "Password must confirm the following constraints:\n"
                f"- {min_characters} alphanumeric characters long,\n"
                "- have both, lower and upper case characters,\n"
                "- have at least one special special character."
            )
        )
    master_pass_2 = Prompt.ask("[bold green]re-enter[/] master password", password=True)
    if master_pass != master_pass_2:
        raise ValueError("Passwords do not match")
    return master_pass
