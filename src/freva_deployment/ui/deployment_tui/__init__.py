"""Call the freva tui."""

from __future__ import annotations

import argparse
import logging

from freva_deployment.deploy import DeployFactory
from freva_deployment.error import DeploymentError
from freva_deployment.logger import logger, set_log_level

from .main_window import MainApp


def tui(args: argparse.Namespace) -> None:
    """Create and run Text User Interface (TUI) for deployment."""
    set_log_level(args.verbose)
    try:
        main_app = MainApp()
        main_app.run()
    except (KeyboardInterrupt, Exception) as error:
        try:
            main_app.thread_stop.set()
            main_app.save_config_to_file(
                save_file=main_app._setup_form.inventory_file.value
            )
        except AttributeError:
            pass
        if isinstance(error, KeyboardInterrupt):
            raise
        msg = str(error)
        if "addwstr" in msg:
            msg = (
                "Cloud not display content, try " "increasing your terminal size"
            )
        if logger.getEffectiveLevel() < logging.INFO:
            logger.exception(error)
        else:
            logger.error("Exiting App: %s", msg)
        return
    setup = main_app.setup
    main_app.thread_stop.set()
    if setup:
        ask_pass = setup.pop("ask_pass")
        ssh_port = setup.pop("ssh_port")
        skip_version_check = setup.pop("skip_version_check", False)
        with DeployFactory(_cowsay=args.cowsay, **setup) as DF:
            try:
                DF.play(
                    ask_pass,
                    args.verbose,
                    ssh_port=ssh_port,
                    skip_version_check=skip_version_check,
                )
            except KeyboardInterrupt:
                raise SystemExit(130)
            except DeploymentError:
                raise SystemExit(1)
