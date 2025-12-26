import os
import re
import sys
import time
import json

from pathlib import Path
from sdx_dl.cf_bypasser.CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage, ChromiumOptions
from DrissionPage._functions.settings import Settings
from sdx_dl.cf_bypasser.cache.cookie_cache import CookieCache
from sdx_dl.cf_bypasser.utils.misc import md5_hash, get_public_ip, clean_screen
from sdx_dl.sdxconsole import console
from sdx_dl.sdxlocale import gl
from sdx_dl.sdxlogger import logger
from urllib.parse import urlparse
from typing import Any
from bs4 import BeautifulSoup


SUBDIVX_PAGE = 'https://www.subdivx.com/'


__all__ = ["get_cf_bypass", "manual_bypasser"]


def get_cache_path(app_name: str = "subdx-dl", file_name: str | None = "sdx_cache_connection.json") -> Path:
    """Get platform-specific cache directory"""
    if sys.platform == "win32":
        base_dir = Path(f'{os.getenv("LOCALAPPDATA")}')
    elif sys.platform == "darwin":
        base_dir = Path.home() / "Library" / "Caches"
    else:
        base_dir = Path.home() / ".cache"

    cache_dir = base_dir / app_name

    if not os.path.isdir(cache_dir):
        cache_dir.mkdir(parents=True, exist_ok=True)

    if file_name:
        cache_dir = cache_dir / file_name
        if not os.path.isfile(cache_dir):
            with open(cache_dir, 'w') as file:
                file.write('')
                file.close()

    return cache_dir


def get_chromium_options(browser_path: str, arguments: list[str]) -> ChromiumOptions:
    """
    Configures and returns Chromium options.

    :param browser_path: Path to the Chromium browser executable.
    :param arguments: List of arguments for the Chromium browser.
    :return: Configured ChromiumOptions instance.
    """
    options = ChromiumOptions().auto_port()
    options.set_paths(browser_path=browser_path)
    for argument in arguments:
        options.set_argument(argument)

    # options.no_imgs(True)
    # options.mute(True)
    # options.headless(True)
    return options


def get_cf_bypass(browser: str = "", force: bool = False, proxy: str | None = None, mute: bool = False):
    """Try get cf credentials"""

    browser_path = browser
    sdx_cache_path = get_cache_path()

    # Arguments to make the browser better for automation and less detectable.
    arguments = [
        "-no-first-run",
        "-force-color-profile=srgb",
        "-metrics-recording-only",
        "-password-store=basic",
        "-use-mock-keychain",
        "-export-tagged-pdf",
        "-no-default-browser-check",
        "-disable-background-mode",
        "-enable-features=NetworkService,NetworkServiceInProcess,LoadCryptoTokenExtension,PermuteTLSExtensions",
        "-disable-features=FlashDeprecationWarning,EnablePasswordsAccountStorage",
        "-deny-permission-prompts",
        "-disable-gpu",
        "-accept-lang=en-US"
    ]

    options = get_chromium_options(browser_path, arguments)

    # Try to get cached cookies first
    cookie_cache = CookieCache(cache_file=f'{sdx_cache_path}')
    cookie_cache.clear_expired()
    local_address = get_public_ip(proxy)
    hostname = urlparse(SUBDIVX_PAGE).netloc
    cache_key = md5_hash(hostname + local_address if local_address else hostname)
    cached = cookie_cache.get(cache_key)

    if not cached or cached.is_expired() or force:
        logger.debug(f"No cached cookies, expired or force bypasser for {cache_key}, generating new ones...")

        # Initialize the browser
        console.print(
            f':robot: [italic yellow]{gl("Getting_connection")}[/]',
            emoji=True, new_line_start=True
        )
        time.sleep(3)
        driver = ChromiumPage(addr_or_opts=options)
        Settings.set_language('en')
        try:
            logger.debug(f'Navigating to the {SUBDIVX_PAGE} page.')
            driver.get(SUBDIVX_PAGE)

            # Where the bypass starts
            logger.debug('Starting Cloudflare bypass.')
            cf_bypasser = CloudflareBypasser(driver, max_retries=8)

            # If you are solving an in-page captcha (like the one here: https://seleniumbase.io/apps/turnstile), use cf_bypasser.click_verification_button() directly instead of cf_bypasser.bypass().
            # It will automatically locate the button and click it. Do your own check if needed.

            cf_bypasser.bypass()
            if not cf_bypasser.is_bypassed():
                driver.quit()
                console.print(":no_entry: Bypass failed!", emoji=True, new_line_start=True)
                sys.exit(1)
            else:
                console.print(":heavy_check_mark:  Bypass successful!", emoji=True, new_line_start=True)
                time.sleep(2)
                clean_screen()

            cookies = driver.cookies(all_domains=True, all_info=True).as_dict()
            page = driver.html
            _vdata = BeautifulSoup(page, 'lxml')
            _f_search = str(_vdata('div', id="vs")[0].text).replace("v", "").replace(".", "")
            cookie = "; ".join(f"{key}={value}" for key, value in cookies.items() if key in ["sdx", "cf_clearance"])
            user_agent = driver.user_agent
            data_conn = {
                "user_agent": user_agent,
                "cookie": cookie,
                "search": _f_search
            }
            sdx_dc_path = get_cache_path(file_name='sdx_data_connection.json')
            data_cache: dict[str, Any] = {
                "user_agent": driver.user_agent,
                "cookies": cookies
            }

            logger.debug("Saving credentials...")
            try:
                cookie_cache.set(cache_key, data_cache["cookies"], data_cache["user_agent"], ttl_hours=24)
                with open(sdx_dc_path, 'w') as file:
                    json.dump(data_conn, file, indent=2)
                    file.close()
            except Exception as e:
                logger.error(f"Failed to save credential file: {e}")

            logger.debug("Saved cookies successfully")

            # Sleep for a while to let the user see the result if needed
            time.sleep(3)
        except Exception as e:
            logger.error("An error occurred: %s", str(e))
        finally:
            logger.debug('Closing the browser.')
            driver.quit()
    else:
        if not mute:
            console.print(
                f':white_check_mark: {gl("Still_cached_cookies")}\n'
                f'[bold yellow]{gl("Expires_at")}[/]{cached.expires_at.strftime("%H:%M:%S %d/%m/%Y")}',
                emoji=True
            )


def manual_bypasser():
    from rich.prompt import Prompt

    try:
        cf_clearance = Prompt.ask(
            f'[bold yellow]{gl("cf_clearance_cookie")}[/]',
            show_default=False,
            default=""
        )
        if cf_clearance:
            assert re.match(r'[a-zA-Z0-9\.\-\_]+$', cf_clearance), gl("Invalid_cf_clearance")
        else:
            raise AssertionError(gl("Invalid_cf_clearance"))

        sdx_cookie = Prompt.ask(
            f'[bold yellow]{gl("sdx_cookie")}[/]',
            show_default=False,
            default=""
        )
        if sdx_cookie:
            assert re.match(r'^[a-zA-Z0-9]+$', sdx_cookie), gl("Invalid_sdx")
        else:
            raise AssertionError(gl("Invalid_sdx"))

        user_agent = Prompt.ask(
            f'[bold yellow]{gl("User_agent")}[/]',
            show_default=False,
            default=""
        )
        if user_agent:
            browser_patterns = [
                r'Mozilla/\d+\.\d+',
                r'AppleWebKit/\d+\.\d+',
                r'Chrome/\d+',
                r'Safari/\d+',
                r'Firefox/\d+',
                r'Edge/\d+'
            ]
            valid_user_agent = any(re.search(pattern, user_agent) for pattern in browser_patterns)
            assert valid_user_agent, gl("Invalid_user_agent")
        else:
            raise AssertionError(gl("Invalid_user_agent"))

        try:
            sdx_cache_path = get_cache_path()
            cookie_cache = CookieCache(cache_file=f'{sdx_cache_path}')
            cookie_cache.clear_expired()
            local_address = get_public_ip()
            hostname = urlparse(SUBDIVX_PAGE).netloc
            cache_key = md5_hash(hostname + local_address if local_address else hostname)
            cookies = {"cf_clearance": cf_clearance, "sdx": sdx_cookie}
            data_cache: dict[str, Any] = {
                "user_agent": user_agent,
                "cookies": cookies
            }

            cookie_cache.set(cache_key, data_cache["cookies"], data_cache["user_agent"], ttl_hours=24)
            console.print(f'[bold green]{gl("Done")}[/]', new_line_start=True)
        except Exception as e:
            console.print(
                f':no_entry: [bold red]{gl("Failed_to_save_cache")}[/]\n'
                f'Error: {e}',
                emoji=True, new_line_start=False
            )
            sys.exit(1)
    except AssertionError as e:
        console.print(f':no_entry: [bold red]{e}[/]')
        sys.exit(1)
