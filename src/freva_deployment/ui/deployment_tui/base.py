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
        self.how_exited_handers[npyscreen.wgwidget.EXITED_ESCAPE] = self.exit

    def exit(self) -> None:
        """Exit the dialogue."""
        self.wCommand.value = ""
        self.value = ""
        self.exit_editing()

    def update_grid(self) -> None:
        if self.value:
            self.value = os.path.expanduser(self.value)
        if not os.path.exists(self.value):
            self.value = os.getcwd()
        if os.path.isdir(self.value):
            working_dir = Path(self.value)
        else:
            working_dir = Path(self.value).parent
        self.wStatus1.value = working_dir
        file_list, dir_list = [], []
        if working_dir.parent != working_dir:
            dir_list.append("..")
        try:
            for fn in working_dir.glob("*"):
                rel_path = str(fn.relative_to(working_dir))
                if not rel_path.startswith("."):
                    if fn.is_dir():
                        dir_list.append(str(fn) + os.sep)
                    elif fn.suffix in self.file_extentions:
                        file_list.append(str(fn))
        except OSError:
            npyscreen.notify_wait(
                title="Error", message="Could not read specified directory."
            )
        # DOES NOT CURRENTLY WORK - EXCEPT FOR THE WORKING DIRECTORY.  REFACTOR.
        # sort Filelist
        file_list.sort(key=str.casefold)
        dir_list.sort(key=str.casefold)
        if self.sort_by_extension:
            file_list.sort(key=self.get_extension)
        self.wMain.set_grid_values_from_flat_list(
            dir_list + file_list, reset_cursor=False
        )
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
    F.edit()
    return F.wCommand.value


class BaseForm(npyscreen.FormMultiPageWithMenus, npyscreen.FormWithMenus):
    """Base class for forms."""

    _num: int = 0
    input_fields: dict[str, tuple[npyscreen.TitleText, bool]] = {}
    """Dictionary of input fileds: the key of the dictionary represents the name
       of the key in the in config toml input files. Values represent a tuple of
       npysceen types that display the input information on this key to the
       user and a boolean indicating whether or not this variable is mandatory.
    """
    certificates: list[str] = []
    """The type of certificate files this step needs."""

    def get_config(self, key) -> dict[str, str | bool | list[str]]:
        """Read the configuration for a step."""
        try:
            cfg = self.parentApp.config[key].copy()
            if not isinstance(cfg, dict):
                cfg = {"config": {}}
        except (KeyError, AttributeError, TypeError):
            cfg = {"config": {}}
        cfg.setdefault("config", {})
        for k, values in cfg["config"].items():
            if values is None:
                cfg["config"][k] = ""
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

    @property
    def num(self) -> str:
        """Calculate the number for enumerations of any input field."""
        self._num += 1
        return f"{self._num}. "

    def check_config(
        self, notify: bool = True,
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
            "^K:Prev. Tab ",
            "^L:Next Tab ",
            "^R:Run ",
            "^S:Save ",
            "^O:Load ",
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

    def previews_form(self, *args, **keywords) -> None:
        return self.change_forms(*args, reverse=True, **keywords)

    def change_forms(self, *args, reverse=False, **keywords) -> None:
        """Cycle between the deployment config forms."""
        for step in self.parentApp._steps_lookup.keys():
            if self.name.lower().startswith(step):
                name = step
                break
            elif self.name.lower().startswith("database"):
                name = "db"
                break
        keys = self.parentApp._steps_lookup.keys()
        steps = list(self.parentApp._steps_lookup.values())
        if reverse:
            change_to = dict(zip(keys, [steps[-1]] + steps[:-1]))
        else:
            change_to = dict(zip(keys, steps[1:] + [steps[0]]))
        # raise ValueError(change_to, reverse, self.parentApp._steps_lookup)
        self.parentApp.current_form = name
        self.parentApp.change_form(change_to[name])

    def run_deployment(self, *args) -> None:
        """Switch to the deployment setup form."""
        self.parentApp.current_form = self.name
        self.parentApp.change_form("SETUP")

    def create(self) -> None:
        """Setup the form."""
        self.how_exited_handers[
            npyscreen.wgwidget.EXITED_ESCAPE
        ] = self.parentApp.exit_application
        self.add_handlers({"^O": self.parentApp.load_dialog})
        self.add_handlers({"^S": self.parentApp.save_dialog})
        self.add_handlers({"^K": self.previews_form})
        self.add_handlers({"^L": self.change_forms})
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
            name="Check to set up the {}".format(self.step),
            scroll_exit=True,
        )
        self._add_widgets()
