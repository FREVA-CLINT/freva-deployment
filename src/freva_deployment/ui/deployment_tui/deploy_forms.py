from __future__ import annotations

from getpass import getuser
from pathlib import Path
from typing import Dict, List, cast

import npyscreen

from freva_deployment import AVAILABLE_CONDA_ARCHS, AVAILABLE_PYTHON_VERSIONS
from freva_deployment.utils import get_current_file_dir

from .base import BaseForm, logger


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
    """Name of this step."""
    certificates: list[str] = ["public"]
    """The type of certificate files this step needs."""

    @property
    def scheduler_systems(self):
        """Define available scheduler systems."""
        return ["local", "slurm", "pbs", "lfs", "moab", "oar", "sge"]

    def scheduler_index(self, scheduler_system: str = ""):
        """Get the index of the saved scheduler_system"""
        scheduler_system = scheduler_system or "local"
        for nn, choice in enumerate(self.scheduler_systems):
            if choice == scheduler_system:
                return nn
        return 0

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
                    name=f"{self.num}Server Name(s) where core is deployed:",
                    value=self.get_host("core"),
                ),
                True,
            ),
            install_dir=(
                self.add_widget_intelligent(
                    npyscreen.TitleFilename,
                    name=f"{self.num}Anaconda installation dir. for core:",
                    value=cfg.get("install_dir", ""),
                ),
                True,
            ),
            root_dir=(
                self.add_widget_intelligent(
                    npyscreen.TitleFilename,
                    name=(
                        f"{self.num}Directory where project configuration is stored "
                        f"(defaults to `anaconda installation dir.` in #{self._num-1}):"
                    ),
                    value=cfg.get("root_dir", ""),
                ),
                False,
            ),
            base_dir_location=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=(
                        f"{self.num}User data directory, defaults to "
                        f"project config. dir given in #{self._num-1}."
                    ),
                    value=cfg.get("base_dir_location", ""),
                ),
                False,
            ),
            preview_path=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=(
                        f"{self.num}Plugin output dir for the web UI "
                        "(preview path), defaults to user data dir"
                        f" given in #{self._num - 1}."
                    ),
                    value=cfg.get("preview_path", ""),
                ),
                False,
            ),
            scheduler_system=(
                self.add_widget_intelligent(
                    npyscreen.TitleCombo,
                    name=f"{self.num}Workload manger",
                    value=self.scheduler_index(
                        cast(str, cfg.get("scheduler_system"))
                    ),
                    values=self.scheduler_systems,
                ),
                True,
            ),
            scheduler_output_dir=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Ouput dir. of the scheduler system, "
                    "${base_dir_location}/share",
                    value=cfg.get("scheduler_output_dir", ""),
                ),
                False,
            ),
            admins=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Set the admin user(s) - comma separated:",
                    value=cfg.get("admins", getuser()),
                ),
                False,
            ),
            admin_group=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=(
                        f"{self.num}Set the Freva admin group - "
                        "leave blank if not needed:"
                    ),
                    value=cfg.get("admin_group", ""),
                ),
                False,
            ),
            ansible_become_user=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=(
                        f"{self.num}Become (sudo) user name to change to on "
                        "remote machine, leave blank if not needed:"
                    ),
                    value=cfg.get("ansible_become_user", ""),
                ),
                False,
            ),
            arch=(
                self.add_widget_intelligent(
                    npyscreen.TitleCombo,
                    name=(
                        f"{self.num}Set the target architecture of the system where "
                        "the backend will be installed:"
                    ),
                    value=arch_idx,
                    values=AVAILABLE_CONDA_ARCHS,
                ),
                True,
            ),
            core_playbook=(
                self.add_widget_intelligent(
                    npyscreen.TitleFilename,
                    name=(
                        f"{self.num}Set the path to the playbook used for"
                        " setting up the system."
                    ),
                    value=cfg.get("core_playbook", ""),
                ),
                False,
            ),
            ansible_python_interpreter=(
                self.add_widget_intelligent(
                    npyscreen.TitleFilename,
                    name=f"{self.num}Python path on remote machine:",
                    value=cfg.get(
                        "ansible_python_interpreter", "/usr/bin/python3"
                    ),
                ),
                False,
            ),
            ansible_user=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Username for remote machine:",
                    value=cfg.get("ansible_user", getuser()),
                ),
                False,
            ),
            git_path=(
                self.add_widget_intelligent(
                    npyscreen.TitleFilename,
                    name=f"{self.num}Path to the git executable (leave blank for default):",
                    value=cfg.get("git_path", ""),
                ),
                False,
            ),
        )


class WebScreen(BaseForm):
    """Form for the web deployment configuration."""

    step: str = "web"
    certificates: list[str] = ["public", "private"]
    """The type of certificate files this step needs."""

    def get_index(self, choices: list[str], key: str):
        """Get the key value pair for a combo box"""
        for nn, choice in enumerate(choices):
            if choice == key:
                return nn
        return 0

    def _add_widgets(self) -> None:
        """Add widgets to the screen."""
        self.list_keys = "imprint", "scheduler_host", "allowed_hosts"
        cfg = self.get_config(self.step)
        for key in self.list_keys:
            if key in cfg and isinstance(cfg[key], str):
                value = cast(str, cfg[key])
                cfg[key] = [v.strip() for v in value.split(",") if v.strip()]
        availalbe_ldab_models = [
            "MiklipUserInformation",
            "UCARUserInformation",
            "DWDUserInformation",
            "FUUserInformation",
        ]
        current_ldab_model = get_index(
            availalbe_ldab_models,
            cast(str, cfg.get("ldap_model", "MiklipUserInformation")),
            0,
        )
        self.input_fields: dict[str, tuple[npyscreen.TitleText, bool]] = dict(
            hosts=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Server Name(s) the web service is deployed on:",
                    value=self.get_host("web"),
                ),
                True,
            ),
            data_path=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Parent directory for any permanent data:",
                    value=cast(str, cfg.get("data_path", "/opt/freva")),
                ),
                True,
            ),
            project_website=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Url of the Freva home page:",
                    value=cfg.get("project_website", ""),
                ),
                True,
            ),
            main_color=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Html color of the main color theme:",
                    value=cfg.get("main_color", "Tomato"),
                ),
                True,
            ),
            border_color=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Html color for the borders:",
                    value=cfg.get("border_color", "#6c2e1f"),
                ),
                True,
            ),
            hover_color=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Html color for hover modes:",
                    value=cfg.get("hover_color", "#d0513a"),
                ),
                True,
            ),
            institution_logo=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Path to the institution logo.",
                    value=cfg.get(
                        "institution_logo", "/path/to/logo/on/target/machine"
                    ),
                ),
                True,
            ),
            about_us_text=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}About us text - short blurb about Freva:",
                    value=cfg.get("about_us_text", "Testing"),
                ),
                True,
            ),
            contacts=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Contact email address:",
                    value=str(cfg.get("contacts", "data@dkrz.de")),
                ),
                True,
            ),
            email_host=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=(
                        f"{self.num}Smtp email that will be used to send "
                        "emails to the contacts via the web ui"
                    ),
                    value=cfg.get("email_host", "mailhost.dkrz.de"),
                ),
                True,
            ),
            imprint=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Institution address - comma separated:",
                    value=",".join(
                        cast(
                            List[str],
                            cfg.get(
                                "imprint",
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
                    name=f"{self.num}More in detail project description:",
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
            homepage_heading=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}A brief describtion of the project:",
                    value=cfg.get(
                        "homepage_heading", "Lorem ipsum dolor sit amet"
                    ),
                ),
                True,
            ),
            scheduler_host=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Scheduler hostname(s) - comma separated:",
                    value=",".join(
                        cast(
                            List[str],
                            cfg.get("scheduler_host", ["levante.dkrz.de"]),
                        )
                    ),
                ),
                True,
            ),
            allowed_hosts=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Set additional hostnames django can serve:",
                    value=",".join(
                        cast(
                            List[str],
                            cfg.get("allowed_hosts", ["localhost"]),
                        ),
                    ),
                ),
                True,
            ),
            auth_ldap_server_uri=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=(
                        f"{self.num}Ldap server name(s) used for authentication"
                        " - comma separated:"
                    ),
                    value=cfg.get(
                        "auth_ldap_server_uri",
                        "ldap://idm-dmz.dkrz.de",
                    ),
                ),
                True,
            ),
            auth_ldap_start_tls=(
                self.add_widget_intelligent(
                    npyscreen.RoundCheckBox,
                    max_height=2,
                    value=cfg.get("auth_ldap_start_tls", False),
                    editable=True,
                    name=(
                        f"{self.num}Enable TLS encryption when communicating with the"
                        "ldap server. Needs to be configured:"
                    ),
                    scroll_exit=True,
                ),
                True,
            ),
            allowed_group=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Unix group allowed to log on to the web:",
                    value=cfg.get("allowed_group", "my_freva"),
                ),
                False,
            ),
            ldap_user_base=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Ldap search keys for user base:",
                    value=cfg.get(
                        "ldap_user_base", "cn=users,cn=accounts,dc=dkrz,dc=de"
                    ),
                ),
                True,
            ),
            ldap_group_base=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Ldap search keys for group base:",
                    value=cfg.get(
                        "ldap_group_base",
                        "cn=groups,cn=accounts,dc=dkrz,dc=de",
                    ),
                ),
                True,
            ),
            ldap_user_dn=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Distinguished name (dn) for the ldap user:",
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
                    name=f"{self.num}Password for ldap user:",
                    value=cfg.get("ldap_user_pw", ""),
                ),
                False,
            ),
            ldap_first_name_field=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=(f"{self.num}Ldap search search key for first name"),
                    value=cfg.get(
                        "ldap_first_name_field",
                        "givenname",
                    ),
                ),
                False,
            ),
            ldap_last_name_field=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=(f"{self.num}Ldap search search key for last name"),
                    value=cfg.get(
                        "ldap_last_name_field",
                        "sn",
                    ),
                ),
                False,
            ),
            ldap_email_field=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=(f"{self.num}Ldap search search key for email addr"),
                    value=cfg.get(
                        "ldap_email_name_field",
                        "mail",
                    ),
                ),
                False,
            ),
            ldap_group_class=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=(f"{self.num}Ldap object class"),
                    value=cfg.get(
                        "ldap_group_class",
                        "groupOfNames",
                    ),
                ),
                True,
            ),
            ldap_group_type=(
                self.add_widget_intelligent(
                    npyscreen.TitleCombo,
                    name=(f"{self.num}Ldap group type"),
                    value=self.get_index(
                        ["posix", "nested"],
                        cast(str, cfg.get("ldap_group_type", "nested")),
                    ),
                    values=["posix", "nested"],
                ),
                True,
            ),
            ldap_model=(
                self.add_widget_intelligent(
                    npyscreen.TitleCombo,
                    name=(
                        f"{self.num}Ldap tools class to be used for authentication."
                    ),
                    value=current_ldab_model,
                    values=availalbe_ldab_models,
                ),
                True,
            ),
            web_playbook=(
                self.add_widget_intelligent(
                    npyscreen.TitleFilename,
                    name=(
                        f"{self.num}Set the path to the playbook used for"
                        " setting up the system."
                    ),
                    value=cfg.get("web_playbook", ""),
                ),
                False,
            ),
            ansible_become_user=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=(
                        f"{self.num}Become (sudo) user name to change to on "
                        "remote machine, leave blank for root less deployment:"
                    ),
                    value=cfg.get("ansible_become_user", "root"),
                ),
                False,
            ),
            ansible_python_interpreter=(
                self.add_widget_intelligent(
                    npyscreen.TitleFilename,
                    name=f"{self.num}Pythonpath on remote machine:",
                    value=cfg.get(
                        "ansible_python_interpreter", "/usr/bin/python3"
                    ),
                ),
                False,
            ),
            ansible_user=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Username for remote machine:",
                    value=cfg.get("ansible_user", getuser()),
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
            cast(List[str], list(map(str, db_ports))),
            str(cfg.get("port", 3306)),
            6,
        )
        self.input_fields: dict[str, tuple[npyscreen.TitleText, bool]] = dict(
            hosts=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Server Name(s) where the database service is deployed:",
                    value=self.get_host("db"),
                ),
                True,
            ),
            wipe=(
                self.add_widget_intelligent(
                    npyscreen.RoundCheckBox,
                    max_height=2,
                    value=cfg.get("wipe", False),
                    editable=True,
                    name=(f"{self.num}Delete existing data?"),
                    scroll_exit=True,
                ),
                True,
            ),
            user=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Database user:",
                    value=cfg.get("user", "evaluation_system"),
                ),
                True,
            ),
            db=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Database name:",
                    value=cfg.get("db", "evaluation_system"),
                ),
                True,
            ),
            port=(
                self.add_widget_intelligent(
                    npyscreen.TitleCombo,
                    name=f"{self.num}Database Port:",
                    value=port_idx,
                    values=db_ports,
                ),
                True,
            ),
            data_path=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=(
                        f"{self.num}Parent directory for any permanent data:"
                    ),
                    value=cast(str, cfg.get("data_path", "/opt/freva")),
                ),
                True,
            ),
            db_playbook=(
                self.add_widget_intelligent(
                    npyscreen.TitleFilename,
                    name=(
                        f"{self.num}Set the path to the db playbook used for"
                        " setting up the system."
                    ),
                    value=cfg.get("db_playbook", ""),
                ),
                False,
            ),
            ansible_become_user=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=(
                        f"{self.num}Become (sudo) user name to change to on "
                        "remote machine, leave blank for root less deployment:"
                    ),
                    value=cfg.get("ansible_become_user", "root"),
                ),
                False,
            ),
            ansible_python_interpreter=(
                self.add_widget_intelligent(
                    npyscreen.TitleFilename,
                    name=f"{self.num}Pythonpath on remote machine:",
                    value=cfg.get(
                        "ansible_python_interpreter", "/usr/bin/python3"
                    ),
                ),
                False,
            ),
            ansible_user=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Username for remote machine:",
                    value=cfg.get("ansible_user", getuser()),
                ),
                False,
            ),
        )


class DatabrowserScreen(BaseForm):
    """Form for the databrowser deployment configuration."""

    step: str = "databrowser"

    def _add_widgets(self) -> None:
        """Add widgets to the screen."""
        self.list_keys: list[str] = []
        cfg = self.get_config(self.step)
        databrowser_ports: list[int] = list(range(7770, 7780))
        solr_mem_values = [f"{i}g" for i in range(1, 10)]
        solr_mem_select = get_index(
            cast(str, solr_mem_values, cfg.get("solr_mem", "4g")), 3
        )
        databrowser_port_idx = get_index(
            [str(p) for p in databrowser_ports],
            str(cfg.get("databrowser_port", 7777)),
            7,
        )
        self.input_fields: dict[str, tuple[npyscreen.TitleText, bool]] = dict(
            hosts=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Server Name(s) where the databrowser service is deployed:",
                    value=self.get_host("databrowser"),
                ),
                True,
            ),
            wipe=(
                self.add_widget_intelligent(
                    npyscreen.RoundCheckBox,
                    max_height=2,
                    value=cfg.get("wipe", False),
                    editable=True,
                    name=(f"{self.num}Delete existing data?"),
                    scroll_exit=True,
                ),
                True,
            ),
            solr_mem=(
                self.add_widget_intelligent(
                    npyscreen.TitleCombo,
                    name=f"{self.num}Virtual memory (in GB) for the search engine service:",
                    value=solr_mem_select,
                    values=solr_mem_values,
                ),
                True,
            ),
            databrowser_port=(
                self.add_widget_intelligent(
                    npyscreen.TitleCombo,
                    name=f"{self.num}Databrowser API port:",
                    value=databrowser_port_idx,
                    values=databrowser_ports,
                ),
                True,
            ),
            data_path=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Parent directory for any permanent data:",
                    value=cast(str, cfg.get("data_path", "/opt/freva")),
                ),
                True,
            ),
            databrowser_playbook=(
                self.add_widget_intelligent(
                    npyscreen.TitleFilename,
                    name=(
                        f"{self.num}Set the path to the playbook used for"
                        " setting up the system."
                    ),
                    value=cfg.get("databrowser_playbook", ""),
                ),
                False,
            ),
            ansible_become_user=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=(
                        f"{self.num}Become (sudo) user name to change to on "
                        "remote machine, leave blank for root less deployment:"
                    ),
                    value=cfg.get("ansible_become_user", "root"),
                ),
                False,
            ),
            ansible_python_interpreter=(
                self.add_widget_intelligent(
                    npyscreen.TitleFilename,
                    name=f"{self.num}Pythonpath on remote machine:",
                    value=cfg.get(
                        "ansible_python_interpreter", "/usr/bin/python3"
                    ),
                ),
                False,
            ),
            ansible_user=(
                self.add_widget_intelligent(
                    npyscreen.TitleText,
                    name=f"{self.num}Username for remote machine:",
                    value=cfg.get("ansible_user", getuser()),
                ),
                False,
            ),
        )


class RunForm(npyscreen.FormMultiPageAction):
    """Definition of the form that applies the actual deployment."""

    _num: int = 0

    @property
    def num(self) -> str:
        """Calculate the number for enumerations of any input field."""
        self._num += 1
        return f"{self._num}. "

    def on_ok(self) -> None:
        """Define what happens once the `ok` for applying the deployment is hit."""

        self.parentApp.thread_stop.set()
        if not self.project_name.value:
            npyscreen.notify_confirm(
                "You have to set a project name", title="ERROR"
            )
            return
        missing_form: None | str = self.parentApp.check_missing_config()
        if missing_form:
            self.parentApp.change_form(missing_form)
            return
        public_keyfile = self.public_keyfile.value
        cert_files = dict(
            public=public_keyfile or "",
            private=self.private_keyfile.value or "",
        )
        save_file = Path(
            self.parentApp.get_save_file(self.inventory_file.value or None)
        )
        if isinstance(self.gen_keys.value, list):
            gen_keys = bool(self.gen_keys.value[0])
        else:
            gen_keys = bool(self.gen_keys.value)
        for key_type, keyfile in cert_files.items():
            key_file = Path(
                get_current_file_dir(save_file.parent, str(keyfile))
            )
            for step, deploy_form in self.parentApp._forms.items():
                if not keyfile or not Path(key_file).is_file():
                    if (
                        key_type in deploy_form.certificates
                        and step in self.parentApp.steps
                        and gen_keys is False
                    ):
                        if keyfile:
                            msg = f"{key_type} certificate file `{key_file}` must exist."
                        else:
                            msg = (
                                f"You must give a {key_type} certificate file."
                            )
                        npyscreen.notify_confirm(msg, title="ERROR")
                        return
        _ = self.parentApp.save_config_to_file(
            save_file=save_file, write_toml_file=True
        )
        try:
            ssh_port = int(self.ssh_port.value)
        except ValueError:
            ssh_port = 22
        self.parentApp.setup = {
            "steps": list(set(self.parentApp.steps)),
            "ask_pass": bool(self.use_ssh_pw.value),
            "config_file": str(save_file) or None,
            "ssh_port": ssh_port,
            "local_debug": bool(self.local_debug.value),
            "gen_keys": bool(gen_keys),
        }
        self.parentApp.exit_application(
            save_file=save_file, msg="Do you want to continue?"
        )

    def on_cancel(self) -> None:
        """Define what happens after the the cancel button is hit."""
        name = self.parentApp.current_form.lower()
        self.parentApp.setup = {}
        for step, form_name in self.parentApp._steps_lookup.items():
            if name.startswith(step):
                # Tell the MyTestApp object to change forms.
                self.parentApp.change_form(form_name)
                return
        self.parentApp.change_form("MAIN")

    def create(self) -> None:
        """Custom definitions executed when the from gets created."""
        self.how_exited_handers[npyscreen.wgwidget.EXITED_ESCAPE] = (
            self.parentApp.exit_application
        )
        self._add_widgets()

    def _add_widgets(self) -> None:
        """Add the widgets to the form."""

        project_name = self.parentApp.config.get(
            "project_name", self.parentApp._read_cache("project_name", "")
        )
        self.project_name = self.add_widget_intelligent(
            npyscreen.TitleText,
            name=f"{self.num}Set the name of the project",
            value=project_name,
        )
        self.inventory_file = self.add_widget_intelligent(
            npyscreen.TitleFilename,
            name=f"{self.num}Save config as",
            value=str(self.parentApp.save_file or ""),
        )
        self.public_keyfile = self.add_widget_intelligent(
            npyscreen.TitleFilename,
            name=f"{self.num}Select a public certificate file; needed for steps web, core, db",
            value=self.parentApp.read_cert_file("public_keyfile"),
        )
        self.private_keyfile = self.add_widget_intelligent(
            npyscreen.TitleFilename,
            name=f"{self.num}Select a private certificate file; needed for steps web",
            value=self.parentApp.read_cert_file("private_keyfile"),
        )
        self.gen_keys = self.add_widget_intelligent(
            npyscreen.RoundCheckBox,
            max_height=2,
            value=self.parentApp._read_cache("gen_keys", False),
            name=f"{self.num}Generate a pair web certificates, debugging",
        )
        self.use_ssh_pw = self.add_widget_intelligent(
            npyscreen.RoundCheckBox,
            max_height=2,
            editable=True,
            value=self.parentApp._read_cache("ssh_pw", False),
            name=f"{self.num}Use password for ssh connection",
            scroll_exit=True,
        )
        self.ssh_port = self.add_widget_intelligent(
            npyscreen.TitleText,
            name=f"{self.num}If you need to, you can change the ssh port here",
            value=str(self.parentApp._read_cache("ssh_port", 22)),
        )
        self.local_debug = self.add_widget_intelligent(
            npyscreen.RoundCheckBox,
            max_height=2,
            value=self.parentApp._read_cache("local_debug", False),
            editable=True,
            name=f"{self.num}Deploy services on the local machine, debug",
        )
