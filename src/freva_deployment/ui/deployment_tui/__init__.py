"""Call the freva tui."""
from __future__ import annotations
import argparse

from freva_deployment.deploy import DeployFactory
from freva_deployment.utils import set_log_level
from .main_window import MainApp


def parse_args() -> int:
    """Consturct command line argument parser."""
    app = argparse.ArgumentParser(
        prog="deploy-freva",
        description="Text User Interfave for freva deployment",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    app.add_argument(
        "-v", "--verbose", action="count", help="Verbosity level", default=0
    )
    parser = app.parse_args()
    return parser.verbose


def tui() -> None:
    """Create and run text user interface (tui) for deployment."""

    verbosity = set_log_level(parse_args())
    try:
        main_app = MainApp()
        main_app.run()
    except KeyboardInterrupt:
        try:
            main_app.thread_stop.set()
            main_app.save_config_to_file()
        except AttributeError:
            pass
        return
    setup = main_app.setup
    if setup:
        project_name = setup.pop("project_name")
        server_map = setup.pop("server_map")
        with DeployFactory(project_name, **setup) as DF:
            DF.play(server_map, verbosity)
