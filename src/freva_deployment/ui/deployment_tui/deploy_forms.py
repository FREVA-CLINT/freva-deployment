from __future__ import annotations
from getpass import getuser
import npyscreen
from pathlib import Path

from .base import BaseForm, logger
from freva_deployment import AVAILABLE_PYTHON_VERSIONS, AVAILABLE_CONDA_ARCHS


def get_index(values: list[...,str|int], target: str|int, default: int = 0) -> int:
    """Get the index target item in list.

    Parameters:
    ===========
    values:
        the list of values that is searched
    target:
        the item the list of values that is searched for
    default:
        if nothing is found return the default value

    Returns:
    ========
    int: Index of the the target item in the list
    """

    for n, value in enumerate(values):
        if value == target:
            return n
    return default


class CoreScreen(BaseForm):
    """Form for the core deployment configuration."""

    step: str = "core"

    def _add_widgets(self) -> None:
        """Add widgets to the screen."""
        self.list_keys = []
        cfg = self.get_config(self.step)
        arch = cfg.get("arch", AVAILABLE_CONDA_ARCHS[0])
        python_version = cfg.get("python_version", AVAILABLE_PYTHON_VERSIONS[-1])
        arch_idx = get_index(AVAILABLE_CONDA_ARCHS, arch, 0)
        python_version_idx = get_index(AVAILABLE_PYTHON_VERSIONS, python_version, -1)
        self.input_fields: dict[str, tuple[npyscreen.TitleText, bool]] = dict(
            hosts=(
                self.add(
                    npyscreen.TitleText,
                    name="Server Name(s) where core is deployed:",
                    value=self.get_host("core"),
                ),
                True,
            ),
            branch=(
                self.add(
                    npyscreen.TitleText,
                    name="Deploy branch:",
                    value=cfg.get("branch", "freva-dev"),
                ),
                True,
            ),
            install_dir=(
                self.add(
                    npyscreen.TitleFilename,
                    name="Anaconda installation dir. for core:",
                    value=cfg.get("install_dir", ""),
                ),
                True,
            ),
            install=(
                self.add(
                    npyscreen.CheckBox,
                    max_height=2,
                    value=cfg.get("install", True),
                    editable=True,
                    name=("Install a new instance of the core, or just add a new "
                          "configuration."),
                    scroll_exit=True,
                ),
                True
            ),
            root_dir=(
                self.add(
                    npyscreen.TitleFilename,
                    name=(
                        "Project configuration file directory "
                        "defaults to `intallation directory`:"
                    ),
                    value=cfg.get("root_dir", ""),
                ),
                True,
            ),
            base_dir_location=(
                self.add(
                    npyscreen.TitleText,
                    name="Plugin data directory (user work dir.):",
                    value=cfg.get("base_dir_location", ""),
                ),
                True,
            ),
            admins=(
                self.add(
                    npyscreen.TitleText,
                    name="Set the admin user(s) - comma separated",
                    value=cfg.get("admins", getuser())
            ),
            False,
            ),
            ansible_become_user=(
                self.add(
                    npyscreen.TitleText,
                    name="Set an (additional) username that has privileges to install the core",
                    value=cfg.get("ansible_become_user", ""),
                ),
                False,
            ),
            python_version=(
                self.add(
                    npyscreen.TitleCombo,
                    name="Set the python version that ist deployed.",
                    value=python_version_idx,
                    values=AVAILABLE_PYTHON_VERSIONS,
                ),
                True,
            ),
            arch=(
                self.add(
                    npyscreen.TitleCombo,
                    name=(
                        "Set the target architecutre of the system where "
                        "the backend will be installed"
                    ),
                    value=arch_idx,
                    values=AVAILABLE_CONDA_ARCHS,
                ),
                True,
            ),
            ansible_python_interpreter=(
                self.add(
                    npyscreen.TitleFilename,
                    name="Pythonpath on remote machine (leave blank for current path):",
                    value=cfg.get("ansible_python_interpreter", ""),
                ),
                False,
            ),
            ansible_user=(
                self.add(
                    npyscreen.TitleText,
                    name="Remote login user (leave blank for current user):",
                    value=cfg.get("ansible_user", ""),
                ),
                False,
            ),
        )


class WebScreen(BaseForm):
    """Form for the web deployment configuration."""

    step: str = "web"

    def _add_widgets(self) -> None:
        """Add widgets to the screen."""
        self.list_keys = "contacts", "address", "auth_ldap_server_uri", "scheduler_host"
        cfg = self.get_config(self.step)
        for key in self.list_keys:
            if key in cfg:
                if isinstance(cfg[key], str):
                    cfg[key] = [v.strip() for v in cfg[key].split(",") if v.strip()]
                    logger.warning(key, cfg[key])
        self.input_fields: dict[str, tuple[npyscreen.TitleText, bool]] = dict(
            hosts=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Server Name(s) the web service is deployed on:",
                    value=self.get_host("web"),
                ),
                True,
            ),
            branch=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Deploy branch:",
                    value=cfg.get("branch", "master"),
                ),
                True,
            ),
            url=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Url of the freva home page:",
                    value=cfg.get("url", "www.freva.drkz.de"),
                ),
                True,
            ),
            institution_logo=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Path to the logo, leave blank for default logo",
                    value=cfg.get("institution_logo", ""),
                ),
                False,
            ),
            main_color=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Html color of the main color theme",
                    value=cfg.get("main_color", "Tomato"),
                ),
                True,
            ),
            border_color=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Html color for the borders",
                    value=cfg.get("border_color", "#6c2e1f"),
                ),
                True,
            ),
            hover_color=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Html color for hover modes",
                    value=cfg.get("hover_color", "#d0513a"),
                ),
                True,
            ),
            about_us_text=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="About us text: Short blurb about freva.",
                    value=cfg.get("about_us_test", "Testing"),
                ),
                True,
            ),
            contacts=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Email address for admin(s) - comma seperated",
                    value=",".join(cfg.get("contatcs", ["admin@freva.dkrz.de"])),
                ),
                True,
            ),
            address=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Institution address, comma separated",
                    value=",".join(
                        cfg.get(
                            "address",
                            [
                                "freva",
                                "German Climate Computing Centre (DKRZ)",
                                "Bundesstr. 45a",
                                "20146 Hamburg",
                                "Germany",
                            ],
                        )
                    ),
                ),
                True,
            ),
            homepage_text=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="More in detail project describtion.",
                    value=cfg.get(
                        "homepage_text",
                        (
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
                ),
                True,
            ),
            home_page_heading=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="A brief describtion of the project",
                    value=cfg.get("home_page_heading", "Lorem ipsum dolor sit amet"),
                ),
                True,
            ),
            schduler_host=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Slurm scheduler hostname",
                    value=",".join(cfg.get("scheduler_host", ["mistral.dkrz.de"])),
                ),
                True,
            ),
            auth_ldap_server_uri=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=(
                        "Ldap server name(s) used for authentication - comma "
                        "separated"
                    ),
                    value=",".join(
                        cfg.get(
                            "auth_ldap_server_uri",
                            ["ldap://mldap0.hpc.dkrz.de", "ldap://mldap1.hpc.dkrz.de"],
                        )
                    ),
                ),
                True,
            ),
            auth_allowed_group=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Unix groups allowed to log on to the web:",
                    value=cfg.get("auth_allowed_group", "my_freva"),
                ),
                True,
            ),
            ldap_user_base=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Ldap search keys for user base",
                    value=cfg.get(
                        "ldap_user_base", "cn=users,cn=accounts,dc=dkrz,dc=de"
                    ),
                ),
                True,
            ),
            ldap_group_base=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Ldap search keys for group base",
                    value=cfg.get(
                        "ldap_group_base", "cn=groups,cn=accounts,dc=dkrz,dc=de",
                    ),
                ),
                True,
            ),
            ldap_user_dn=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Distinguished name (dn) for the ldap user",
                    value=cfg.get(
                        "ldap_user_dn",
                        "uid=dkrzagent,cn=sysaccounts,cn=etc,dc=dkrz,dc=de",
                    ),
                ),
                True,
            ),
            ldap_user_pw=(
                self.add_widget_intelligent(
                    npyscreen.TitlePassword,
                    name="Password for ldap user",
                    value=cfg.get("ldap_user_pw", "dkrzprox"),
                ),
                True,
            ),
            ansible_python_interpreter=(
                self.add_widget_intelligent(
                    npyscreen.TitleFilename,
                    name="Pythonpath on remote machine (leave blank for current path):",
                    value=cfg.get("ansible_python_interpreter", ""),
                ),
                False,
            ),
            ansible_user=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Remote login user (leave blank for current user):",
                    value=cfg.get("ansible_user", ""),
                ),
                False,
            ),
        )


class DBScreen(BaseForm):
    """Form for the core deployment configuration."""

    step: str = "db"
    def _add_widgets(self) -> None:
        """Add widgets to the screen."""
        self.list_keys = []
        cfg = self.get_config(self.step)
        db_ports: list[...,int] = list(range(3300, 3320))
        port_idx = get_index(db_ports, cfg.get("port", 3306), 6)
        self.input_fields: dict[str, tuple[npyscreen.TitleText, bool]] = dict(
            hosts=(
                self.add(
                    npyscreen.TitleText,
                    name="Server Name(s) where the database service is deployed:",
                    value=self.get_host("db"),
                ),
                True,
            ),
            user=(
                self.add(
                    npyscreen.TitleText,
                    name="Database user:",
                    value=cfg.get("user", "evaluation_system"),
                ),
                True,
            ),
            db=(
                self.add(
                    npyscreen.TitleText,
                    name="Database name:",
                    value=cfg.get("db", "evaluation_system")
            ),
            True,
            ),
            port=(
                self.add(
                    npyscreen.TitleCombo,
                    name="Database Port",
                    value=port_idx,
                    values=db_ports,
                ),
                True,
            ),
            ansible_python_interpreter=(
                self.add(
                    npyscreen.TitleFilename,
                    name="Pythonpath on remote machine (leave blank for current path):",
                    value=cfg.get("ansible_python_interpreter", ""),
                ),
                False,
            ),
            ansible_user=(
                self.add(
                    npyscreen.TitleText,
                    name="Remote login user (leave blank for current user):",
                    value=cfg.get("ansible_user", ""),
                ),
                False,
            ),
        )


class SolrScreen(BaseForm):
    """Form for the solr deployment configuration."""

    step: str = "solr"

    def _add_widgets(self) -> None:
        """Add widgets to the screen."""
        self.list_keys = []
        cfg = self.get_config(self.step)
        solr_ports: list[...,int] = list(range(8980, 9000))
        port_idx = get_index(solr_ports, cfg.get("port", 8983), 3)
        self.input_fields: dict[str, tuple[npyscreen.TitleText, bool]] = dict(
            hosts=(
                self.add(
                    npyscreen.TitleText,
                    name="Server Name(s) where the solr service is deployed:",
                    value=self.get_host("solr"),
                ),
                True,
            ),
            mem=(
                self.add(
                    npyscreen.TitleCombo,
                    name="Virtual memory (in GB) for the solr server:",
                    value=3,
                    values=[f"{i}g" for i in range(1, 10)],
                ),
                True,
            ),
            port=(
                self.add(
                    npyscreen.TitleCombo,
                    name="Solr port:",
                    value=port_idx,
                    values=solr_ports,
                ),
                True,
            ),
            core=(
                self.add(
                    npyscreen.TitleText,
                    name="Name of the standard solr core:",
                    value=cfg.get("core", "files"),
                ),
                True,
            ),
            ansible_python_interpreter=(
                self.add(
                    npyscreen.TitleFilename,
                    name="Pythonpath on remote machine (leave blank for current path):",
                    value=cfg.get("ansible_python_interpreter", ""),
                ),
                False,
            ),
            ansible_user=(
                self.add(
                    npyscreen.TitleText,
                    name="Remote login user (leave blank for current user):",
                    value=cfg.get("ansible_user", ""),
                ),
                False,
            ),
        )


class RunForm(npyscreen.FormMultiPageAction):
    """Definition of the form that applies the actual deployment."""

    def on_ok(self) -> None:
        """Define what happens once the `ok` for applying the deployment is hit."""
        if not self.project_name.value:
            npyscreen.notify_confirm("You have to set a project name", title="ERROR")
            return
        missing_form: None | str = self.parentApp.check_missing_config()
        if missing_form:
            self.parentApp.change_form(missing_form)
            return
        cert_file: str = self.cert_file.value or ""
        if cert_file:
            if not Path(cert_file).exists() or not Path(cert_file).is_file():
                msg = f"Public certificate file `{cert_file}` must exist or empty."
                npyscreen.notify_confirm(msg, title="ERROR")
                return
        self.parentApp._thread_stop.set()
        save_file = self.parentApp.save_config_to_file(write_toml_file=True)
        self.parentApp.setup = {
            "project_name": self.project_name.value,
            "steps": list(set(self.parentApp.steps)),
            "config_file": str(save_file) or None,
            "cert_file": str(cert_file) or None,
            "wipe": bool(self.wipe.value),
            "ask_pass": bool(self.use_ssh_pw.value),
        }
        self.parentApp.exit_application(msg="Do you want to continue?")

    def on_cancel(self) -> None:
        """Define what happens after the the cancel button is hit."""
        name = self.parentApp.current_form.lower()
        for step, form_name in self.parentApp._steps_lookup.items():
            if name.startswith(step):
                # Tell the MyTestApp object to change forms.
                self.parentApp.change_form(form_name)
                return
        self.parentApp.change_form("MAIN")

    def create(self) -> None:
        """Custom definitions executed when the from gets created."""
        self.how_exited_handers[
            npyscreen.wgwidget.EXITED_ESCAPE
        ] = self.parentApp.exit_application
        self._add_widgets()

    def _add_widgets(self) -> None:
        """Add the widgets to the form."""

        wipe = self.parentApp._read_cache("wipe", False)
        ssh_pw = self.parentApp._read_cache("ssh_pw", True)
        self.project_name = self.add(
            npyscreen.TitleText,
            name="Set the name of the project",
            value=self.parentApp._read_cache("project_name", ""),
        )
        self.inventory_file = self.add(
            npyscreen.TitleFilename,
            name="Save config as",
            value=str(self.parentApp.save_file),
        )
        self.cert_file = self.add(
            npyscreen.TitleFilename,
            name="Select a public certificate file, defaults to `<project_name>.crt`",
            value=str(self.parentApp.cert_file),
        )
        self.wipe = self.add(
            npyscreen.CheckBox,
            max_height=2,
            value=wipe,
            editable=True,
            name="Delete all existing data on docker volumes (wipe)",
            scroll_exit=True,
        )
        self.use_ssh_pw = self.add(
            npyscreen.CheckBox,
            max_height=2,
            value=ssh_pw,
            editable=True,
            name="Use password for ssh connection",
            scroll_exit=True,
        )
