"""Module to run the freva deployment."""

from __future__ import annotations

import json
import os
import random
import signal
import string
import sys
import time
from copy import deepcopy
from getpass import getuser
from io import StringIO
from pathlib import Path
from socket import gethostbyname, gethostname
from typing import Any, cast
from urllib.parse import urlparse

import tomlkit
import yaml
from ansible_runner import run
from ansible_runner.runner import Runner
from rich import print as pprint
from rich.console import Console
from rich.live import Live
from rich.prompt import Prompt
from rich.spinner import Spinner

from freva_deployment import FREVA_PYTHON_VERSION

from .error import ConfigurationError, DeploymentError, handled_exception
from .keys import RandomKeys
from .logger import logger
from .runner import RunnerDir
from .utils import (
    RichConsole,
    asset_dir,
    config_dir,
    get_email_credentials,
    get_passwd,
    load_config,
)
from .versions import get_steps_from_versions


class DeployFactory:
    """Apply freva deployment and its services.

    Parameters
    ----------
    project_name: str
        The name of the project to distinguish this instance from others.
    steps: list[str], default: ["core", "web", "freva_rest", "db"]
        The components that are going to be deployed.
    config_file: os.PathLike, default: None
        Path to any existing deployment configuration file.
    local_debug: bool, default: False
        Run deployment only on local machine, debug mode.
    gen_keys: bool, default: False
        Create new set of certificates, if they don't already exist.

    Examples
    --------

    >>> from freva_deployment import DeployFactory as DF
    >>> deploy = DF(steps=["freva_rest"])
    >>> deploy.play(ask_pass=True)
    """

    step_order: tuple[str, ...] = ("core", "db", "freva_rest", "web")
    _steps_with_cert: tuple[str, ...] = ("core", "db", "web")

    @handled_exception
    def __init__(
        self,
        steps: list[str] | None = None,
        config_file: Path | str | None = None,
        local_debug: bool = False,
        gen_keys: bool = False,
    ) -> None:
        self.gen_keys = gen_keys or local_debug
        self.local_debug = local_debug
        self._config_keys: list[str] = []
        self._master_pass: str = ""
        self.email_password: str = ""
        self._td: RunnerDir = RunnerDir()
        self.eval_conf_file: Path = self._td.parent_dir / "evaluation_system.conf"
        self.web_conf_file: Path = self._td.parent_dir / "freva_web.toml"
        self.apache_config: Path = self._td.parent_dir / "freva_web.conf"
        self._db_pass: str = ""
        self._steps = steps or ["db", "freva_rest", "web", "core"]
        if self._steps == ["auto"] or self._steps == "auto":
            self._steps = []
        self._inv_tmpl = Path(config_file or config_dir / "inventory.toml")
        self._cfg_tmpl = self.aux_dir / "evaluation_system.conf.tmpl"
        self.cfg = self._read_cfg()
        self.project_name = self.cfg.pop("project_name", None)
        self._random_key = RandomKeys(self.project_name or "freva")
        self.playbooks: dict[str, Path | None] = {}
        if not self.project_name:
            raise ConfigurationError("You must set a project name") from None
        self._set_hostnames()
        self.current_step = ""
        self._check_steps_()

    def _check_steps_(self) -> None:
        """Before we do anything check if something is wrong with the config."""
        # First the steps that are needed
        old_master = self._master_pass
        self._master_pass = old_master or "foo"
        not_in_use = set(["db", "freva_rest", "web", "core"]) - set(self.steps)
        # We temporary set the env variables for email user and email password
        # This is not pretty but prevents the password dialogs, which aren't
        # needed at this step to show up.
        # Later we will set everything back as it was.
        current_values = {}
        for key in ("EMAIL_USER", "EMAIL_PASSWD"):
            current_values[key] = os.environ.get(key, "")
            os.environ[key] = current_values[key] or "foo"
        for step in self.steps:
            getattr(self, f"_prep_{step.replace('-', '_')}")()
        for step in not_in_use:
            try:
                getattr(self, f"_prep_{step.replace('-', '_')}")()
            except ConfigurationError as error:
                logger.warning("Some of your config isn't valid:\n%s", error)
        for key, value in current_values.items():
            os.environ[key] = current_values[key]
        self._master_pass = old_master

    @property
    def master_pass(self) -> str:
        """Define the master password."""
        if self._master_pass:
            return self._master_pass
        self._master_pass = get_passwd(os.environ.get("MASTER_PASSWD", ""))
        return self._master_pass

    @property
    def public_key_file(self) -> str:
        """Path to the public certificate file."""
        public_keyfile = self.cfg["certificates"].get("public_keyfile")
        chain_keyfile = self.cfg["certificates"].get("chain_keyfile")
        if public_keyfile:
            return str(Path(public_keyfile).expanduser().absolute())
        if chain_keyfile:
            return str(Path(chain_keyfile).expanduser().absolute())
        if self.gen_keys:
            return self._random_key.public_chain_file
        raise ConfigurationError(
            "You must give a valid path to a public key file."
        ) from None

    @property
    def private_key_file(self) -> str:
        """Path to the private key file."""
        keyfile = self.cfg["certificates"].get("private_keyfile")
        if keyfile:
            return str(Path(keyfile).expanduser().absolute())
        if self.gen_keys:
            return self._random_key.private_key_file
        raise ConfigurationError(
            "You must give a valid path to a private key file."
        ) from None

    def _prep_vault(self) -> None:
        """Prepare the vault."""
        self.cfg["vault"]["config"].setdefault("ansible_become_user", "root")
        self.cfg["vault"]["config"].pop("db_playbook", "")
        self.cfg["vault"]["config"]["db_port"] = self.cfg["vault"]["config"].get(
            "port", 3306
        )
        self.cfg["vault"]["config"]["db_user"] = self.cfg["vault"]["config"].get(
            "user", ""
        )
        self.cfg["vault"]["config"]["root_passwd"] = self.master_pass
        self.cfg["vault"]["config"]["passwd"] = self.db_pass
        self.cfg["vault"]["config"]["keyfile"] = self.public_key_file
        self.cfg["vault"]["config"]["email"] = self.cfg["web"]["config"].get(
            "contacts", ""
        )
        self.cfg["vault"]["config"]["db_host"] = self.cfg["db"]["config"].get(
            "host", self.cfg["db"]["hosts"]
        )

    def _prep_db(self) -> None:
        """prepare the mariadb service."""
        self._config_keys.append("db")
        self.cfg["db"]["config"].setdefault("ansible_become_user", "root")
        host = self.cfg["db"]["hosts"]
        self.cfg["db"]["config"]["root_passwd"] = self.master_pass
        self.cfg["db"]["config"]["passwd"] = self.db_pass
        self.cfg["db"]["config"]["keyfile"] = self.public_key_file
        data_path = Path(
            cast(
                str,
                self.cfg["db"]["config"].get("data_path", "/opt/freva"),
            )
        )
        self.cfg["db"]["config"]["data_path"] = str(data_path)
        for key in ("name", "user", "db"):
            self.cfg["db"]["config"][key] = self.cfg["db"]["config"].get(key) or "freva"
        db_host = self.cfg["db"]["config"].get("host", "").strip()
        if not db_host:
            self.cfg["db"]["config"]["host"] = host
        self.cfg["db"]["config"].setdefault("port", "3306")
        self.cfg["db"]["config"]["email"] = self.cfg["web"]["config"].get(
            "contacts", ""
        )
        self.playbooks["db"] = self.cfg["db"]["config"].get("db_playbook")
        self._prep_vault()
        self._prep_web(False)

    def _prep_freva_rest(self, prep_web=True) -> None:
        """prepare the freva_rest service."""
        self._config_keys.append("freva_rest")
        self.cfg["freva_rest"]["config"].setdefault("ansible_become_user", "root")
        self.cfg["freva_rest"]["config"]["root_passwd"] = self.master_pass
        self.cfg["freva_rest"]["config"].pop("core", None)
        data_path = Path(
            cast(
                str,
                self.cfg["freva_rest"]["config"].get("data_path", "/opt/freva"),
            )
        )
        self.cfg["freva_rest"]["config"]["data_path"] = str(data_path)
        self.playbooks["freva_rest"] = self.cfg["freva_rest"]["config"].get(
            "freva_rest_playbook"
        )
        for key, default in dict(solr_mem="4g", freva_rest_port=7777).items():
            self.cfg["freva_rest"]["config"][key] = (
                self.cfg["freva_rest"]["config"].get(key) or default
            )
        self.cfg["freva_rest"]["config"]["email"] = self.cfg["web"]["config"].get(
            "contacts", ""
        )
        if prep_web:
            self._prep_web(False)

    def _prep_core(self) -> None:
        """prepare the core deployment."""
        self._config_keys.append("core")
        self.cfg["core"]["config"].setdefault("ansible_become_user", "")
        self.playbooks["core"] = self.cfg["core"]["config"].get("core_playbook")
        # Legacy args as we are going to use micromamba
        self.cfg["core"]["config"]["arch"] = (
            self.cfg["core"]["config"]
            .get("arch", "linux-64")
            .lower()
            .replace("x86_", "")
            .replace("mac", "")
        )
        self.cfg["core"]["config"]["python_version"] = FREVA_PYTHON_VERSION
        self.cfg["core"]["config"]["admins"] = (
            self.cfg["core"]["config"].get("admins") or getuser()
        )
        if not self.cfg["core"]["config"]["admins"]:
            self.cfg["core"]["config"]["admins"] = getuser()
        install_dir = Path(self.cfg["core"]["config"]["install_dir"])
        root_dir = Path(self.cfg["core"]["config"].get("root_dir", "") or install_dir)
        self.cfg["core"]["config"]["install_dir"] = str(install_dir)
        self.cfg["core"]["config"]["root_dir"] = str(root_dir)
        preview_path = self.cfg["core"]["config"].get("preview_path", "")
        base_dir_location = self.cfg["core"]["config"].get(
            "base_dir_location", ""
        ) or str(root_dir / "work")
        self.cfg["core"]["config"]["base_dir_location"] = base_dir_location
        scheduler_output_dir = self.cfg["core"]["config"].get(
            "scheduler_output_dir", ""
        )
        scheduler_system = self.cfg["core"]["config"].get("scheduler_system", "local")
        if not preview_path:
            self.cfg["core"]["config"]["preview_path"] = str(
                Path(base_dir_location) / "share" / "preview"
            )
        if not scheduler_output_dir:
            scheduler_output_dir = str(Path(base_dir_location) / "share")
        elif Path(scheduler_output_dir).parts[-1] != scheduler_system:
            scheduler_output_dir = Path(scheduler_output_dir) / scheduler_system
        self.cfg["core"]["config"]["scheduler_output_dir"] = str(scheduler_output_dir)
        self.cfg["core"]["config"]["keyfile"] = self.public_key_file
        git_exe = self.cfg["core"]["config"].get("git_path")
        self.cfg["core"]["config"]["git_path"] = git_exe or "git"
        self.cfg["core"]["config"][
            "git_url"
        ] = "https://github.com/FREVA-CLINT/freva.git"

    def _prep_web(self, ask_pass: bool = True) -> None:
        """prepare the web deployment."""
        self._config_keys.append("web")
        self.playbooks["web"] = self.cfg["web"]["config"].get("web_playbook")
        self.cfg["web"]["config"].setdefault("ansible_become_user", "root")
        self._prep_core()
        freva_rest_host = (
            f'{self.cfg["freva_rest"]["hosts"]}:'
            f'{self.cfg["freva_rest"]["config"]["freva_rest_port"]}'
        )
        self.cfg["web"]["config"]["freva_rest_host"] = freva_rest_host
        self.cfg["web"]["config"].setdefault("deploy_web_server", True)
        data_path = Path(
            cast(
                str,
                self.cfg["web"]["config"].get("data_path", "/opt/freva"),
            )
        )
        self.cfg["web"]["config"]["data_path"] = str(data_path)
        admin = self.cfg["core"]["config"]["admins"]
        try:
            for k, v in self.cfg["web"]["config"].items():
                self.cfg["web"]["config"].setdefault(k, "")
        except KeyError:
            raise ConfigurationError(
                "No web config section given, please configure the web.config"
            ) from None
        if not isinstance(admin, str):
            self.cfg["web"]["config"]["admin"] = admin[0]
        else:
            self.cfg["web"]["config"]["admin"] = admin
        allowed_hosts = self.cfg["web"]["config"].get("allowed_hosts") or ["localhost"]
        allowed_hosts.append(self.cfg["web"]["hosts"])
        allowed_hosts.append(f"{self.project_name}-httpd")
        self.cfg["web"]["config"]["allowed_hosts"] = list(set(allowed_hosts))
        self.cfg["web"]["config"].setdefault("allowed_hosts", ["localhost"])

        _webserver_items = {
            "institution_logo": self.cfg["web"]["config"].get("institution_logo", ""),
            "main_color": self.cfg["web"]["config"].get("main_color", "Tomato"),
            "border_color": self.cfg["web"]["config"].get("border_color", "#6c2e1f"),
            "hover_color": self.cfg["web"]["config"].get("hover_color", "#d0513a"),
            "homepage_text": self.cfg["web"]["config"].get("homepage_text", ""),
            "imprint": self.cfg["web"]["config"].get("imprint", []),
            "homepage_heading": self.cfg["web"]["config"].get("homepage_heading", ""),
            "about_us_text": self.cfg["web"]["config"].get("about_us_text", ""),
            "contacts": self.cfg["web"]["config"].get("contacts", []),
            "insitution_name": self.cfg["web"]["config"].get("insitution_name", ""),
            "menu_entries": self.cfg["web"]["config"].get("menu_entries", []),
        }
        try:
            with Path(_webserver_items["homepage_text"]).open("r") as f_obj:
                _webserver_items["homepage_text"] = f_obj.read()
        except (FileNotFoundError, IOError, KeyError):
            pass
        try:
            with Path(_webserver_items["about_us_text"]).open() as f_obj:
                _webserver_items["about_us_text"] = f_obj.read()
        except (FileNotFoundError, IOError, KeyError):
            pass
        with self.web_conf_file.open("w") as f_obj:
            tomlkit.dump(_webserver_items, f_obj)

        if self.local_debug:
            self.cfg["web"]["config"]["redis_host"] = self.cfg["web"]["hosts"]
        else:
            self.cfg["web"]["config"]["redis_host"] = f"{self.project_name}-redis"

        server_name = self.cfg["web"]["config"].pop("server_name", [])
        if isinstance(server_name, str):
            server_name = server_name.split(",")
        server_name = ",".join([a for a in server_name if a.strip()])
        if not server_name:
            server_name = self.cfg["web"]["hosts"]
        self.cfg["web"]["config"]["server_name"] = server_name
        web_host = self.cfg["web"]["hosts"]
        if web_host == "127.0.0.1":
            web_host = "localhost"
        self.cfg["web"]["config"]["host"] = web_host
        self.cfg["web"]["config"]["csrf_trusted_origins"] = []
        for url in (server_name, self.cfg["web"]["config"]["project_website"]):
            trusted_origin = urlparse(url)

            if trusted_origin.scheme:
                self.cfg["web"]["config"]["csrf_trusted_origins"].append(
                    f"https://{trusted_origin.netloc}"
                )
            else:
                self.cfg["web"]["config"]["csrf_trusted_origins"].append(
                    f"https://{trusted_origin.path}"
                )
        self.cfg["web"]["config"]["freva_bin"] = os.path.join(
            self.cfg["core"]["config"]["install_dir"], "bin"
        )
        for key in ("core", "web"):
            self.cfg[key]["config"]["config_toml_file"] = str(self.web_conf_file)
        self._prep_vault()
        if ask_pass:
            email_user, self.email_password = get_email_credentials()
            self.cfg["vault"]["config"]["email_user"] = email_user
            self.cfg["vault"]["config"]["email_password"] = self.email_password
        self.cfg["vault"]["config"]["ansible_python_interpreter"] = self.cfg["db"][
            "config"
        ].get("ansible_python_interpreter", "/usr/bin/python3")
        self.cfg["web"]["config"]["root_passwd"] = self.master_pass
        self.cfg["web"]["config"]["private_keyfile"] = self.private_key_file
        self.cfg["web"]["config"]["public_keyfile"] = self.public_key_file
        self.cfg["web"]["config"]["apache_config_file"] = str(self.apache_config)
        if ask_pass:
            self._prep_apache_config()

    def _prep_apache_config(self):
        with open(self.apache_config, "w") as f_obj:
            f_obj.write((Path(asset_dir) / "web" / "freva_web.conf").read_text())

    def _set_hostnames(self) -> None:
        """Set the hostnames from the config or if debug the alias."""
        default_ports = {"db": 3306, "freva_rest": 8080}
        if self.local_debug:
            for step in self.steps:
                if isinstance(self.cfg[step], dict) and "hosts" in self.cfg[step]:
                    self.cfg[step]["hosts"] = gethostbyname(gethostname())
                if step in ("db", "freva_rest"):
                    self.cfg[step]["config"]["port"] = default_ports[step]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._td.cleanup()

    def _read_cfg(self) -> dict[str, Any]:
        try:
            config = dict(load_config(self._inv_tmpl, convert=True).items())
            config["vault"] = deepcopy(config["db"])
            return config
        except FileNotFoundError:
            raise ConfigurationError(f"No such file {self._inv_tmpl}") from None
        except KeyError:
            raise ConfigurationError("You must define a db section") from None

    def _check_config(self) -> None:
        sections = []
        config_keys = deepcopy(self._config_keys)
        if "db" in config_keys:
            config_keys.append("vault")
        for section in self.cfg.keys():
            for step in config_keys:
                if section.startswith(step) and section not in sections:
                    sections.append(section)
        for section in sections:
            for key, value in self.cfg[section]["config"].items():
                if not value and not self._empty_ok and not isinstance(value, bool):
                    raise ConfigurationError(
                        f"{key} in {section} is empty in {self._inv_tmpl}"
                    ) from None

    @property
    def ask_become_password(self) -> bool:
        """Check if we have to ask for the sudo passwd at all."""
        cfg = deepcopy(self.cfg)
        solr_config = cfg.get("databrowser", cfg.get("solr", {}))
        cfg.setdefault("freva_rest", solr_config)
        for step in self.step_order:
            if cfg[step]["config"].get("ansible_become_user", "") or "root":
                return True
        return False

    @property
    def _empty_ok(self) -> list[str]:
        """Define all keys that can be empty."""
        return [
            "admins",
            "conda_exec_path",
            "ansible_become_user",
        ]

    def _get_files_copy(self, key) -> Path | None:
        return dict(
            core=self.eval_conf_file.absolute(),
            web=self.eval_conf_file.absolute(),
        ).get(key, None)

    @property
    def db_pass(self) -> str:
        """Create a password for the database."""
        if self._db_pass:
            return self._db_pass
        num_chars, num_digits = 30, 8
        num_chars -= num_digits
        characters = [
            "".join([random.choice(string.ascii_letters) for i in range(num_chars)]),
            "".join([random.choice(string.digits) for i in range(num_digits)]),
        ]
        str_characters = "".join(characters)
        _db_pass = "".join(random.sample(str_characters, len(str_characters)))
        while _db_pass.startswith("@"):
            # Vault treats values starting with "@" as file names.
            _db_pass = "".join(random.sample(str_characters, len(str_characters)))
        self._db_pass = _db_pass
        return self._db_pass

    @property
    def _needs_core(self) -> list[str]:
        """Define the steps that need the core config."""
        return ["web", "core"]

    def _set_additional_config_values(
        self,
        step: str,
        config: dict[str, dict[str, dict[str, str | int | bool]]],
    ) -> None:
        """Set additional values to the configuration."""
        if step in self._needs_core:
            for key in (
                "root_dir",
                "base_dir_location",
                "preview_path",
                "scheduler_output_dir",
            ):
                value = self.cfg["core"]["config"].get(key, "")
                config[step]["vars"][f"core_{key}"] = value
        config[step]["vars"][f"{step}_hostname"] = self.cfg[step]["hosts"]
        config[step]["vars"][f"{step}_name"] = f"{self.project_name}-{step}"
        config[step]["vars"]["asset_dir"] = str(asset_dir)
        config[step]["vars"]["ansible_user"] = (
            self.cfg[step]["config"].get("ansible_user") or getuser()
        )
        config[step]["vars"][f"{step}_ansible_python_interpreter"] = (
            self.cfg[step]["config"].get("ansible_python_interpreter")
            or "/usr/bin/python3"
        )
        dump_file = self._get_files_copy(step)
        if dump_file:
            config[step]["vars"][f"{step}_dump"] = str(dump_file)

    def parse_config(self, steps: list[str]) -> str | None:
        """Create config files for anisble and evaluation_system.conf."""
        versions = json.loads((Path(__file__).parent / "versions.json").read_text())
        additional_steps = set(steps) - set(self.steps)
        if additional_steps:
            pprint(
                "The following, [b]not selected[/b] steps will be auto "
                f"updated.\n[green]{', '.join(additional_steps)}[/]"
            )
            time.sleep(3)
        new_steps = set(steps + self.steps)
        if not new_steps:
            return None
        self._steps = list(new_steps)
        playbook = self.create_playbooks()
        logger.info("Parsing configurations")
        self._check_config()
        config: dict[str, dict[str, dict[str, str | int | bool]]] = {}
        info: dict[str, dict[str, dict[str, str | int | bool]]] = {}
        config_keys = deepcopy(self._config_keys)
        if "db" in config_keys:
            config_keys.append("vault")
        for step in set(config_keys):
            config[step], info[step] = {}, {}
            config[step]["hosts"] = self.cfg[step]["hosts"]
            info[step]["hosts"] = self.cfg[step]["hosts"]
            config[step]["vars"], info[step]["vars"] = {}, {}
            for key, value in self.cfg[step]["config"].items():
                if key in ("root_passwd",) or key.startswith(step):
                    new_key = key
                else:
                    new_key = f"{step.replace('-', '_')}_{key}"
                config[step]["vars"][new_key] = value
            config[step]["vars"]["project_name"] = self.project_name
            config[step]["vars"][f"{step.replace('-', '_')}_version"] = versions.get(
                step, ""
            )
            config[step]["vars"]["debug"] = self.local_debug
            # Add additional keys
            self._set_additional_config_values(step, config)
        if "freva_rest" in config:
            config["freva_rest"]["vars"]["solr_version"] = versions["solr"]
        for step in info:
            for key, value in config[step]["vars"].items():
                if (
                    f"{{{{{key}}}}}" in playbook
                    or f"{{{{ {key} }}}}" in playbook
                    or key == "debug"
                ):
                    info[step]["vars"][key] = value
        info_str = yaml.dump(json.loads(json.dumps(info)))
        for passwd in (self.email_password, self.master_pass):
            if passwd:
                info_str = info_str.replace(passwd, "***")
        RichConsole.print(info_str, style="bold", markup=True)
        return yaml.dump(json.loads(json.dumps(config)))

    @property
    def python_prefix(self) -> Path:
        """Get the path of the new conda evnironment."""
        return Path(sys.exec_prefix) / "bin" / "python3"

    @property
    def aux_dir(self) -> Path:
        """Directory with auxillary files."""
        return asset_dir / "config"

    @property
    def playbook_dir(self) -> Path:
        """The location of all playbooks."""
        return asset_dir / "playbooks"

    @property
    def steps(self) -> list[str]:
        """Set all the deployment steps."""
        steps = []
        for step in self._steps:
            steps.append(step)
            if step == "db" and "vault" not in steps:
                steps.append("vault")
        return [s for s in self.step_order if s in steps]

    def create_playbooks(self) -> str:
        """Create the ansible playbook form all steps."""
        logger.info("Creating Ansible playbooks")
        playbook = []
        self.current_step = "foo"
        _ = [getattr(self, f"_prep_{step}")() for step in self.steps]
        for step in self.steps:
            playbook_file = (
                self.playbooks.get(step)
                or self.playbook_dir / f"{step}-server-playbook.yml"
            )
            with Path(playbook_file).open(encoding="utf-8") as f_obj:
                playbook += yaml.safe_load(f_obj)
        return self._td.create_playbook(playbook)

    def create_eval_config(self) -> None:
        """Create and dump the evaluation_system.config."""
        logger.info("Creating evaluation_system.conf")
        keys = (
            ("core", "admins"),
            ("web", "project_website"),
            ("core", "root_dir"),
            ("core", "base_dir_location"),
            ("core", "preview_path"),
            ("core", "scheduler_output_dir"),
            ("core", "scheduler_system"),
        )
        cfg_file = asset_dir / "config" / "evaluation_system.conf.tmpl"
        with cfg_file.open() as f_obj:
            lines = f_obj.readlines()
            for num, line in enumerate(lines):
                if line.startswith("project_name"):
                    lines[num] = f"project_name={self.project_name}\n"
                for key, value in keys:
                    if line.startswith(value):
                        cfg = self.cfg[key]["config"].get(value, "")
                        if cfg:
                            lines[num] = f"{value}={cfg}\n"
                for step in ("freva_rest", "db"):
                    cfg = self.cfg[step]["config"].get("port", "")
                    if line.startswith(f"{step}.port"):
                        lines[num] = f"{step}.port={cfg}\n"
                    if line.startswith(f"{step}.host"):
                        lines[num] = f"{step}.host={self.cfg[step]['hosts']}\n"
                if line.startswith("solr.host"):
                    lines[num] = f"solr.host={self.cfg[step]['hosts']}\n"
                if line.startswith("db.host"):
                    lines[num] = f"db.host={self.cfg['db']['config']['host']}\n"
        dump_file = self._get_files_copy("core")
        if dump_file:
            with dump_file.open("w") as f_obj:
                f_obj.write("".join(lines))

    def get_ansible_password(self, ask_pass: bool = False) -> dict[str, str]:
        """The passwords for the ansible environments."""
        ssh_pass_msg = "Give the [b]ssh[/b] password for remote login"
        sudo_pass_msg = "Give the password elevating user privilege ([b]sudo[/b])"
        if ask_pass:
            sudo_pass_msg += ", defaults to ssh password"
        passwords = {}
        sudo_key = "^BECOME password.*:\\s*?$"
        ssh_key = "^SSH password:\\s*?$"
        passwords[sudo_key] = os.environ.get("ANSIBLE_BECOME_PASSWORD", "") or ""
        passwords[ssh_key] = os.environ.get("ANSIBLE_SSH_PASSWORD", "") or ""
        if ask_pass and not passwords[ssh_key]:
            passwords[ssh_key] = Prompt.ask(
                f"[green]{ssh_pass_msg}[/green]", password=True
            )
        if not passwords[sudo_key] and self.ask_become_password:
            passwords[sudo_key] = Prompt.ask(
                f"[green]{sudo_pass_msg}[/green]", password=True
            )
            if not passwords[sudo_key]:
                passwords[sudo_key] = passwords.get(ssh_key, "")
        return passwords

    @handled_exception
    def play(
        self, ask_pass: bool = True, verbosity: int = 0, ssh_port: int = 22
    ) -> Runner | None:
        """Play the ansible playbook.

        Parameters
        ----------
        ask_pass: bool, default: True
            Instruct Ansible to ask for the ssh password instead of using a
            ssh key
        verbosity: int, default: 0
            Verbosity level, default 0
        ssh_port: int, default: 22
            Set the ssh port, in 99.9% of cases this should be left at port 22
        """
        try:
            return self._play(ask_pass=ask_pass, verbosity=verbosity, ssh_port=ssh_port)
        except KeyboardInterrupt:
            pprint(" [red][ERROR]: User interrupted execution[/]", file=sys.stderr)
            raise KeyboardInterrupt() from None

    def get_steps_from_versions(
        self,
        envvars: dict[str, str],
        extravars: dict[str, str | int],
        cmdline: str,
        passwords: dict[str, str],
        verbosity: int,
    ) -> list[str]:
        """Check the versions of the different freva parts."""
        config: dict[str, dict[str, dict[str, str | int | bool]]] = {}
        steps = set(self.step_order) - set(self.steps)
        if not steps or self.local_debug:
            # The user has selected all steps anyway, nothing to do here:
            return []
        cfg = deepcopy(self.cfg)
        if cfg.get("freva_rest") is None:
            cfg["freva_rest"] = cfg.get("databrowser", cfg.get("solr", {}))
        for step in steps:
            config[step] = {}
            config[step]["hosts"] = cfg[step]["hosts"]
            if "ansible_become_user" not in cfg[step]["config"]:
                become_user = "root"
            else:
                become_user = cfg[step]["config"]["ansible_become_user"]
            config[step]["vars"] = {
                f"{step}_ansible_become_user": become_user,
                "asset_dir": str(asset_dir),
                f"{step}_ansible_user": cfg[step]["config"].get(
                    "ansible_user", getuser()
                ),
            }
        config.setdefault("core", {})
        config["core"].setdefault("vars", {})
        config["core"]["vars"]["core_install_dir"] = cfg["core"]["config"][
            "install_dir"
        ]
        stdout = sys.stdout
        buffer = StringIO()
        sig_handler = signal.getsignal(signal.SIGINT)
        text = "Getting versions of micro-services ..."
        spinner = Spinner("weather", text=text)
        status_text = {
            "successful": " [green]ok[/green]",
            "canceled": " [yellow]canceled[/yellow]",
            "failed": " [red]failed[/red]",
        }
        with Live(spinner, refresh_per_second=3, console=Console(stderr=True)):
            extravars["forks"] = 4
            try:
                sys.stdout = buffer
                sys.stdout.write("\n")
                event = run(
                    playbook=str(asset_dir / "playbooks" / "versions.yaml"),
                    inventory=config,
                    envvars=envvars,
                    passwords=passwords,
                    extravars=extravars,
                    cmdline=cmdline,
                    verbosity=verbosity,
                    forks=4,
                )
            finally:
                sys.stdout = stdout
                signal.signal(signal.SIGINT, sig_handler)
            spinner.update(
                text=text + status_text.get(event.status, " [red]failed[/red]")
            )

        if event.status not in ["successful", "canceled"]:
            raise DeploymentError(buffer.getvalue()) from None
        if event.status == "canceled":
            raise KeyboardInterrupt() from None
        if verbosity > 0:
            print(buffer.getvalue())
        versions = {}
        for res in event.events:
            msg = res.get("event_data", {}).get("res", {}).get("msg")
            title = res.get("event_data", {}).get("task", "").lower()
            if msg is not None and title.startswith("display"):
                service = res.get("event_data", {}).get("task", "").split()[1]
                versions[service] = msg.strip()
        additional_steps = get_steps_from_versions(versions)
        return additional_steps

    def _play(
        self,
        ask_pass: bool = True,
        verbosity: int = 0,
        ssh_port: int = 22,
    ) -> Runner | None:
        """Play the ansible playbook.

        Parameters
        ----------
        ask_pass: bool, default: True
            Instruct Ansible to ask for the ssh password instead of using a
            ssh key
        verbosity: int, default: 0
            Verbosity level, default 0
        ssh_port: int, default: 22
            Set the ssh port, in 99.9% of cases this should be left at port 22
        """
        envvars: dict[str, str] = {
            "ANSIBLE_STDOUT_CALLBACK": "yaml",
            "ANSIBLE_CONFIG": self._td.ansible_config_file,
        }
        extravars: dict[str, str | int] = {
            "ansible_port": ssh_port,
            "ansible_ssh_args": "-o ForwardX11=no",
        }
        if self.local_debug:
            extravars["ansible_connection"] = "local"

        cmdline = "--ask-become"
        if ask_pass:
            cmdline += " --ask-pass"
        passwords = self.get_ansible_password(ask_pass)
        steps = self.get_steps_from_versions(
            envvars.copy(),
            extravars.copy(),
            cmdline,
            passwords.copy(),
            verbosity,
        )
        inventory = self.parse_config(steps)
        if inventory is None:
            logger.info("Services up to date, nothing to do!")
            return None
        self.create_eval_config()
        logger.debug(inventory)
        logger.info("Playing the playbooks for %s with ansible", ", ".join(self.steps))
        logger.debug(self.playbooks)
        time.sleep(3)
        sig_handler = signal.getsignal(signal.SIGINT)
        try:
            result = run(
                private_data_dir=str(self._td.parent_dir),
                playbook=str(self._td.playbook_file),
                inventory=inventory,
                envvars=envvars,
                passwords=passwords,
                extravars=extravars,
                cmdline=cmdline,
                verbosity=verbosity,
            )
        finally:
            signal.signal(signal.SIGINT, sig_handler)
        if result.status in ("timeout", "failed"):
            raise DeploymentError(f"Deployment not successful: {result.status}")
        elif result.status == "canceled":
            raise KeyboardInterrupt() from None
        return result
