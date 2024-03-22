"""Definition of the logger."""

import logging

from rich.console import Console
from rich.logging import RichHandler

logger_stream_handle = RichHandler(
    rich_tracebacks=True,
    show_path=False,
    console=Console(soft_wrap=True, stderr=True),
)
logging.basicConfig(
    format="%(name)s - %(message)s",
    level=logging.INFO,
    handlers=[logger_stream_handle],
    datefmt="[%X]",
)
logger = logging.getLogger("freva-deployment")


def set_log_level(verbosity: int) -> None:
    """Set the log level of the logger."""
    logger.setLevel(max(logging.INFO - 10 * verbosity, logging.DEBUG))
