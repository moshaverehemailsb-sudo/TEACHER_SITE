import logging

from app.config import config_warnings


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    for warning in config_warnings():
        logging.getLogger("baf.config").warning(warning)