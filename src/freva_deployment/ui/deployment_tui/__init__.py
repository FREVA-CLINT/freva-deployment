from __future__ import annotations
from .main_window import MainApp
from freva_deployment.deploy import DeployFactory

def tui() -> None:
    """Create and run text user interface (tui) for deployment."""
    try:
        main_app = MainApp()
        main_app.run()
    except KeyboardInterrupt:
        pass
    setup = main_app.setup
    if setup:
        project_name = setup.pop("project_name")
        with DeployFactory(project_name, **setup) as DF:
            DF.play()
