from __future__ import annotations
from functools import partial
import os
from pathlib import Path
import npyscreen, curses
import logging


logging.basicConfig(filename="mylog.log", level=logging.DEBUG)
logger: logging.Logger = logging.getLogger("deploy-freva-tui")


class FileSelector(npyscreen.FileSelector):
    def __init__(self, *args, file_extentions=[".toml"], **kwargs):

        if isinstance(file_extentions, str):
            file_extentions = [file_extentions]
        self.file_extentions = file_extentions
        # self.how_exited_handers[npyscreen.wgwidget.EXITED_ESCAPE] = self.exit_editing
        super().__init__(*args, **kwargs)

    def update_grid(self):
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


def selectFile(starting_value=None, *args, **keywords):
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

    def get_host(self, key) -> str:
        host = self.parentApp.config[key]["hosts"]
        if isinstance(host, str):
            host = [v.strip() for v in host.split(",") if v.strip()]
        return ",".join(host)

    def get_config(self):
        """Check if the from entries are valid."""
        config = {}
        for key, (obj, mandatory) in self.input_fields.items():
            try:
                value = obj.values[obj.value]
            except AttributeError:
                value = obj.value
            if isinstance(value, str) and mandatory:
                if not value and self.use.value:
                    msg = f"MISSING ENTRY FOR: {obj.name}"
                    npyscreen.notify_confirm(msg, title="ERROR")
                    return
            config[key] = value
        cfg = dict(hosts=config.pop("hosts"))
        cfg["config"] = config
        for key, value in cfg["config"].items():
            if key in self.list_keys:
                cfg["config"][key] = value.split(",")
        return cfg

    def draw_form(self):
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

    def change_forms(self, *args, **keywords):
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

    def whenDisplayText(self, argument):
        npyscreen.notify_confirm(argument)

    def run_deployment(self, *args):

        self.parentApp.current_form = self.name
        self.parentApp.change_form("SETUP")

    def create(self):
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
