from .main_window import MainApp


def tui() -> None:
    """Create and run text user interface (tui) for deployment."""
    try:
        main_app = MainApp()
        main_app.run()
    except KeyboardInterrupt:
        pass
    if main_app.setup:
        print(main_app.setup)
