"""Module to run the freva deployment."""
from __future__ import annotations
from getpass import getuser
import os
from pathlib import Path
import random
import shlex
import string
from subprocess import run
import sys
from tempfile import TemporaryDirectory, mkdtemp
from typing import Any

from rich.console import Console
from numpy import sign
import toml
import yaml

from .utils import (
    asset_dir,
    config_dir,
    create_self_signed_cert,
    get_passwd,
    logger,
    upload_server_map,
)


class DeployFactory:
    """Apply freva deployment and its services.

    Parameters
    ----------
    project_name: str
        The name of the project to distinguish this instance from others.
    steps: list[str], default: ["services", "core", "web"]
        The components that are going to be deployed.
    cert_file: os.PathLike, default: None
        The path to the public cert file that is injected to the web container.
    config_file: os.PathLike, default: None
        Path to any existing deployment configuration file.
    wipe: bool, default: False
        Delete any existing deployment resources, such as docker volumes.

    Examples
    --------

    >>> from freva_deployment import DeployFactory as DF
    >>> deploy = DF("xces", steps=["solr"], ask_pass=True)
    >>> deploy.play()
    """

    step_order: tuple[str, ...] = ("db", "vault", "solr", "core", "web")
    _steps_with_cert: tuple[str, ...] = ("db", "vault", "core", "web")

    def __init__(
        self,
        project_name: str,
        steps: list[str] | None = None,
        cert_file: str | None = None,
        config_file: Path | str | None = None,
        wipe: bool = False,
    ) -> None:

        self._config_keys: list[str] = []
        self.master_pass: str = ""
        self._td: TemporaryDirectory = TemporaryDirectory(prefix="inventory")
        self.inventory_file: Path = Path(self._td.name) / "inventory.yaml"
        self.eval_conf_file: Path = Path(self._td.name) / "evaluation_system.conf"
        self.web_conf_file: Path = Path(self._td.name) / "freva_web.toml"
        self._db_pass: str = ""
        self.project_name = project_name
        self._steps = steps or ["services", "core", "web"]
        self.wipe = wipe
        self._cert_file = cert_file or ""
        self._inv_tmpl = Path(config_file or config_dir / "inventory.toml")
        self._cfg_tmpl = self.aux_dir / "evaluation_system.conf.tmpl"
        self.cfg = self._read_cfg()

    @property
    def private_key_file(self) -> str:
        """Path to the private certifcate file."""
        return str(Path(self.public_key_file).with_suffix(".key"))

    @property
    def public_key_file(self) -> str:
        """Path to the public certificate file."""
        if not any((step in self._steps_with_cert for step in self.steps)):
            return str(Path(mkdtemp(suffix=".crt")))
        if not self._cert_file:
            _cert_file = config_dir / "keys" / f"{self.project_name}.crt"
        _cert_file = Path(self._cert_file or _cert_file)
        if not _cert_file.is_file():
            logger.warning("Certificate file does not exist, creating new one")
            _cert_file = create_self_signed_cert(_cert_file)
        return str(_cert_file.absolute())

    def _prep_vault(self) -> None:
        """Prepare the vault."""
        self._config_keys.append("vault")
        self.cfg["vault"] = self.cfg["db"].copy()
        if not self.master_pass:
            self.master_pass = get_passwd()
        self.cfg["vault"]["config"]["root_passwd"] = self.master_pass
        self.cfg["vault"]["config"]["passwd"] = self.db_pass
        self.cfg["vault"]["config"]["keyfile"] = self.public_key_file
        self.cfg["vault"]["config"]["private_keyfile"] = self.private_key_file

    def _prep_db(self) -> None:
        """prepare the mariadb service."""
        self._config_keys.append("db")
        if not self.master_pass:
            self.master_pass = get_passwd()
        host = self.cfg["db"]["hosts"]
        self.cfg["db"]["config"]["root_passwd"] = self.master_pass
        self.cfg["db"]["config"]["passwd"] = self.db_pass
        self.cfg["db"]["config"]["keyfile"] = self.public_key_file
        self.cfg["db"]["config"]["private_keyfile"] = self.private_key_file
        for key in ("name", "user", "db"):
            self.cfg["db"]["config"].setdefault(key, "freva")
        db_host = self.cfg["db"]["config"].get("host", "")
        if not db_host:
            self.cfg["db"]["config"]["host"] = host
        self.cfg["db"]["config"].setdefault("port", "3306")
        self._prep_vault()
        self._create_sql_dump()

    def _prep_solr(self) -> None:
        """prepare the apache solr service."""
        self._config_keys.append("solr")
        for key, default in dict(core="files", mem="4g", port=8983).items():
            self.cfg["solr"]["config"].setdefault(key, default)

    def _prep_core(self) -> None:
        """prepare the core deployment."""
        self._config_keys.append("core")
        self.cfg["core"]["config"].setdefault("admins", getuser())
        if not self.cfg["core"]["config"]["admins"]:
            self.cfg["core"]["config"]["admins"] = getuser()
        self.cfg["core"]["config"].setdefault("branch", "freva-dev")
        install_dir = self.cfg["core"]["config"]["install_dir"]
        root_dir = self.cfg["core"]["config"].get("root_dir", "")
        if not root_dir:
            self.cfg["core"]["config"]["root_dir"] = install_dir
        self.cfg["core"]["config"]["keyfile"] = self.public_key_file
        self.cfg["core"]["config"]["private_keyfile"] = self.private_key_file
        self.cfg["core"]["config"].setdefault("git_path", "git")

    def _prep_web(self) -> None:
        """prepare the web deployment."""
        self._config_keys.append("web")
        self.cfg["web"]["config"].setdefault("branch", "master")
        self._prep_core()
        admin = self.cfg["core"]["config"]["admins"]
        if not isinstance(admin, str):
            self.cfg["web"]["config"]["admin"] = admin[0]
        else:
            self.cfg["web"]["config"]["admin"] = admin
        _webserver_items = {}
        try:
            _webserver_items = {
                k.replace("web_", "").upper(): v
                for (k, v) in self.cfg["web"]["config"].items()
            }
        except KeyError as error:
            raise KeyError(
                "No web config section given, please configure the web.config"
            ) from error
        try:
            with Path(_webserver_items["homepage_text"]).open("r") as f_obj:
                _webserver_items["homepage_text"] = f_obj.read()
        except (FileNotFoundError, IOError, KeyError):
            pass
        logo = Path(self.cfg["web"]["config"].get("institution_logo", ""))
        alias = self.cfg["web"]["config"].pop("server_alias", [])
        if isinstance(alias, str):
            alias = alias.split(",")
        alias = ",".join([a for a in alias if a.strip()])
        if not alias:
            alias = self.cfg["web"]["hosts"]
        self.cfg["web"]["config"]["server_alias"] = alias
        web_host = self.cfg["web"]["hosts"]
        if web_host == "127.0.0.1":
            web_host = "localhost"
        self.cfg["web"]["config"]["host"] = web_host
        _webserver_items["INSTITUTION_LOGO"] = f"logo{logo.suffix}"
        try:
            with Path(_webserver_items["ABOUT_US_TEXT"]).open() as f_obj:
                _webserver_items["ABOUT_US_TEXT"] = f_obj.read()
        except (FileNotFoundError, IOError, KeyError):
            pass
        try:
            _webserver_items["IMPRINT"] = _webserver_items["ADDRESS"].split(",")
        except AttributeError:
            pass
        with self.web_conf_file.open("w") as f_obj:
            toml.dump(_webserver_items, f_obj)
        for key in ("core", "web"):
            logo_suffix = logo.suffix or ".png"
            self.cfg[key]["config"]["config_toml_file"] = str(self.web_conf_file)
            self.cfg[key]["config"]["institution_logo"] = str(logo.absolute())
            self.cfg[key]["config"]["institution_logo_suffix"] = logo_suffix
        if not self.master_pass:
            self.master_pass = get_passwd()
        self.cfg["web"]["config"]["root_passwd"] = self.master_pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._td.cleanup()

    def _read_cfg(self) -> dict[str, Any]:
        try:
            with self._inv_tmpl.open() as f_obj:
                return dict(toml.load(f_obj))
        except FileNotFoundError as error:
            raise FileNotFoundError(f"No such file {self._inv_tmpl}") from error

    @property
    def git_url(self) -> str:
        """Get the url of the git repository."""
        try:
            return self.cfg["coreservers:vars"]["git_url"]
        except KeyError as error:
            raise KeyError(
                (
                    "You must set git_url and branch keys in coreservers:vars in "
                    "the inventory file"
                )
            ) from error

    @property
    def git_branch(self) -> str:
        """Get the branch that is installed."""
        try:
            return self.cfg["coreservers:vars"]["branch"]
        except KeyError:
            return "main"

    def _add_local_config(self, config):
        if "db" not in self.steps:
            return {}
        cfg = dict(
            local=dict(
                hosts="127.0.0.1",
                vars=dict(
                    db_db=config["db_db"],
                    db_passwd=self.db_pass,
                    db_host=config["db_host"],
                    db_dump=str(self._dump_file),
                    db_port=config.get("db_port", 3306),
                    user=getuser(),
                    local_ansible_python_interpreter=str(self.python_prefix),
                ),
            )
        )
        return cfg

    def _check_config(self) -> None:
        sections = []
        for section in self.cfg.keys():
            for step in self._config_keys:
                if section.startswith(step) and section not in sections:
                    sections.append(section)
        for section in sections:
            for key, value in self.cfg[section]["config"].items():
                if not value and not self._empty_ok and not isinstance(value, bool):
                    raise ValueError(f"{key} in {section} is empty in {self._inv_tmpl}")

    @property
    def _empty_ok(self) -> list[str]:
        """Define all keys that can be empty."""
        return [
            "admins",
            "conda_exec_path",
        ]

    def _get_files_copy(self, key) -> Path | None:
        return dict(
            db=self._dump_file,
            solr=(self.aux_dir / "managed-schema").absolute(),
            core=self.eval_conf_file.absolute(),
            web=self.eval_conf_file.absolute(),
        ).get(key, None)

    @property
    def db_pass(self) -> str:
        """Create a password for the database."""
        if self._db_pass:
            return self._db_pass
        punctuations = "!@$^&*()_+-;:|,.%"
        num_chars, num_digits, num_punctuations = 20, 4, 4
        num_chars -= num_digits + num_punctuations
        characters = [
            "".join([random.choice(string.ascii_letters) for i in range(num_chars)]),
            "".join([random.choice(string.digits) for i in range(num_digits)]),
            "".join([random.choice(punctuations) for i in range(num_punctuations)]),
        ]
        str_characters = "".join(characters)
        self._db_pass = "".join(random.sample(str_characters, len(str_characters)))
        return self._db_pass

    @property
    def _needs_core(self) -> list[str]:
        """Define the steps that need the core config."""
        return ["web", "core"]

    def _set_additional_config_values(
        self, step: str, config: dict[str, dict[str, dict[str, str | int | bool]]]
    ) -> None:
        """Set additional values to the configuration."""
        if step in self._needs_core:
            for key in ("git_url", "branch", "root_dir"):
                value = self.cfg["core"]["config"][key]
                config[step]["vars"][f"core_{key}"] = value
        config[step]["vars"][f"{step}_hostname"] = self.cfg[step]["hosts"]
        config[step]["vars"][f"{step}_name"] = f"{self.project_name}-{step}"
        config[step]["vars"]["asset_dir"] = str(asset_dir)
        config[step]["vars"]["ansible_user"] = self.cfg[step]["config"].get(
            "ansible_user", getuser()
        )
        config[step]["vars"]["wipe"] = self.wipe
        config[step]["vars"][f"{step}_ansible_python_interpreter"] = self.cfg[step][
            "config"
        ].get("ansible_python_interpreter", "/usr/bin/python3")
        dump_file = self._get_files_copy(step)
        if dump_file:
            config[step]["vars"][f"{step}_dump"] = str(dump_file)

    def parse_config(self) -> str:
        """Create config files for anisble and evaluation_system.conf."""
        logger.info("Parsing configurations")
        self._check_config()
        config: dict[str, dict[str, dict[str, str | int | bool]]] = {}
        for step in set(self._config_keys):
            config[step] = {}
            config[step]["hosts"] = self.cfg[step]["hosts"]
            config[step]["vars"] = {}
            for key, value in self.cfg[step]["config"].items():
                if key not in ("root_passwd",):
                    new_key = f"{step}_{key}"
                else:
                    new_key = key
                config[step]["vars"][new_key] = value
            config[step]["vars"]["project_name"] = self.project_name
            # Add additional keys
            self._set_additional_config_values(step, config)
        if "db" in self._config_keys:
            config.update(self._add_local_config(config["db"]["vars"]))
        return yaml.dump(config)

    def _create_sql_dump(self):
        """Create a sql dump file to create tables."""

        logger.info("Creating database dump file.")
        head = """
FLUSH PRIVILEGES;
USE mysql;
CREATE USER IF NOT EXISTS '{user}'@'localhost' IDENTIFIED BY '{passwd}';
CREATE USER IF NOT EXISTS '{user}'@'%' IDENTIFIED BY '{passwd}';
CREATE DATABASE IF NOT EXISTS {db};
ALTER USER '{user}'@'localhost' IDENTIFIED BY '{passwd}';
ALTER USER '{user}'@'%' IDENTIFIED BY '{passwd}';
FLUSH PRIVILEGES;
GRANT ALL PRIVILEGES ON {db}.* TO '{user}'@'%' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON {db}.* TO '{user}'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;
USE {db};

""".format(
            user=self.cfg["db"]["config"]["user"],
            db=self.cfg["db"]["config"]["db"],
            passwd=self.db_pass,
        )
        with self._dump_file.open("w") as f_obj:
            tail = (self.aux_dir / "create_tables.sql").open("r").read()
            f_obj.write(head + tail)

    @property
    def _dump_file(self) -> Path:
        return Path(self._td.name) / "sql_dump.sql"

    @property
    def _playbook_file(self) -> Path:

        return Path(self._td.name) / "ansible-playbook.yml"

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
        """Set all the deploment steps."""
        steps = []
        for step in self.step_order:
            if step in self._steps and step not in steps:
                steps.append(step)
            if step == "db" and step in self._steps:
                steps.append("vault")
        return steps

    def create_playbooks(self):
        """Create the ansible playbook form all steps."""
        logger.info("Creating Ansible playbooks")
        playbook = []
        for step in self.steps:
            getattr(self, f"_prep_{step}")()
            playbook_file = self.playbook_dir / f"{step}-server-playbook.yml"
            with playbook_file.open() as f_obj:
                playbook += yaml.safe_load(f_obj)
        with self._playbook_file.open("w") as f_obj:
            yaml.dump(playbook, f_obj)

    def create_eval_config(self) -> None:
        """Create and dump the evaluation_systme.config."""
        logger.info("Creating evaluation_system.conf")
        keys = (
            ("core", "admins"),
            ("web", "project_website"),
            ("core", "root_dir"),
            ("core", "base_dir_location"),
        )
        server_keys = ("core", "port")
        cfg_file = asset_dir / "config" / "evaluation_system.conf.tmpl"
        with cfg_file.open() as f_obj:
            lines = f_obj.readlines()
            for num, line in enumerate(lines):
                if line.startswith("project_name"):
                    lines[num] = f"project_name={self.project_name}\n"
                for key, value in keys:
                    if line.startswith(value):
                        cfg = self.cfg[key]["config"].get(value, "")
                        lines[num] = f"{value}={cfg}\n"
                for step in ("solr", "db"):
                    for key in server_keys:
                        cfg = self.cfg[step]["config"].get(key, "")
                        if line.startswith(f"{step}.{key}"):
                            lines[num] = f"{step}.{key}={cfg}\n"
                    if line.startswith(f"{step}.host"):
                        lines[num] = f"{step}.host={self.cfg[step]['hosts']}\n"
        dump_file = self._get_files_copy("core")
        if dump_file:
            with dump_file.open("w") as f_obj:
                f_obj.write("".join(lines))

    def play(
        self, server_map: str | None = None, ask_pass: bool = True, verbosity: int = 0
    ) -> None:
        """Play the ansible playbook.

        Parameters
        ----------
        server_map: str, default: None
            Hostname running the service that keeps track of the server
            infrastructure, if None given (default) no new deployed services
            are added.
        ask_pass: bool, default: True
            Instruct Ansible to ask for the ssh passord instead of using a
            ssh key
        verbosity: int, default: 0
            Verbosity level, default 0
        """
        self.create_playbooks()
        inventory = self.parse_config()
        self.create_eval_config()
        with self.inventory_file.open("w") as f_obj:
            f_obj.write(inventory)
        if self.master_pass:
            inventory_str = inventory.replace(
                self.master_pass, "*" * len(self.master_pass)
            )
        else:
            inventory_str = inventory
        Console().print(inventory_str, style="bold", markup=True)
        logger.info("Playing the playbooks with ansible")
        v_string = sign(verbosity) * "-" + verbosity * "v"
        cmd = (
            f"ansible-playbook {v_string} -i {self.inventory_file} "
            f"{self._playbook_file} --ask-become-pass"
        )
        if ask_pass:
            cmd += " --ask-pass"
        try:
            _ = run(
                shlex.split(cmd), env=os.environ.copy(), cwd=str(asset_dir), check=True
            )
        except KeyboardInterrupt:
            pass
        if server_map:
            self.upload_server_info(server_map, inventory)

    def upload_server_info(self, server_map: str, inventory: str) -> None:
        """Upload information on server information to shared nextcloud."""
        deployment_setup: dict[str, dict[str, str]] = {}
        for step, info in yaml.safe_load(inventory).items():
            ansible_step = dict(
                python_path=info["vars"][f"{step}_ansible_python_interpreter"]
            )
            ansible_step["hosts"] = info["hosts"]
            deployment_setup[step] = ansible_step
        upload_server_map(server_map, self.project_name, deployment_setup)
