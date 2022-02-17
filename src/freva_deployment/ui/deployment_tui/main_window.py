from __future__ import annotations
import npyscreen, curses
import logging

logging.basicConfig(filename="mylog.log", level=logging.DEBUG)
from npyscreen import CheckBox, TitleText


class BaseForm(npyscreen.FormMultiPageWithMenus, npyscreen.FormWithMenus):
    """Base class for forms."""

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

    def on_ok(self):
        # Exit the application if the OK button is pressed.
        self.parentApp.switchForm(None)

    def change_forms(self, *args, **keywords):
        name = self.name.lower()
        if name.startswith("core"):
            change_to = "SECOND"
        elif name.startswith("web"):
            change_to = "THIRD"
        elif name.startswith("database"):
            change_to = "FOURTH"
        else:
            change_to = "MAIN"

        # Tell the MyTestApp object to change forms.
        self.parentApp.change_form(change_to)

    def whenDisplayText(self, argument):
        npyscreen.notify_confirm(argument)

    def whenJustBeep(self):
        curses.beep()

    def run_deployment(self, *args):

        value = npyscreen.notify_yes_no("Run deployment")
        if value is True:
            self.exit_application()

    def exit_application(self, *args):
        self.parentApp.setNextForm(None)
        self.editing = False
        self.parentApp.switchFormNow()

    def create(self):
        self.how_exited_handers[
            npyscreen.wgwidget.EXITED_ESCAPE
        ] = self.exit_application
        self.add_handlers({"^T": self.change_forms})
        self.add_handlers({"^R": self.run_deployment})
        self.add_handlers({"^E": self.exit_application})
        # The menus are created here.
        self.menu = self.add_menu(name="Main Menu", shortcut="^M")
        self.submenu = self.menu.addNewSubmenu("Deployment Menu", "^D")
        self._change_form = self.parentApp.change_form
        self.menu.addItemsFromList(
            [
                ("Run Deployment", self.run_deployment, "^R"),
                ("Exit Application", self.exit_application, "^E"),
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
            value=[1,],
            editable=True,
            name="Use this step",
            scroll_exit=True,
        )
        self._add_widgets()


class CoreScreen(BaseForm):
    """Form for the core deployment configuration."""

    def _add_widgets(self):
        """Add widgets to the screen."""
        self.input_fields: dict[str, tuple[TitleText, bool]] = dict(
            server=(
                self.add(
                    TitleText, name="Server Name(s) where core is deployed:", value=""
                ),
                True,
            ),
            branch=(
                self.add(TitleText, name="Deploy branch:", value="freva-dev"),
                True,
            ),
            root_dir=(
                self.add(TitleText, name="Core Installation directory:", value=""),
                True,
            ),
            base_dir_location=(
                self.add(TitleText, name="Plugin data directory (work-dir):", value=""),
                True,
            ),
            ansible_python_interpreter=(
                self.add(
                    TitleText,
                    name="Pythonpath on remote machine (leave blank for current path):",
                    value="",
                ),
                False,
            ),
            ansible_user=(
                self.add(
                    TitleText,
                    name="Remote login user (leave blank for current user):",
                    value="",
                ),
                False,
            ),
        )


class WebScreen(BaseForm):
    """Form for the web deployment configuration."""

    def _add_widgets(self):
        """Add widgets to the screen."""
        self.input_fields: dict[str, tuple[TitleText, bool]] = dict(
            server=(
                self.add_widget_intelligent(
                    TitleText,
                    name="Server Name(s) the web service is deployed on:",
                    value="",
                ),
                True,
            ),
            branch=(
                self.add_widget_intelligent(
                    TitleText, name="Deploy branch:", value="master"
                ),
                True,
            ),
            url=(
                self.add_widget_intelligent(
                    TitleText,
                    name="Url of the freva home page:",
                    value="www.freva.drkz.de",
                ),
                True,
            ),
            institution_logo=(
                self.add_widget_intelligent(
                    TitleText,
                    name="Path to the logo, leave blank for default logo",
                    value="",
                ),
                True,
            ),
            main_color=(
                self.add_widget_intelligent(
                    TitleText,
                    name="Html color of the main color theme",
                    value="Tomato",
                ),
                True,
            ),
            border_color=(
                self.add_widget_intelligent(
                    TitleText, name="Html color for the borders", value="#6c2e1f"
                ),
                True,
            ),
            hover_color=(
                self.add_widget_intelligent(
                    TitleText, name="Html color for hover modes", value="#d0513a"
                ),
                True,
            ),
            about_us_text=(
                self.add_widget_intelligent(
                    TitleText,
                    name="About us text: Short blurb about freva.",
                    value="Testing",
                ),
                True,
            ),
            contacts=(
                self.add_widget_intelligent(
                    TitleText,
                    name="Email address for admin(s) - comma seperated",
                    value="admin@freva.dkrz.de",
                ),
                True,
            ),
            address=(
                self.add_widget_intelligent(
                    TitleText,
                    name="Institution address, comma separated",
                    value="freva, German Climate Computing Centre (DKRZ), Bundesstr. 45a, 20146 Hamburg, Germany",
                ),
                True,
            ),
            homepage_text=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="More in detail project describtion.",
                    value=(
                        "Lorem ipsum dolor sit amet, consectetur "
                        "adipiscing elit, sed do eiusmod tempor "
                        "incididunt ut labore et dolore magna aliqua. "
                        "Ut enim ad minim veniam, quis nostrud "
                        "exercitation ullamco laboris nisi ut aliquip "
                        "ex ea commodo consequat. Duis aute irure dolor "
                        "in reprehenderit in voluptate velit esse cillum "
                        "dolore eu fugiat nulla pariatur. Excepteur sint "
                        "occaecat cupidatat non proident, sunt in culpa "
                        "qui officia deserunt mollit anim id est laborum."
                    ),
                ),
                True,
            ),
            home_page_heading=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="A brief describtion of the project",
                    value="Lorem ipsum dolor sit amet",
                ),
                True,
            ),
            schduler_host=(
                self.add_widget_intelligent(
                    TitleText, name="Slurm scheduler hostname", value="mistral.dkrz.de",
                ),
                True,
            ),
            auth_ldap_server_ui=(
                self.add_widget_intelligent(
                    TitleText,
                    name="Ldap server name(s) used for authentication - comma separated",
                    value="ldap://mldap0.hpc.dkrz.de, ldap://mldap1.hpc.dkrz.de",
                ),
                True,
            ),
            auth_allowed_group=(
                self.add_widget_intelligent(
                    TitleText,
                    name="Unix groups allowed to log on to the web:",
                    value="my_freva",
                ),
                True,
            ),
            ldap_user_base=(
                self.add_widget_intelligent(
                    TitleText,
                    name="Ldap search keys for user base",
                    value="cn=users,cn=accounts,dc=dkrz,dc=de",
                ),
                True,
            ),
            ldap_group_base=(
                self.add_widget_intelligent(
                    TitleText,
                    name="Ldap search keys for group base",
                    value="cn=groups,cn=accounts,dc=dkrz,dc=de",
                ),
                True,
            ),
            ldap_user_dn=(
                self.add_widget_intelligent(
                    TitleText,
                    name="Distinguished name (dn) for the ldap user",
                    value="uid=dkrzagent,cn=sysaccounts,cn=etc,dc=dkrz,dc=de",
                ),
                True,
            ),
            ldap_user_pw=(
                self.add_widget_intelligent(
                    npyscreen.TitlePassword, name="Password for ldap user", value=""
                ),
                True,
            ),
            ansible_python_interpreter=(
                self.add_widget_intelligent(
                    TitleText,
                    name="Pythonpath on remote machine (leave blank for current path):",
                    value="",
                ),
                False,
            ),
            ansible_user=(
                self.add_widget_intelligent(
                    TitleText,
                    name="Remote login user (leave blank for current user):",
                    value="",
                ),
                False,
            ),
        )


class DBScreen(BaseForm):
    """Form for the core deployment configuration."""

    def _add_widgets(self):
        """Add widgets to the screen."""
        self.input_fields: dict[str, tuple[TitleText, bool]] = dict(
            server=(
                self.add(
                    TitleText,
                    name="Server Name(s) where the database service is deployed:",
                    value="",
                ),
                True,
            ),
            user=(
                self.add(TitleText, name="Database user:", value="evaluation_system"),
                True,
            ),
            port=(
                self.add(
                    npyscreen.TitleCombo,
                    name="Database Port",
                    value=6,
                    values=[i for i in range(3300, 3320)],
                ),
                True,
            ),
            ansible_python_interpreter=(
                self.add(
                    TitleText,
                    name="Pythonpath on remote machine (leave blank for current path):",
                    value="",
                ),
                False,
            ),
            ansible_user=(
                self.add(
                    TitleText,
                    name="Remote login user (leave blank for current user):",
                    value="",
                ),
                False,
            ),
        )


class SolrScreen(BaseForm):
    """Form for the solr deployment configuration."""

    def _add_widgets(self):
        """Add widgets to the screen."""
        self.input_fields: dict[str, tuple[TitleText, bool]] = dict(
            server=(
                self.add(
                    TitleText,
                    name="Server Name(s) where the solr service is deployed:",
                    value="",
                ),
                True,
            ),
            mem=(
                self.add(
                    npyscreen.TitleCombo,
                    name="Virtual memory (in GB) for the solr server:",
                    value=5,
                    values=[f"{i/10}g" for i in range(5, 100, 5)],
                ),
                True,
            ),
            port=(
                self.add(
                    npyscreen.TitleCombo,
                    name="Solr port:",
                    value=3,
                    values=[i for i in range(8980, 9000)],
                ),
                True,
            ),
            core=(
                self.add(
                    TitleText, name="Name of the standard solr core:", value="files"
                ),
                True,
            ),
            ansible_python_interpreter=(
                self.add(
                    TitleText,
                    name="Pythonpath on remote machine (leave blank for current path):",
                    value="",
                ),
                False,
            ),
            ansible_user=(
                self.add(
                    TitleText,
                    name="Remote login user (leave blank for current user):",
                    value="",
                ),
                False,
            ),
        )


class MainApp(npyscreen.NPSAppManaged):
    def onStart(self):
        # When Application starts, set up the Forms that will be used.
        # These two forms are persistent between each edit.
        self.addForm(
            "MAIN", CoreScreen, name="Core deployment",
        )
        self.addForm("SECOND", WebScreen, name="Web deployment")
        self.addForm("THIRD", DBScreen, name="Database deployment")
        self.addForm("FOURTH", SolrScreen, name="Solr deployment")

    def onCleanExit(self):
        npyscreen.notify_wait("Goodbye!")

    def change_form(self, name):
        # Switch forms.  NB. Do *not* call the .edit() method directly (which
        # would lead to a memory leak and ultimately a recursion error).
        # Instead, use the method .switchForm to change forms.
        self.switchForm(name)

        # By default the application keeps track of every form visited.
        # There's no harm in this, but we don't need it so:
        self.resetHistory()


if __name__ == "__main__":
    try:
        main_app = MainApp()
        main_app.run()
    except KeyboardInterrupt:
        pass
