# Copyright (C) 2025 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import logging
import tempfile

from sdx_dl.sdxconsole import console
from rich.logging import RichHandler
from rich.traceback import install
install(show_locals=True)

__all__ = ["create_logger", "logger"]


def create_logger(level: str = "DEBUG", verbose: bool = False, mode: str = 'w') -> logging.Logger:

    # Setting logger
    levels = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
    LOGGER_LEVEL = levels[4]
    LOGGER_FORMATTER_LONG = logging.Formatter('%(asctime)-12s %(levelname)-6s %(message)s', '%Y-%m-%d %H:%M:%S')
    LOGGER_FORMATTER_SHORT = logging.Formatter(fmt='%(message)s', datefmt="[%X]")

    level = level if level in levels else LOGGER_LEVEL
    temp_log_dir = tempfile.gettempdir()
    file_log = os.path.join(temp_log_dir, 'subdx-dl.log')

    log = logging.getLogger(__name__)
    log.setLevel(level)

    if not verbose:
        logfile = logging.FileHandler(file_log, mode=mode, encoding='utf-8')
        logfile.setFormatter(LOGGER_FORMATTER_LONG)
        logfile.setLevel(level)
        log.addHandler(logfile)
    else:
        terminal = RichHandler(console=console, rich_tracebacks=True, tracebacks_show_locals=True)
        terminal.setFormatter(LOGGER_FORMATTER_SHORT)
        terminal.setLevel(level)
        log.addHandler(terminal)

    return log


logger = create_logger(mode='a')
