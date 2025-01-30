import logging
import coloredlogs

log_styles = {
    "debug": {"color": "green"},
    "info": {"color": "blue"},
    "warning": {"color": "yellow"},
    "error": {"color": "red"},
    "critical": {"color": "magenta", "bold": True},
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

coloredlogs.install(
    level="DEBUG",
    logger=logger,
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level_styles=log_styles,
)
