"""The Freva deployment Text User Interface (TUI) helps to configure a
deployment setup for a new instance of freva."""
from __future__ import annotations
import json
from pathlib import Path
import time
import threading
from typing import Any, cast

import appdirs
import npyscreen
import tomlkit

from freva_deployment.utils import asset_dir, config_dir
from .base import selectFile, BaseForm
from .deploy_forms import WebScreen, DBScreen, SolrScreen, CoreScreen, RunForm


class MainApp(npyscreen.NPSAppManaged):
    config: dict[str, Any] = dict()

    def onStart(self) -> None:
        """When Application starts, set up the Forms that will be used."""
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.steps: list[str] = []
        self.setup: dict[str, Any] = {}
        self._steps_lookup = {
            "core": "MAIN",
            "web": "SECOND",
            "solr": "FOURTH",
            "db": "THIRD",
        }
        self._forms: dict[str, BaseForm] = {}
        self.current_form = "core"
        self.config = cast(dict[str, Any], self._read_cache("config", {}))
        for step in self._steps_lookup.keys():
            self.config.setdefault(step, {"hosts": "", "config": {}})
        self._add_froms()
        self._thread_stop = threading.Event()
        self._save_thread = threading.Thread(target=self._auto_save)
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
            self._thread_stop.set()
            self.setNextForm(None)
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
            if form_obj.use.value:
                self.steps.append(step)
            self.config[step] = cfg
        return None

    def _auto_save(self) -> None:
        """Auto save the current configuration."""
        while not self._thread_stop.is_set():
            time.sleep(0.5)
            if self._thread_stop.is_set():
                break
            try:
                self.check_missing_config(stop_at_missing=False)
                self.save_config_to_file()
            except Exception:
                pass

    def save_dialog(self, *args, **kwargs) -> None:
        """Careate a dialoge that allows for saving the config file."""

        the_selected_file = selectFile(
            select_dir=False, must_exist=False, file_extentions=[".toml"]
        )
        if the_selected_file:
            the_selected_file = str(Path(the_selected_file).expanduser().absolute())
            self.check_missing_config(stop_at_missing=False)
            self._setup_form.inventory_file.value = the_selected_file
            self.save_config_to_file(write_toml_file=True)

    def _update_config(self, config_file: Path | str) -> None:
        """Update the maindow after a new configuration has been loaded."""

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
        """Careate a dialoge that allows for loading a config file."""

        the_selected_file = selectFile(
            select_dir=False, must_exist=True, file_extentions=[".toml"]
        )
        if the_selected_file:
            self._update_config(the_selected_file)
            self.save_config_to_file()

    def save_config_to_file(self, write_toml_file: bool = False) -> Path | None:
        """Save the status of the tui to file."""
        cache_file = self.cache_dir / ".temp_file.toml"
        save_file = self._setup_form.inventory_file.value
        cert_file = self._setup_form.cert_file.value
        project_name = self._setup_form.project_name.value
        wipe = self._setup_form.wipe.value
        ssh_pw = self._setup_form.use_ssh_pw.value
        if isinstance(wipe, list):
            wipe = bool(wipe[0])
        if isinstance(ssh_pw, list):
            ssh_pw = bool(ssh_pw[0])
        with open(self.cache_dir / "freva_deployment.json", "w") as f:
            json.dump(
                {
                    "save_file": str(save_file),
                    "steps": list(set(self.steps)),
                    "cert_file": str(cert_file),
                    "project_name": project_name,
                    "wipe": wipe,
                    "ssh_pw": ssh_pw,
                    "config": self.config,
                },
                f,
                indent=3,
            )
        if write_toml_file is False:
            return None
        save_file = save_file or cache_file
        save_file = Path(save_file).expanduser().absolute()
        try:
            with open(asset_dir / "config" / "inventory.toml") as f:
                config_tmpl = cast(dict[str, Any], tomlkit.load(f))
        except Exception:
            config_tmpl = self.config
        for step, settings in self.config.items():
            config_tmpl[step]["hosts"] = settings["hosts"]
            for key, config in settings["config"].items():
                config_tmpl[step]["config"][key] = config
        save_file.parent.mkdir(exist_ok=True, parents=True)
        with open(save_file, "w") as f:
            toml_string = tomlkit.dumps(config_tmpl)
            f.write(toml_string)
        return save_file

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
        return cast(list[str], self._read_cache("steps", ["core", "web", "db", "solr"]))

    @property
    def cert_file(self) -> str:
        """Read the certificate file from the cache."""
        return cast(str, self._read_cache("cert_file", ""))

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
