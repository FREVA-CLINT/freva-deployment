from __future__ import annotations
from getpass import getuser
import npyscreen
from pathlib import Path
from typing import cast, List, Dict

from .base import BaseForm, logger
from freva_deployment import AVAILABLE_PYTHON_VERSIONS, AVAILABLE_CONDA_ARCHS


def get_index(values: list[str], target: str, default: int = 0) -> int:
    """Get the target index of item in list.

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
        self.list_keys: list[str] = []
        cfg = self.get_config(self.step)
        arch = cast(str, cfg.get("arch", AVAILABLE_CONDA_ARCHS[0]))
        arch_idx = get_index(AVAILABLE_CONDA_ARCHS, arch, 0)
        self.input_fields: dict[str, tuple[npyscreen.TitleText, bool]] = dict(
            hosts=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Server Name(s) where core is deployed:",
                    value=self.get_host("core"),
                ),
                True,
            ),
            branch=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Deploy branch:",
                    value=cfg.get("branch", "freva-dev"),
                ),
                True,
            ),
            install_dir=(
                self.add_widget_intelligent(
                    npyscreen.TitleFilename,
                    name="Anaconda installation dir. for core:",
                    value=cfg.get("install_dir", ""),
                ),
                True,
            ),
            install=(
                self.add_widget_intelligent(
                    npyscreen.CheckBox,
                    max_height=2,
                    value=cfg.get("install", True),
                    editable=True,
                    name=(
                        "Install a new instance of the core, or just add a new "
                        "configuration."
                    ),
                    scroll_exit=True,
                ),
                True,
            ),
            root_dir=(
                self.add_widget_intelligent(
                    npyscreen.TitleFilename,
                    name=(
                        "Project configuration file directory "
                        "defaults to `intallation directory`:"
                    ),
                    value=cfg.get("root_dir", ""),
                ),
                False,
            ),
            base_dir_location=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Plugin data directory (user work dir.):",
                    value=cfg.get("base_dir_location", ""),
                ),
                True,
            ),
            admins=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Set the admin user(s) - comma separated",
                    value=cfg.get("admins", getuser()),
                ),
                False,
            ),
            admin_group=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=("Set the freva admin group, " "leave blank if not needed."),
                    value=cfg.get("admin_group", ""),
                ),
                False,
            ),
            ansible_become_user=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=(
                        "Set a (additional) username that has privileges "
                        "to install the core"
                    ),
                    value=cfg.get("ansible_become_user", ""),
                ),
                False,
            ),
            conda_exec_path=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=(
                        "Path any existing conda installation. "
                        "Leave blank to "
                        "install a temporary conda distribution"
                    ),
                    value=cfg.get("conda_exec_path", ""),
                ),
                False,
            ),
            arch=(
                self.add_widget_intelligent(
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
            git_path=(
                self.add_widget_intelligent(
                    npyscreen.TitleFilename,
                    name="Path to the git executable (leave blank for default):",
                    value=cfg.get("git_path", "git"),
                ),
                False,
            ),
        )


class WebScreen(BaseForm):
    """Form for the web deployment configuration."""

    step: str = "web"

    def _add_widgets(self) -> None:
        """Add widgets to the screen."""
        self.list_keys = "contacts", "address", "scheduler_host"
        cfg = self.get_config(self.step)
        for key in self.list_keys:
            if key in cfg and isinstance(cfg[key], str):
                value = cast(str, cfg[key])
                cfg[key] = [v.strip() for v in value.split(",") if v.strip()]
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
            project_website=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Url of the freva home page:",
                    value=cfg.get("project_website", ""),
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
                    value=",".join(
                        cast(List[str], cfg.get("contatcs", ["admin@freva.dkrz.de"]))
                    ),
                ),
                True,
            ),
            address=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Institution address, comma separated",
                    value=",".join(
                        cast(
                            List[str],
                            cfg.get(
                                "address",
                                [
                                    "freva",
                                    "German Climate Computing Centre (DKRZ)",
                                    "Bundesstr. 45a",
                                    "20146 Hamburg",
                                    "Germany",
                                ],
                            ),
                        ),
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
            scheduler_host=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Slurm scheduler hostname",
                    value=",".join(
                        cast(List[str], cfg.get("scheduler_host", ["levante.dkrz.de"]))
                    ),
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
                    value=cfg.get(
                        "auth_ldap_server_uri",
                        "ldap://mldap0.hpc.dkrz.de, ldap://mldap1.hpc.dkrz.de",
                    ),
                ),
                True,
            ),
            auth_ldap_start_tls=(
                self.add_widget_intelligent(
                    npyscreen.CheckBox,
                    max_height=2,
                    value=cfg.get("auth_ldap_start_tls", False),
                    editable=True,
                    name=(
                        "Enable TLS encryption when communicating with the"
                        "ldap server. Needs to be configured."
                    ),
                    scroll_exit=True,
                ),
                True,
            ),
            allowed_group=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Unix groups allowed to log on to the web:",
                    value=cfg.get("allowed_group", "my_freva"),
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
        self.list_keys: list[str] = []
        cfg = self.get_config(self.step)
        db_ports: list[int] = list(range(3300, 3320))
        port_idx = get_index(
            cast(List[str], list(map(str, db_ports))), str(cfg.get("port", 3306)), 6
        )
        self.input_fields: dict[str, tuple[npyscreen.TitleText, bool]] = dict(
            hosts=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Server Name(s) where the database service is deployed:",
                    value=self.get_host("db"),
                ),
                True,
            ),
            user=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Database user:",
                    value=cfg.get("user", "evaluation_system"),
                ),
                True,
            ),
            db=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Database name:",
                    value=cfg.get("db", "evaluation_system"),
                ),
                True,
            ),
            port=(
                self.add_widget_intelligent(
                    npyscreen.TitleCombo,
                    name="Database Port",
                    value=port_idx,
                    values=db_ports,
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


class SolrScreen(BaseForm):
    """Form for the solr deployment configuration."""

    step: str = "solr"

    def _add_widgets(self) -> None:
        """Add widgets to the screen."""
        self.list_keys: list[str] = []
        cfg = self.get_config(self.step)
        solr_ports: list[int] = list(range(8980, 9000))
        port_idx = get_index(
            [str(p) for p in solr_ports], str(cfg.get("port", 8983)), 3
        )
        self.input_fields: dict[str, tuple[npyscreen.TitleText, bool]] = dict(
            hosts=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Server Name(s) where the solr service is deployed:",
                    value=self.get_host("solr"),
                ),
                True,
            ),
            mem=(
                self.add_widget_intelligent(
                    npyscreen.TitleCombo,
                    name="Virtual memory (in GB) for the solr server:",
                    value=3,
                    values=[f"{i}g" for i in range(1, 10)],
                ),
                True,
            ),
            port=(
                self.add_widget_intelligent(
                    npyscreen.TitleCombo,
                    name="Solr port:",
                    value=port_idx,
                    values=solr_ports,
                ),
                True,
            ),
            core=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name="Name of the standard solr core:",
                    value=cfg.get("core", "files"),
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


class RunForm(npyscreen.FormMultiPageAction):
    """Definition of the form that applies the actual deployment."""

    def on_ok(self) -> None:
        """Define what happens once the `ok` for applying the deployment is hit."""
        if not self.project_name.value:
            npyscreen.notify_confirm("You have to set a project name", title="ERROR")
            return
        if not self.server_map.value:
            value = npyscreen.notify_yes_no(
                "If you don't set a map server value you wont be able "
                "to start|stop the services. Continue anyway?",
                title="WARNING",
            )
            if not value:
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
        self.parentApp.thread_stop.set()
        save_file = self.parentApp.save_config_to_file(write_toml_file=True)
        self.parentApp.setup = {
            "project_name": self.project_name.value,
            "server_map": self.server_map.value,
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
        self.project_name = self.add_widget_intelligent(
            npyscreen.TitleText,
            name="Set the name of the project",
            value=self.parentApp._read_cache("project_name", ""),
        )
        self.inventory_file = self.add_widget_intelligent(
            npyscreen.TitleFilename,
            name="Save config as",
            value=str(self.parentApp.save_file),
        )
        self.server_map = self.add_widget_intelligent(
            npyscreen.TitleText,
            name=("Hostname of the service mapping the freva server arch."),
            value=self.parentApp._read_cache("server_map", ""),
        )
        self.cert_file = self.add_widget_intelligent(
            npyscreen.TitleFilename,
            name="Select a public certificate file, defaults to `<project_name>.crt`",
            value=str(self.parentApp.cert_file),
        )
        self.wipe = self.add_widget_intelligent(
            npyscreen.CheckBox,
            max_height=2,
            value=wipe,
            editable=True,
            name="Delete all existing data on docker volumes (wipe)",
            scroll_exit=True,
        )
        self.use_ssh_pw = self.add_widget_intelligent(
            npyscreen.CheckBox,
            max_height=2,
            value=ssh_pw,
            editable=True,
            name="Use password for ssh connection",
            scroll_exit=True,
        )
