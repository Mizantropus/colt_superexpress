"""Настройка логирования приложения."""

import logging


def configure_logging(level: str = "INFO") -> None:
    """Настраивает корневой логгер приложения."""
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        force=True,
    )