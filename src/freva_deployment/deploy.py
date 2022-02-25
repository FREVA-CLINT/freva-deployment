#!/usr/bin/env python3
from __future__ import annotations
from getpass import getuser
import os
from pathlib import Path
import random
import shlex
import string
from subprocess import run
import sys
from tempfile import NamedTemporaryFile, TemporaryDirectory, mkdtemp

from rich.console import Console
import toml
import yaml

from .utils import asset_dir, config_dir, create_self_signed_cert, get_passwd, logger


class DeployFactory:

    _tf = None
    master_pass = None
    inventory_file = None
    step_order: tuple[str, ...] = ("db", "vault", "solr", "core", "web", "backup")
    _steps_with_cert: tuple[str, ...] = ("db", "vault", "core", "web")

    @property
    def private_key_file(self) -> str:
        """Path to the private certifcate file."""
        return str(Path(self.public_key_file).with_suffix(".key"))

    @property
    def public_key_file(self) -> str:
        """Path to the public certificate file."""
        if not any([step in self._steps_with_cert for step in self.steps]):
            return str(Path(mkdtemp(suffix=".crt")))
        if not self._cert_file:
            self._cert_file = config_dir / "keys" / f"{self.project_name}.crt"
        if not self._cert_file.is_file():
            logger.warning("Certificate file does not exist, creating new one")
            self._cert_file = create_self_signed_cert(self._cert_file)
        return str(self._cert_file.absolute())

    def _prep_vault(self):
        """Prepare the vault."""
        self.cfg["vault"] = self.cfg["db"].copy()
        if self.master_pass is None:
            self.master_pass = get_passwd()
        self.cfg["vault"]["config"]["root_passwd"] = self.master_pass
        self.cfg["vault"]["config"]["passwd"] = self.db_pass
        self.cfg["vault"]["config"]["keyfile"] = self.public_key_file
        self.cfg["vault"]["config"]["private_keyfile"] = self.private_key_file

    def _prep_db(self):
        """prepare the mariadb service."""
        if self.master_pass is None:
            self.master_pass = get_passwd()
        self.cfg["db"]["config"]["root_passwd"] = self.master_pass
        self.cfg["db"]["config"]["passwd"] = self.db_pass
        self.cfg["db"]["config"]["keyfile"] = self.public_key_file
        self.cfg["db"]["config"]["private_keyfile"] = self.private_key_file
        for key in ("name", "user", "db"):
            self.cfg["db"]["config"].setdefault(key, "freva")
        self.cfg["db"]["config"].setdefault("port", "3306")
        self._create_sql_dump()

    def _prep_solr(self):
        """prepare the apache solr service."""
        for key, default in dict(core="files", mem="4g", port=8983).items():
            self.cfg["solr"]["config"].setdefault(key, default)

    def _prep_core(self):
        """prepare the core deployment."""
        self.cfg["core"]["config"].setdefault("admins", getuser())
        if not self.cfg["core"]["config"]["admins"]:
            self.cfg["core"]["config"]["admins"] = getuser()
        self.cfg["core"]["config"].setdefault("branch", "freva-dev")
        install_dir = self.cfg["core"]["config"]["install_dir"]
        self.cfg["core"]["config"].setdefault("root_dir", install_dir)
        self.cfg["core"]["config"]["keyfile"] = self.public_key_file
        self.cfg["core"]["config"]["private_keyfile"] = self.private_key_file

    def _prep_web(self):
        """prepare the web deployment."""
        self.cfg["web"]["config"].setdefault("branch", "master")
        self._prep_core()
        admin = self.cfg["core"]["config"]["admins"]
        if not isinstance(admin, str):
            self.cfg["web"]["config"]["admin"] = admin[0]
        else:
            self.cfg["web"]["config"]["admin"] = admin
        _webserver_items = {}
        web_conf = Path(self._td.name) / "freva_web.toml"
        web_conf = Path("freva_web.toml")
        try:
            _webserver_items = {
                k.replace("web_", "").upper(): v
                for (k, v) in self.cfg["web"]["config"].items()
            }
        except KeyError:
            raise KeyError(
                "No web config section given, please configure the web.config"
            )
        try:
            with Path(_webserver_items["homepage_text"]).open() as f:
                _webserver_items["homepage_text"] = f.read()
        except Exception:
            pass
        logo = Path(self.cfg["web"]["config"].get("institution_logo", ""))
        alias = self.cfg["web"]["config"].pop("server_alias", [])
        if isinstance(alias, str):
            alias = alias.split(",")
        alias = ",".join([a for a in alias if a.strip()])
        if not alias:
            alias = "none"
        self.cfg["web"]["config"]["server_alias"] = alias
        web_host = self.cfg["web"]["hosts"]
        if web_host == "127.0.0.1":
            web_host = "localhost"
        self.cfg["web"]["config"]["host"] = web_host
        _webserver_items["INSTITUTION_LOGO"] = f"logo{logo.suffix}"
        try:
            with Path(_webserver_items["ABOUT_US_TEXT"]).open() as f:
                _webserver_items["ABOUT_US_TEXT"] = f.read()
        except Exception:
            pass
        try:
            _webserver_items["IMPRINT"] = _webserver_items["ADDRESS"].split(",")
        except AttributeError:
            pass
        with web_conf.open("w") as f:
            toml.dump(_webserver_items, f)
        for key in ("core", "web"):
            logo_suffix = logo.suffix or ".png"
            self.cfg[key]["config"]["config_file"] = str(web_conf.absolute())
            self.cfg[key]["config"]["institution_logo"] = str(logo.absolute())
            self.cfg[key]["config"]["institution_logo_suffix"] = logo_suffix
        if self.master_pass is None:
            self.master_pass = get_passwd()
        self.cfg["web"]["config"]["root_passwd"] = self.master_pass

    def _prep_backup(self):
        """Prepare the config for the backup step."""
        self.cfg["backup"] = self.cfg["db"].copy()
        if self.master_pass is None:
            self.master_pass = get_passwd()
        self.cfg["backup"]["config"]["root_passwd"] = self.master_pass
        self.cfg["backup"]["config"]["passwd"] = self.db_pass
        self.cfg["backup"]["config"]["keyfile"] = self.public_key_file
        self.cfg["backup"]["config"]["private_keyfile"] = self.private_key_file

    def __enter__(self):
        self._td = TemporaryDirectory(prefix="inventory")
        self.inventory_file = Path(self._td.name) / "inventory.yaml"
        return self

    def __exit__(self, type, value, traceback):
        self._td.cleanup()

    def _read_cfg(self):
        try:
            with self._inv_tmpl.open() as f:
                return toml.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"No such file {self._inv_tmpl}")

    @property
    def git_url(self):
        try:
            return self.cfg["coreservers:vars"]["git_url"]
        except KeyError:
            raise KeyError(
                (
                    "You must set git_url and branch keys in coreservers:vars in "
                    "the inventory file"
                )
            )

    @property
    def git_branch(self):
        try:
            return self.cfg["coreservers:vars"]["branch"]
        except KeyError:
            raise KeyError(
                (
                    "You must set git_url and branch keys in coreservers:vars "
                    "in the inventory file"
                )
            )

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
                    db_dump=str(self.dump_file),
                    db_port=config.get("db_port", 3306),
                    user=getuser(),
                    local_ansible_python_interpreter=str(self.python_prefix),
                ),
            )
        )
        return cfg

    def check_config(self):
        sections = []
        for section in self.cfg.keys():
            for step in self.steps:
                if section.startswith(step) and section not in sections:
                    sections.append(section)
        for section in sections:
            for key, value in self.cfg[section]["config"].items():
                if (
                    not value
                    and not key.startswith("admin")
                    and not isinstance(value, bool)
                ):
                    raise ValueError(f"{key} in {section} is empty in {self._inv_tmpl}")

    def get_files_copy(self, key):
        return dict(
            db=self.dump_file,
            solr=(self.aux_dir / "managed-schema").absolute(),
            core=(self._inv_tmpl.parent / "evaluation_system.conf").absolute(),
            web=(self._inv_tmpl.parent / "evaluation_system.conf").absolute(),
        ).get(key, "")

    @property
    def db_pass(self):
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
        characters = "".join(characters)
        self._db_pass = "".join(random.sample(characters, len(characters)))
        return self._db_pass

    @property
    def needs_core(self):
        """Define the steps that need the core config."""
        return ["web", "core"]

    def _set_additional_config_values(
        self, step: str, config: dict[str, dict[str, str | int | bool]]
    ) -> dict[str, dict[str, str | int | bool]]:
        """Set additional values to the configuration."""
        if step in self.needs_core:
            for key in ("git_url", "branch", "root_dir"):
                value = self.cfg["core"]["config"][key]
                config[step]["vars"][f"core_{key}"] = value
        config[step]["vars"][f"{step}_hostname"] = self.cfg[step]["hosts"]
        config[step]["vars"][f"{step}_name"] = f"{self.project_name}_{step}"
        config[step]["vars"]["asset_dir"] = str(asset_dir)
        config[step]["vars"]["user"] = getuser()
        config[step]["vars"]["wipe"] = self.wipe
        config[step]["vars"][f"{step}_ansible_python_interpreter"] = self.cfg[step][
            "config"
        ].get("ansible_python_interpreter", "/usr/bin/python3")
        dump_file = self.get_files_copy(step)
        if dump_file:
            config[step]["vars"][f"{step}_dump"] = str(dump_file)

    def parse_config(self) -> tuple[str, str]:
        """Create config files for anisble and evaluation_system.conf."""
        logger.info("Parsing configurations")
        self.check_config()
        config = {}
        for step in self.steps:
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
        if "db" in self.steps:
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
            db=self.cfg["db"]["config"]["name"],
            passwd=self.db_pass,
        )

        with self.dump_file.open("w") as f:
            tail = (self.aux_dir / "create_tables.sql").open("r").read()
            f.write(head + tail)

    @property
    def dump_file(self):
        return Path(self._td.name) / "sql_dump.sql"

    @property
    def dump_playbook(self):

        return Path("/tmp") / "ansible-playbook.yml"
        return Path(self._td.name) / "ansible-playbook.yml"

    @property
    def python_prefix(self):
        """Get the path of the new conda evnironment."""
        return Path(sys.exec_prefix) / "bin" / "python3"

    @property
    def aux_dir(self):
        """Directory with auxillary files."""
        return asset_dir / "config"

    @property
    def playbook_dir(self):
        """The location of all playbooks."""
        return asset_dir / "playbooks"

    @property
    def steps(self):
        steps = []
        for step in self.step_order:
            if step in self._steps and step not in steps:
                steps.append(step)
            if step == "db" and step in self._steps:
                steps.append("vault")
        return steps

    def __init__(
        self,
        project_name: str,
        steps: list[str] = ["services", "core", "web"],
        cert_file: str | None = None,
        config_file: Path | str | None = None,
        ask_pass: bool = False,
        wipe: bool = False,
    ) -> None:
        self._db_pass = None
        self.project_name = project_name
        self.ask_pass = ask_pass
        self._steps = steps
        self.wipe = wipe
        self._cert_file = cert_file
        self._inv_tmpl = Path(config_file or config_dir / "inventory.toml")
        self._cfg_tmpl = self.aux_dir / "evaluation_system.conf.tmpl"
        self.cfg = self._read_cfg()
        _inventory = self.inventory_file or NamedTemporaryFile().name
        self.inventory_file = Path(_inventory).with_suffix(".yaml")

    def create_playbooks(self):
        """Create the ansible playbook form all steps."""
        logger.info("Creating Ansible playbooks")
        playbook = []
        for step in self.steps:
            getattr(self, f"_prep_{step}")()
            playbook_file = self.playbook_dir / f"{step}-server-playbook.yml"
            with playbook_file.open() as f:
                playbook += yaml.safe_load(f)
        with self.dump_playbook.open("w") as f:
            yaml.dump(playbook, f)

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
        with cfg_file.open() as f:
            lines = f.readlines()
            for nn, line in enumerate(lines):
                if line.startswith("project_name"):
                    lines[nn] = f"project_name={self.project_name}\n"
                for key, value in keys:
                    if line.startswith(value):
                        cfg = self.cfg[key]["config"].get(value, "")
                        lines[nn] = f"{value}={cfg}\n"
                for s in ("solr", "db"):
                    for key in server_keys:
                        cfg = self.cfg[s]["config"].get(key, "")
                        if line.startswith(f"{s}.{key}"):
                            lines[nn] = f"{s}.{key}={cfg}\n"
                    if line.startswith(f"{s}.host"):
                        lines[nn] = f"{s}.host={self.cfg[s]['hosts']}\n"
        with self.get_files_copy("core").open("w") as f:
            f.write("".join(lines))

    def play(self):
        """Play the ansible playbook."""
        self.create_playbooks()
        self.create_eval_config()
        inventory = self.parse_config()
        with self.inventory_file.open("w") as f:
            f.write(inventory)
        if self.master_pass:
            inventory_str = inventory.replace(
                self.master_pass, "*" * len(self.master_pass)
            )
        else:
            inventory_str = inventory
        Console().print(inventory_str, style="bold", markup=True)
        logger.info("Playing the playbooks with ansible")
        cmd = f"ansible-playbook -i {self.inventory_file} {self.dump_playbook}"
        if self.ask_pass:
            cmd += " --ask-pass"
        cmd += " --ask-become-pass"
        try:
            run(shlex.split(cmd), env=os.environ.copy(), cwd=str(asset_dir))
        except KeyboardInterrupt:
            pass
