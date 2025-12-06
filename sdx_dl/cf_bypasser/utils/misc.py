import os
import logging
import typing
import asyncio
import tempfile
import requests

from hashlib import md5
from rich.logging import RichHandler
from rich.traceback import install
install(show_locals=True)


def md5_hash(text: str | bytes) -> str:
    if isinstance(text, str):
        text = text.encode('utf-8')
    return md5(text).hexdigest()


@typing.no_type_check
def get_browser_init_lock() -> asyncio.Lock:
    """Get the global browser initialization lock for the current event loop."""

    # Global lock state for browser initialization
    global _global_lock_state
    _global_lock_state = {"lock": None, "loop": None}

    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.Lock()

    if _global_lock_state["lock"] is None or _global_lock_state["loop"] != current_loop:
        _global_lock_state["lock"] = asyncio.Lock()
        _global_lock_state["loop"] = current_loop

    return _global_lock_state["lock"]


def create_logger(level: str = "DEBUG", verbose: bool = False):

    # Setting logger
    levels = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
    LOGGER_LEVEL = levels[4]
    LOGGER_FORMATTER_LONG = logging.Formatter('%(asctime)-12s %(levelname)-6s %(message)s', '%Y-%m-%d %H:%M:%S')
    LOGGER_FORMATTER_SHORT = logging.Formatter(fmt='%(message)s', datefmt="[%X]")

    level = level if level in levels else LOGGER_LEVEL
    temp_log_dir = tempfile.gettempdir()
    file_log = os.path.join(temp_log_dir, 'subdx-dl.log')

    global logger
    logger = logging.getLogger(__name__)
    logger.setLevel(level)

    if not verbose:
        logfile = logging.FileHandler(file_log, mode='w', encoding='utf-8')
        logfile.setFormatter(LOGGER_FORMATTER_LONG)
        logfile.setLevel(level)
        logger.addHandler(logfile)
    else:
        console = RichHandler(rich_tracebacks=True, show_path=False)
        console.setFormatter(LOGGER_FORMATTER_SHORT)
        console.setLevel(level)
        logger.addHandler(console)


create_logger()


def get_public_ip(proxy: str | None = None):
    """Get hostname public ip"""

    services = [
        'https://api.ipify.org',
        'https://checkip.amazonaws.com'
    ]
    proxies = {'http': proxy, 'https': proxy} if proxy else None

    for service in services:
        try:
            response = requests.get(service, timeout=10, proxies=proxies)
            response.raise_for_status()  # Raise an exception for bad status codes
            ip = response.text.strip()
            # Basic validation that it looks like an IP address
            if ip.count('.') == 3 and all(part.isdigit() for part in ip.split('.')):
                return ip
        except requests.RequestException as e:
            logger.debug(f"Failed to get IP from {service}: {e}")
            continue

    return None
