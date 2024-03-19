"""Call the freva tui."""

from __future__ import annotations

import argparse

from freva_deployment import __version__
from freva_deployment.deploy import DeployFactory
from freva_deployment.utils import RichConsole, set_log_level
from freva_deployment.versions import VersionAction, display_versions

from .main_window import MainApp


def parse_args() -> int:
    """Construct command line argument parser."""
    app = argparse.ArgumentParser(
        prog="deploy-freva",
        description="Text User Interface for Freva deployment",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    app.add_argument(
        "-v", "--verbose", action="count", help="Verbosity level", default=0
    )
    app.add_argument(
        "-V",
        "--version",
        action=VersionAction,
        version="%(prog)s [b]{version}[/b]{services}".format(
            version=__version__, services=display_versions()
        ),
    )
    parser = app.parse_args()
    return parser.verbose


def tui() -> None:
    """Create and run Text User Interface (TUI) for deployment."""
    verbosity = parse_args()
    set_log_level(verbosity)
    try:
        main_app = MainApp()
        main_app.run()
    except KeyboardInterrupt:
        try:
            main_app.thread_stop.set()
            main_app.save_config_to_file(
                save_file=main_app._setup_form.inventory_file.value
            )
        except AttributeError:
            pass
        return
    setup = main_app.setup
    main_app.thread_stop.set()
    if setup:
        ask_pass = setup.pop("ask_pass")
        steps = ", ".join(setup["steps"])
        ssh_port = setup.pop("ssh_port")
        RichConsole.print(f"Playing steps: [i]{steps}[/] with ansible")
        with DeployFactory(**setup) as DF:
            DF.play(ask_pass, verbosity, ssh_port=ssh_port)
