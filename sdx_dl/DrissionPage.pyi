from typing import Any
from pathlib import Path

class ChromiumElement:
    @property
    def attrs(self) -> dict[str, Any]:
        ...

    def parent(self) -> 'ChromiumElement':
        ...

    def shadow_root(self) -> 'ChromiumElement' | None:
        ...

    def child(self) -> 'ChromiumElement':
        ...

    def children(self) -> list['ChromiumElement']:
        ...

    def ele(self, selector: str) -> 'ChromiumElement' | None:
        ...

    def eles(self, selector: str) -> list['ChromiumElement']:
        ...

    def __call__(self, selector: str) -> 'ChromiumElement' | None:
        ...

    def click(self) -> None:
        ...

    @property
    def tag(self) -> str:
        ...

class ChromiumOptions:
    def auto_port(self) -> 'ChromiumOptions':
        ...

    def set_paths(self, browser_path: str | Path | None = None, local_port: int | str | None = None,
        address: str | None = None, download_path: str | Path | None = None, user_data_path: str | Path | None = None,
        cache_path: str | Path | None = None) -> 'ChromiumOptions':
        """A quick path setting function, soon to be deprecated.

        :param browser_path: Browser executable file path
        :param local_port: Local port number
        :param address: Debug browser address, e.g., 127.0.0.1:9222
        :param download_path: Download file path
        :param user_data_path: User data path
        :param cache_path: Cache path
        :return: Current object
        """
        ...

    def set_argument(self, argument: str, value: Any = None) -> None:
        ...

    def no_imgs(self, on_off: bool = True) -> 'ChromiumOptions':
        """Set whether to load images.
 
        :param on_off: on or off 
        :return: current object 
        """
        ...

    def mute(self, on_off: bool = True) -> 'ChromiumOptions':
        """Set whether to mute.

        :param on_off: on or off 
        :return: current object 
        """
        ...
    def headless(self, on_off: bool = True) -> 'ChromiumOptions':
        """Set whether to hide the browser interface.
 
        :param on_off: on or off 
        :return: current object 
        """
        ...

class ChromiumPage:
    def __init__(self, addr_or_opts: 'ChromiumOptions') -> None:
        ...

    def get(self, url: str) -> None:
        ...

    def cookies(self, all_domains: bool = False, all_info: bool = False) -> 'CookiesList':
        ...

    @property
    def html(self) -> str:
        ...

    @property
    def user_agent(self) -> str:
        ...

    def quit(self) -> None:
        ...

    def eles(self, selector: str) -> list['ChromiumElement']:
        ...

    def ele(self, selector: str) -> 'ChromiumElement' | None:
        ...

    @property
    def title(self) -> str:
        ...

class CookiesList(list[Any]):
    def as_dict(self) -> dict[str, Any]:
        """Returns in dictionary format, containing only the name and value fields."""
        ...

    def as_str(self) -> str:
        """Returns in str format, containing only the name and value fields."""
        ...

    def as_json(self) -> str:
        """Return in JSON format"""
        ...

    def __next__(self) -> dict[str, Any]: ...
