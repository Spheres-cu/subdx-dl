import os
import requests
import certifi

from hashlib import md5
from sdx_dl.sdxlogger import logger

__all__ = ["get_public_ip", "md5_hash"]


def md5_hash(text: str | bytes) -> str:
    if isinstance(text, str):
        text = text.encode('utf-8')
    return md5(text).hexdigest()


def get_public_ip(proxy: str | None = None):
    """Get hostname public ip"""

    services = [
        'https://api.ipify.org',
        'https://checkip.amazonaws.com'
    ]
    proxies = {'http': proxy, 'https': proxy} if proxy else None
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
    session = requests.Session()
    session.headers.update({
        'Accept': 'text/html,application/xhtml+xml,application/xml',
        'Content-Type': 'text/plain',
        'User-Agent': ua
    })

    for service in services:
        try:
            response = session.get(service, timeout=10, proxies=proxies, verify=certifi.where())
            response.raise_for_status()  # Raise an exception for bad status codes
            ip = response.text.strip()
            # Basic validation that it looks like an IP address
            if ip.count('.') == 3 and all(part.isdigit() for part in ip.split('.')):
                return ip
        except requests.RequestException as e:
            logger.debug(f"Failed to get IP from {service}: {e}")
            continue

    return None


def clean_screen() -> None:
    """Clean the screen"""
    os.system('clear' if os.name != 'nt' else 'cls')
