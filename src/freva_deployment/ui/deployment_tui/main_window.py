"""The Freva deployment Text User Interface (TUI) helps to configure a
deployment setup for a new instance of freva."""
from __future__ import annotations
import json
from pathlib import Path
import time
import threading
from typing import Any, Dict, List, cast

import appdirs
import npyscreen
import tomlkit

from freva_deployment.utils import asset_dir, config_dir
from .base import selectFile, BaseForm, VarForm
from .deploy_forms import WebScreen, DBScreen, SolrScreen, CoreScreen, RunForm


class MainApp(npyscreen.NPSAppManaged):
    config: dict[str, Any] = dict()

    @property
    def steps(self) -> list[str]:
        """Get the deploy steps."""
        steps = []
        for step, form_obj in self._forms.items():
            if form_obj.use.value and step not in steps:
                steps.append(step)
        return steps

    def onStart(self) -> None:
        """When Application starts, set up the Forms that will be used."""
        npyscreen.setTheme(npyscreen.Themes.ElegantTheme)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.setup: dict[str, Any] = {}
        self._forms: dict[str, BaseForm] = {}
        self.current_form = "core"
        self.init()
        self.thread_stop = threading.Event()
        self.start_auto_save()

    def init(self) -> None:
        self._steps_lookup = {
            "core": "MAIN",
            "web": "SECOND",
            "solr": "FOURTH",
            "db": "THIRD",
        }
        self.config = cast(Dict[str, Any], self._read_cache("config", {}))
        for step in self._steps_lookup.keys():
            self.config.setdefault(step, {"hosts": "", "config": {}})
        self._add_froms()

    def reset(self) -> None:
        npyscreen.blank_terminal()
        self.init()

    def start_auto_save(self) -> None:
        """(Re)-Start the auto save thread."""
        self._save_thread = threading.Thread(target=self._auto_save)
        self._save_thread.daemon = True
        self._save_thread.start()

    def _add_froms(self) -> None:
        """Add forms to edit the deploy steps to the main window."""
        self._forms["core"] = self.addForm(
            "MAIN",
            CoreScreen,
            name="Core deployment",
        )
        self._forms["web"] = self.addForm("SECOND", WebScreen, name="Web deployment")
        self._forms["db"] = self.addForm("THIRD", DBScreen, name="Database deployment")
        self._forms["solr"] = self.addForm("FOURTH", SolrScreen, name="Solr deployment")
        self._setup_form = self.addForm("SETUP", RunForm, name="Apply the Deployment")

    def exit_application(self, *args, **kwargs) -> None:
        value = npyscreen.notify_ok_cancel(
            kwargs.get("msg", "Exit Application?"), title=""
        )
        if value is True:
            self.thread_stop.set()
            self.setNextForm(None)
            self.save_config_to_file(save_file=kwargs.get("save_file"))
            self.editing = False
            self.switchFormNow()

    def change_form(self, name: str) -> None:
        # Switch forms.  NB. Do *not* call the .edit() method directly (which
        # would lead to a memory leak and ultimately a recursion error).
        # Instead, use the method .switchForm to change forms.
        self.switchForm(name)

        # By default the application keeps track of every form visited.
        # There's no harm in this, but we don't need it so:
        self.resetHistory()

    def check_missing_config(self, stop_at_missing: bool = True) -> str | None:
        """Evaluate all forms."""
        for step, form_obj in self._forms.items():
            cfg = form_obj.check_config(notify=stop_at_missing)
            if cfg is None and stop_at_missing:
                return self._steps_lookup[step]
            try:
                self.config[step] = cfg
            except Exception as error:
                raise ValueError((step, cfg))
                raise error
        return None

    def _auto_save(self) -> None:
        """Auto save the current configuration."""
        while not self.thread_stop.is_set():
            time.sleep(0.5)
            if self.thread_stop.is_set():
                break
            try:
                self.check_missing_config(stop_at_missing=False)
                self.save_config_to_file()
            except Exception:
                pass

    def save_dialog(self, *args, **kwargs) -> None:
        """Create a dialoge that allows for saving the config file."""

        the_selected_file = selectFile(
            select_dir=False, must_exist=False, file_extentions=[".toml"]
        )
        if the_selected_file:
            the_selected_file = Path(the_selected_file).with_suffix(".toml")
            the_selected_file = str(the_selected_file.expanduser().absolute())
            self.check_missing_config(stop_at_missing=False)
            self._setup_form.inventory_file.value = the_selected_file
            self.save_config_to_file(write_toml_file=True)

    def _update_config(self, config_file: Path | str) -> None:
        """Update the main window after a new configuration has been loaded."""

        try:
            with open(config_file) as f:
                self.config = tomlkit.load(f)
        except Exception:
            return
        self.resetHistory()
        self.editing = True
        self.switchFormNow()
        self._add_froms()
        self._setup_form.inventory_file.value = config_file

    def load_dialog(self, *args, **kwargs) -> None:
        """Create a dialoge that allows for loading a config file."""

        the_selected_file = selectFile(
            select_dir=False, must_exist=True, file_extentions=[".toml"]
        )
        if the_selected_file:
            self._update_config(the_selected_file)
            self.save_config_to_file()

    def save_config_to_file(self, **kwargs) -> Path | None:
        """Save the status of the tui to file."""
        try:
            return self._save_config_to_file(**kwargs)
        except Exception as error:
            npyscreen.notify_confirm(
                title="Error",
                message=f"Couldn't save config:\n{error}",
            )
        return None

    def get_save_file(self, save_file: Path | None = None) -> str:
        """Get the name of the file where the config should be stored to."""
        cache_file = self.cache_dir / ".temp_file.toml"
        if save_file:
            save_file = Path(save_file).expanduser().absolute()
        return str(save_file or cache_file)

    def _save_config_to_file(
        self,
        write_toml_file: bool = False,
        save_file: Path | None = None,
    ) -> Path | None:
        cert_files = dict(
            public_keyfile=self._setup_form.public_keyfile.value or "",
            private_keyfile=self._setup_form.private_keyfile.value or "",
            chain_keyfile=self._setup_form.chain_keyfile.value or "",
        )
        for key, value in cert_files.items():
            if value and "cfd" not in value.lower():
                cert_files[key] = str(Path(value).expanduser().absolute())
        project_name = self._setup_form.project_name.value
        server_map = self._setup_form.server_map.value
        ssh_pw = self._setup_form.use_ssh_pw.value
        if isinstance(ssh_pw, list):
            ssh_pw = bool(ssh_pw[0])
        self.config["certificates"] = cert_files
        self.config["project_name"] = project_name or ""
        config = {
            "save_file": self.get_save_file(save_file),
            "steps": self.steps,
            "ssh_pw": ssh_pw,
            "server_map": server_map,
            "config": self.config,
        }
        with open(self.cache_dir / "freva_deployment.json", "w") as f:
            json.dump({k: v for (k, v) in config.items()}, f, indent=3)
        if write_toml_file is False:
            return None
        try:
            with open(self.save_file) as f:
                config_tmpl = cast(Dict[str, Any], tomlkit.load(f))
        except FileNotFoundError:
            with open(asset_dir / "config" / "inventory.toml") as f:
                config_tmpl = cast(Dict[str, Any], tomlkit.load(f))
        except Exception:
            config_tmpl = self.config
        config_tmpl["certificates"] = cert_files
        config_tmpl["project_name"] = project_name
        for step, settings in self.config.items():
            if step in ("certificates", "project_name"):
                continue
            config_tmpl[step]["hosts"] = settings["hosts"]
            for key, config in settings["config"].items():
                config_tmpl[step]["config"][key] = config
        Path(self.save_file).parent.mkdir(exist_ok=True, parents=True)
        with open(self.save_file, "w") as f:
            toml_string = tomlkit.dumps(config_tmpl)
            f.write(toml_string)
        return Path(self.save_file)

    @property
    def cache_dir(self) -> Path:
        """The user cachedir."""
        return Path(appdirs.user_cache_dir()) / "freva-deployment"

    def _read_cache(
        self, key: str, default: str | list | bool | dict[str, str] = ""
    ) -> str | bool | list | dict[str, str]:
        try:
            with open(self.cache_dir / "freva_deployment.json", "r") as f:
                return json.load(f).get(key, default)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return default

    @property
    def _steps(self) -> list[str]:
        """Read the deployment-steps from the cache."""
        return cast(List[str], self._read_cache("steps", ["core", "web", "db", "solr"]))

    def read_cert_file(self, key: str) -> str:
        """Read the certificate file from the cache."""
        cert_file = cast(str, self.config.get("certificates", {}).get(key, ""))
        if cert_file:
            return cert_file
        return cast(str, self._read_cache(key, ""))

    @property
    def save_file(self) -> str:
        """Read the file that stores the configuration from the cache."""
        fall_back = config_dir / "inventory.toml"
        return cast(str, self._read_cache("save_file", str(fall_back)))


if __name__ == "__main__":
    try:
        main_app = MainApp()
        main_app.run()
    except KeyboardInterrupt:
        pass
