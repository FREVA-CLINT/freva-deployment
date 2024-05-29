"""Collection of utils for deployment."""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import sys
import sysconfig
from pathlib import Path
from typing import Any, Dict, MutableMapping, NamedTuple, Optional, Union, cast

import appdirs
import requests
import tomlkit
from rich.console import Console
from rich.prompt import Prompt

from .error import ConfigurationError
from .logger import logger

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
    "- set the [magenta]mongo db[/] user password\n"
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

    @staticmethod
    def get_dirs(user: bool = True, key: str = "data") -> Path:
        """Get the 'scripts' and 'purelib' directories we'll install into.

        This is now a thin wrapper around sysconfig.get_paths(). It's not inlined,
        because some tests mock it out to install to a different location.
        """

        if user:
            if (sys.platform == "darwin") and sysconfig.get_config_var(
                "PYTHONFRAMEWORK"
            ):
                return Path(sysconfig.get_paths("osx_framework_user")[key])
            return Path(sysconfig.get_paths(os.name + "_user")[key])
        # The default scheme is 'posix_prefix' or 'nt', and should work for e.g.
        # installing into a virtualenv
        return Path(sysconfig.get_paths()[key])

    @property
    def asset_dir(self) -> Path:
        data_dir = self.get_dirs(False) / "share" / "freva" / "deployment"
        user_dir = self.get_dirs(True) / "share" / "freva" / "deployment"
        for path in (data_dir, user_dir):
            if path.is_dir():
                return path
        raise ConfigurationError(
            "Could not find asset dir, please consider reinstalling the package."
        )

    @property
    def inventory_file(self) -> Path:
        return self.asset_dir / "config" / "inventory.toml"

    @property
    def config_dir(self):
        inventory_file = self._user_config_dir / "inventory.toml"
        if inventory_file.exists():
            return self.asset_dir
        inventory_file.parent.mkdir(exist_ok=True, parents=True)
        try:
            inventory_file.unlink()
        except FileNotFoundError:
            pass
        shutil.copy2(self.asset_dir / "config" / "inventory.toml", inventory_file)
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


def _update_config(
    new_config: MutableMapping[str, Any], old_config: MutableMapping[str, Any]
) -> None:
    for key, value in old_config.items():
        if key in new_config and isinstance(value, dict):
            _update_config(new_config[key], old_config[key])
        else:
            new_config[key] = value


def _create_new_config(inp_file: Path) -> Path:
    """Update any old configuration file to a newer version."""
    config = cast(
        Dict[str, Dict[str, Dict[str, Union[str, float, int, bool]]]],
        tomlkit.loads(inp_file.read_text()),
    )
    create_backup = False
    config_tmpl = tomlkit.loads(AD.inventory_file.read_text())
    # Legacy solr:
    if "solr" in config or "databrowser" in config:
        create_backup = True
        if "solr" in config:
            config["freva_rest"] = config.pop("solr")
            for key in ("port", "mem"):
                if key in config["freva_rest"]["config"]:
                    config["freva_rest"]["config"][f"solr_{key}"] = config[
                        "freva_rest"
                    ]["config"].pop(key)
        else:
            config["freva_rest"] = config.pop("databrowser")
            config["freva_rest"]["config"]["freva_rest_port"] = config["freva_rest"][
                "config"
            ].pop("databrowser_port", "")
            config["freva_rest"]["config"]["freva_rest_playbook"] = config[
                "freva_rest"
            ]["config"].pop("databrowser_playbook", "")
    if create_backup:
        backup_file = inp_file.with_suffix(inp_file.suffix + ".bck")
        logger.info(
            "Updating config file, original config can be found in %s",
            backup_file,
        )
        backup_file.write_text(inp_file.read_text())
        _update_config(config_tmpl, config)
        inp_file.write_text(tomlkit.dumps(config_tmpl))
    return inp_file


def load_config(inp_file: str | Path, convert: bool = False) -> dict[str, Any]:
    """Load the inventory toml file and replace all environment variables."""
    inp_file = _create_new_config(Path(inp_file).expanduser().absolute())
    variables = cast(
        dict[str, str], tomlkit.loads(config_file.read_text())["variables"]
    )
    config = tomlkit.loads(inp_file.read_text())
    if convert:
        _convert_dict(config, variables, inp_file.parent)
    return config


def get_setup_for_service(service: str, setups: list[ServiceInfo]) -> tuple[str, str]:
    """Get the setup of a service configuration."""
    for setup in setups:
        if setup.name == service:
            return setup.python_path, setup.hosts
    raise ConfigurationError("Service not found")


def read_db_credentials(
    cert_file: Path, db_host: str, port: int = 5002
) -> dict[str, str]:
    """Read database config."""
    with cert_file.open() as f_obj:
        key = "".join([k.strip() for k in f_obj.readlines() if not k.startswith("-")])
        sha = hashlib.sha512(key.encode()).hexdigest()
    url = f"http://{db_host}:{port}/vault/data/{sha}"
    return requests.get(url).json()


def get_email_credentials() -> tuple[str, str]:
    """Read login credentials for email server.

    Returns
    =======
    tuple: username and password
    """
    username: str = os.environ.get("EMAIL_USER", "") or ""
    password: str = os.environ.get("EMAIL_PASSWD", "") or ""
    msg = (
        "\nThe web will need login credentials to connect to the [b green]mail server [/]"
        "that has been set up.\nYou should now enter your [it]login credentials[/].\n"
        "[b]Note:[/]These credentials will be securely stored in an encrypted vault\n"
    )
    if not username or not password:
        RichConsole.print(msg)
        if not username:
            username = Prompt.ask("[green b]Username[/] for mail server")
        if not password:
            password = Prompt.ask("[green b]Password[/] for mail server", password=True)
    return username, password


def get_passwd(master_pass: Optional[str] = None, min_characters: int = 8) -> str:
    """Create a secure pasword.

    Parameters
    ==========
    min_characters:
        The minimum lenght of the password (default 8)

    Returns
    =======
    str: The password
    """
    logger.debug("Creating Password")
    msg = ""
    while True:
        try:
            if master_pass:
                return _passwd_is_good(master_pass, min_characters)
            return _create_passwd(min_characters, msg)
        except ValueError as e:
            RichConsole.print(f"[red]{e}[/]")
            msg = "[b red]re-enter[/] master password"
            master_pass = ""


def _passwd_is_good(master_pass: str, min_characters: int) -> str:

    is_ok: bool = len(master_pass) > min_characters
    for check in ("[a-z]", "[A-Z]", "[0-9]"):
        if not re.search(check, master_pass):
            is_ok = False
            break
    forbidden_characters = ":/?#[]@%"
    is_ok = is_ok and len([True for c in "[_$^&*-!]" if c in master_pass]) > 0
    for character in forbidden_characters:
        if character in master_pass:
            is_ok = False
            break
    if not is_ok:
        raise ValueError(
            (
                "Password must confirm the following constraints:\n"
                f"- {min_characters} alphanumeric characters long,\n"
                "- have both, lower and upper case characters,\n"
                "- have at least one special special character.\n"
                f"- must *not* not contain: {forbidden_characters}"
            )
        )
    return master_pass


def _create_passwd(min_characters: int, msg: str = "") -> str:
    """Create passwords."""
    master_pass = Prompt.ask(msg or password_prompt, password=True)
    _passwd_is_good(master_pass, min_characters)
    master_pass_2 = Prompt.ask("[bold green]re-enter[/] master password", password=True)
    if master_pass != master_pass_2:
        raise ValueError("Passwords do not match")
    return master_pass
