from __future__ import annotations
import os
from pathlib import Path
import logging

import curses
import npyscreen


logging.basicConfig(level=logging.DEBUG)
logger: logging.Logger = logging.getLogger("deploy-freva-tui")


class FileSelector(npyscreen.FileSelector):
    """FileSelector widget that allows for filtering file extensions."""

    file_extentions: list[str]
    """List of allowed file extensions."""
    value: str
    """The value of this file selector."""

    def __init__(
        self, *args, file_extentions: str | list[str] = [".toml"], **kwargs
    ) -> None:

        if isinstance(file_extentions, str):
            self.file_extentions = [file_extentions]
        else:
            self.file_extentions = file_extentions
        super().__init__(*args, **kwargs)

    def update_grid(self) -> None:
        if self.value:
            self.value = os.path.expanduser(self.value)
        if not os.path.exists(self.value):
            self.value = os.getcwd()
        if os.path.isdir(self.value):
            working_dir = self.value
        else:
            working_dir = os.path.dirname(self.value)
        self.wStatus1.value = working_dir
        file_list = []
        if os.path.abspath(os.path.join(working_dir, "..")) != os.path.abspath(
            working_dir
        ):
            file_list.append("..")
        try:
            file_list.extend(
                [os.path.join(working_dir, fn) for fn in os.listdir(working_dir)]
            )
        except OSError:
            npyscreen.notify_wait(
                title="Error", message="Could not read specified directory."
            )
        # DOES NOT CURRENTLY WORK - EXCEPT FOR THE WORKING DIRECTORY.  REFACTOR.
        new_file_list = []
        for f in file_list:
            f = os.path.normpath(f)
            if os.path.isdir(f):
                new_file_list.append(f + os.sep)
            else:
                if Path(f).suffix in self.file_extentions:
                    new_file_list.append(f)
        file_list = new_file_list
        del new_file_list
        # sort Filelist
        file_list.sort()
        if self.sort_by_extension:
            file_list.sort(key=self.get_extension)
        file_list.sort(key=os.path.isdir, reverse=True)
        self.wMain.set_grid_values_from_flat_list(file_list, reset_cursor=False)
        self.display()


def selectFile(starting_value: str = "", *args, **keywords):
    F = FileSelector(*args, **keywords)
    F.set_colors()
    F.wCommand.show_bold = True
    if starting_value:
        if not os.path.exists(os.path.abspath(os.path.expanduser(starting_value))):
            F.value = os.getcwd()
        else:
            F.value = starting_value
            F.wCommand.value = starting_value
    else:
        F.value = os.getcwd()
    F.update_grid()
    F.display()
    F.edit()
    return F.wCommand.value


class BaseForm(npyscreen.FormMultiPageWithMenus, npyscreen.FormWithMenus):
    """Base class for forms."""

    def get_config(self, key) -> dict[str, str | bool | list[str]]:
        """Read the configuration for a step."""
        try:
            cfg = self.parentApp.config[key].copy()
            if not isinstance(cfg, dict):
                cfg = {"config": {}}
        except (KeyError, AttributeError, TypeError):
            cfg = {"config": {}}
        cfg.setdefault("config", {})
        return cfg["config"]

    def get_host(self, key) -> str:
        """Read the host name(s) from the main windows config."""
        try:
            host = self.parentApp.config[key]["hosts"]
        except (TypeError, KeyError):
            return ""
        if isinstance(host, str):
            host = [v.strip() for v in host.split(",") if v.strip()]
        return ",".join(host)

    def check_config(
        self,
        notify: bool = True,
    ) -> dict[str, str | dict[str, str | list | int | bool | None]] | None:
        """Check if the from entries are valid."""
        config = {}
        for key, (obj, mandatory) in self.input_fields.items():
            try:
                value = obj.values[obj.value]
            except AttributeError:
                value = obj.value
            if isinstance(value, str):
                if not value and self.use.value and mandatory and notify:
                    msg = f"MISSING ENTRY FOR {self.step}: {obj.name}"
                    npyscreen.notify_confirm(msg, title="ERROR")
                    return None
                elif not value and not mandatory:
                    continue
            config[key] = value
        cfg = dict(hosts=config.pop("hosts"))
        cfg["config"] = config
        for key, value in cfg["config"].items():
            if key in self.list_keys:
                cfg["config"][key] = value.split(",")
        return cfg

    def draw_form(self) -> None:
        """Overload the draw_from method from, this is done to add menus."""
        super().draw_form()
        menus = [
            " " + self.__class__.MENU_KEY + ":Main Menu ",
            "^T:Next Tab ",
            "^R:Run Deployment ",
            "^E:Exit ",
        ]
        y, x = self.display_menu_advert_at()
        for n, menu_advert in enumerate(menus):
            if isinstance(menu_advert, bytes):
                menu_advert = menu_advert.decode("utf-8", "replace")
            X = sum([len(menu) for menu in menus[:n]]) + x
            self.add_line(
                y,
                X,
                menu_advert,
                self.make_attributes_list(menu_advert, curses.A_NORMAL),
                self.columns - X - 1,
            )

    def change_forms(self, *args, **keywords) -> None:
        """Cycle between the deployment config forms."""
        name = self.name.lower()
        keys = self.parentApp._steps_lookup.keys()
        steps = list(self.parentApp._steps_lookup.values())
        change_to = dict(zip(keys, steps[1:] + [steps[0]]))
        for step in keys:
            if name.startswith(step):
                self.parentApp.current_form = step
                self.parentApp.change_form(change_to[step])
                return
        self.parentApp.current_form = "core"
        self.parentApp.change_form("MAIN")

    # def whenDisplayText(self, argument):
    #    npyscreen.notify_confirm(argument)

    def run_deployment(self, *args) -> None:
        """Switch to the deployment setup form."""
        self.parentApp.current_form = self.name
        self.parentApp.change_form("SETUP")

    def create(self) -> None:
        """Setup the form."""
        self.how_exited_handers[
            npyscreen.wgwidget.EXITED_ESCAPE
        ] = self.parentApp.exit_application
        self.add_handlers({"^L": self.parentApp.load_dialog})
        self.add_handlers({"^S": self.parentApp.save_dialog})
        self.add_handlers({"^T": self.change_forms})
        self.add_handlers({"^R": self.run_deployment})
        self.add_handlers({"^E": self.parentApp.exit_application})
        # The menus are created here.
        self.menu = self.add_menu(name="Main Menu", shortcut="^M")
        self.submenu = self.menu.addNewSubmenu("Deployment Menu", "^D")
        self._change_form = self.parentApp.change_form
        self.menu.addItemsFromList(
            [
                ("Save Config", self.parentApp.save_dialog, "^S"),
                ("Load Config", self.parentApp.load_dialog, "^L"),
                ("Run Deployment", self.run_deployment, "^R"),
                ("Exit Application", self.parentApp.exit_application, "^E"),
            ]
        )
        self.submenu.addItemsFromList(
            [
                ("Core Deployment", self._change_form, "c", "c", ("MAIN",)),
                ("Web Deployment", self._change_form, "w", "w", ("SECOND",)),
                ("DB Deployment", self._change_form, "d", "d", ("THIRD",)),
                ("Solr Deployment", self._change_form, "s", "s", ("FOURTH",)),
                ("Run Deployment", self.run_deployment, "^R"),
            ]
        )
        self.use = self.add(
            npyscreen.CheckBox,
            max_height=2,
            value=self.step in self.parentApp._steps,
            editable=True,
            name="Use this step",
            scroll_exit=True,
        )
        self._add_widgets()
