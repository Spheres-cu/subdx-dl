# Copyright (C) 2024 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from sdx_dl.sdxconsole import console

### Config Settings imports ###
import os
import json
import typing
from typing import Optional, List, Dict, Any
from pathlib import Path

### Metadata video extractor imports ###
from guessit import guessit, jsonutils # type: ignore

### Check version imports ###
import re
import argparse
import urllib3
import certifi
from bs4 import BeautifulSoup
from importlib.metadata import version
from urllib3.exceptions import HTTPError

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

####  HTML2BBCode imports ###
from bs4 import Tag
from pygments.lexers import guess_lexer

####  Generate user agents imports ###
import sys
import random

__all__ = [
    "HTML2BBCode",
    "NoResultsError",
    "GenerateUserAgent",
    "VideoMetadataExtractor",
    "validate_proxy",
    "ChkVersionAction",
    "ConfigManager",
    "ViewConfigAction",
    "SaveConfigAction",
    "SetConfigAction",
    "ResetConfigAction",
    "FindFiles"
]

####  HTML2BBCode class ###
class HTML2BBCode:
    """
    HTML to BBCode converter
    """
    @staticmethod
    def guess_language(code: str) -> str:
        """
        Guesses the programming language from a string. This is not accurate for short strings. 'pygments' is used to
        guess code here because many other language detectors cannot detect the language properly.
        """
        guessed = guess_lexer(code).name
        if guessed == "Text only":
            return ""
        return guessed.lower()

    @classmethod
    def _html_to_bbcode(cls, tag:Tag) -> str:
        result = f""
        if hasattr(tag, 'children'):
            for child in tag.children:
                if isinstance(child, str):
                    result += child
                elif isinstance(child, Tag):
                    result += cls._html_to_bbcode(child) 

        if tag.name == "span":
            if "class" in list(tag.attrs.keys()):
                tag_type = tag["class"][0]
                if tag_type == "bb-bold":  # bold
                    result = f"[bold green]{result}[/bold green]"
                elif tag_type == "bb-italic":  # italic
                    result = f"[italic bright_yellow]{result}[/italic bright_yellow]"
                elif tag_type == "bb-underline":  # underline
                    result = f"[u]{result}[/u]"
                elif tag_type == "bb-strikethrough":  # strikethrough
                    result = f"[s]{result}[/s]"
                elif tag_type == "bb-big":  # big
                    result = f"[big]{result}[/big]"
                elif tag_type == "bb-small":  # small
                    result = f"[small]{result}[/small]"
            elif "style" in list(tag.attrs.keys()):
                if "color" in tag["style"]:  # color
                    tag_color = f'{tag.get("style")}'
                    result = f'[color={tag_color.replace("color:", "")}]{result}[/color]'
        elif tag.name == "br":  # line break
            result = "\n"
        elif tag.name == "a":  # url
            result = f"[link={tag['href']}]{result}[/link]"
        elif tag.name == "b":  # bold
            result = f"[bold green]{result}[/bold green]"
        elif tag.name == "i":  # bold
            result = f"[italic bright_yellow]{result}[/italic bright_yellow]" # italic
        elif tag.name == "ul":  # unordered list
            result = f"[list]\n{result}[/list]"
        elif tag.name == "li":  # list item
            result = f"[*] {result}"
        elif tag.name == "ol":  # ordered list
            result = f"[list=1]\n{result}[/list]"
        elif tag.name == "blockquote":  # quote
            quote_author = tag.find("p", {"class": "bb-quote-author"})
            if quote_author is not None:
                quote_author_name = str(quote_author.get_text()).replace(" wrote:", "")
                quote_author = "=" + quote_author_name
            else:
                quote_author = ""
            result = f"[quote{quote_author}]{result}[/quote]"
        elif tag.name == "p":
            if "class" in list(tag.attrs.keys()):
                if "bb-quote-author" in tag["class"]:
                    result = ""
            else:
                result = f"[p]{result}[/p]"  # p
        elif tag.name == "div":
            if "class" in list(tag.attrs.keys()):
                if "code" in tag["class"]:  # code
                    language = cls.guess_language(tag.get_text())
                    if not language:
                        language = ""
                    else:
                        language = "=" + language
                    result = f"[code{language}]{result}[/code]"
                # This converter cannot convert scratchblocks html to scratchblocks bbcode
                elif "scratchblocks" in tag["class"]:  # scratchblocks
                    result = f"[scratchblocks]{tag.get_text()}[/scratchblocks]"
            elif "style" in list(tag.attrs.keys()):
                if "text-align:center;" in tag["style"]:  # center
                    result = f"[center]{result}[/center]"
        return result

    @classmethod
    def html_to_bbcode(cls, html: str) -> str:
        try:
            soup = BeautifulSoup(html, "lxml")  # lxml is the fastest
            return cls._html_to_bbcode(soup)
        except Exception:
            pass
            return html

####  Utils Classes ###
class NoResultsError(Exception):
    pass

### Generate a user agent class ###
class GenerateUserAgent:
    """
    Class containing methods for generating user agents.
    """

    @staticmethod
    def _token() -> str:
        return "Mozilla/5.0"
    
    @staticmethod
    def _platform() -> str:
        _WINDOWS_PREFIX: str = "Windows NT 10.0; Win64; x64"
        _MAC_PREFIX: str = "Macintosh; Intel Mac OS X"
        _LINUX_PREFIX: str = "X11; Ubuntu; Linux x86_64"

        if sys.platform == "win32":
            # Windows
            platform = _WINDOWS_PREFIX
        elif sys.platform == "darwin":
            # macOS
            platform = _MAC_PREFIX
        else:
            # Linux and other UNIX-like systems
            platform = _LINUX_PREFIX
        return f'{platform}'

    @classmethod
    def firefox(cls) -> list[str]:
        """Generate a list of common firefox user agents

        Returns:
            list[str]: The list of common firefox user agents
        """
        return [f"{cls._token()} ({cls._platform()}; rv:{version}.0) Gecko/20100101 Firefox/{version}.0" for version in range(120, 138)]

    @classmethod
    def chrome(cls) -> list[str]:
        """Generate a list of common chrome user agents

        Returns:
            list[str]: The list of common chrome user agents
        """
        return [f"{cls._token()} ({cls._platform()}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36" for version in range(120, 135)]

    @classmethod
    def opera(cls) -> list[str]:
        """Generate a list of common opera user agents

        Returns:
            list[str]: The list of common opera user agents
        """
        return [f"{cls._token()} ({cls._platform()}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36 OPR/{opr}.0.0.0"
            for version in range(120, 135, 5) for opr in range(103, 118, 5)]

    @classmethod
    def safari(cls) -> list[str]:
        """Generate a list of common safari user agents

        Returns:
            list[str]: The list of common safari user agents
        """
        if sys.platform == "darwin":
            return [f"{cls._token()} ({cls._platform()} 14_7_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{major}.{minor} Safari/605.1.15" for major, minors in [(16, range(5, 7)), (17, range(0, 7))] for minor in minors]
        else:
            return []

    @classmethod
    def safari_mobile(cls) -> list[str]:
        """Generate a list of common mobile safari user agents

        Returns:
            list[str]: The list of common safari mobile user agents
        """
        if sys.platform == "darwin":
            return [f"{cls._token()} (iPhone; CPU iPhone OS {major}_{minor} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{major}.{minor} Mobile/15E148 Safari/604.1" for major, minors in [(16, range(5, 8)), (17, range(0, 7))] for minor in minors]
        else:
            return []

    @staticmethod
    def generate_all() -> list[str]:
        """Convenience method, Generate common user agents for all supported browsers

        Returns:
            list[str]: The list of common user agents for all supported browsers in GenerateUserAgent.
        """
        if sys.platform == "darwin":
            return GenerateUserAgent.safari() + GenerateUserAgent.safari_mobile() + GenerateUserAgent.opera()
        else:
            return GenerateUserAgent.firefox() + GenerateUserAgent.chrome() + GenerateUserAgent.opera()
        
    @staticmethod
    def generate_random() -> list[str]:
        """Convenience method, Generate random user agents for all supported browsers

        Returns:
            list[str]: The list of random user agents for all supported browsers in GenerateUserAgent.
        """
        if sys.platform == "darwin":
            return random.choice([GenerateUserAgent.safari() + GenerateUserAgent.safari_mobile() + GenerateUserAgent.opera()])
        else:
            return random.choice([GenerateUserAgent.firefox(), GenerateUserAgent.chrome(), GenerateUserAgent.opera()])
        
    @staticmethod
    def random_browser() -> str:
        """Convenience method, Generate a random user agents for one supported browser

        Returns:
            str: With the random user agents for one supported browser in GenerateUserAgent.
        """
        if sys.platform == "darwin":
            browser = random.choice([GenerateUserAgent.safari() + GenerateUserAgent.safari_mobile() + GenerateUserAgent.opera()])
            return random.choice(browser)
        else:
            browser = random.choice([GenerateUserAgent.firefox(), GenerateUserAgent.chrome(), GenerateUserAgent.opera()])
            return random.choice(browser)


### validate proxy settings ###

def validate_proxy(proxy_str:str) -> bool:
    """
    Validation with IP address or domain and port.
    """

    ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    host_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9]$'
    
    match = re.match(r'^(?:(https|http)://)?(?:([^:@]+):([^:@]+)@)?([^:@/]+)(?::(\d+))?$', proxy_str)
    
    if not match:
        return False
        
    protocol, _, _, host, port = match.groups() 
    
    if not (re.match(ip_pattern, host) or re.match(host_pattern, host)):
        return False
        
    if (port is None) or (not (0 < int(port) <= 65535)):
        return False
    
    if protocol not in ["http", "https", None]:
        return False
    
    return True

### Check version ###
def ExceptionErrorMessage(e: Exception):
    """Parse ``Exception`` error message."""
    if isinstance(e, (HTTPError)):
        msg = e.__str__().split(":", maxsplit=1)[1].split("(")[0]
    else:
        msg = e.__str__()
    error_class = e.__class__.__name__
    console.print("Error occurred: " + error_class + ":" + msg)
    sys.exit(1)

def _check_version(version:str, proxy:str):
    """Check for new version."""
    ua = GenerateUserAgent.random_browser()
    headers={"user-agent" : ua}
    msg = f''
    
    if (proxy):
        if not (any(p in proxy for p in ["http", "https"])):
            proxy = "http://" + proxy
        session = urllib3.ProxyManager(proxy, headers=headers, cert_reqs="CERT_REQUIRED", ca_certs=certifi.where(), retries=2, timeout=10)
    else:
        session = urllib3.PoolManager(headers=headers, cert_reqs="CERT_REQUIRED", ca_certs=certifi.where(), retries=2, timeout=10)
  
    def get_version_description(version:str):
        """Get new `version` description."""
        url = f"https://github.com/Spheres-cu/subdx-dl/releases/tag/{version}"
        
        response = session.request('GET', url).data.decode()

        description = f""
        soup = BeautifulSoup(response, 'lxml')
        try:
            data = soup.find('div', attrs={'data-test-selector': 'body-content'})
            data_items:list[str] = [li.text.strip() for li in data.find_all('li')] # type: ignore
        except AttributeError:
            return description

        for result in data_items:
            text = f"\u25cf {result}"
            description = description + text + "\n"
        
        return description

    try:
        _page_version = f"https://raw.githubusercontent.com/Spheres-cu/subdx-dl/refs/heads/main/sdx_dl/__init__.py"
        _dt_version = session.request('GET', _page_version).data.decode()
        _g_version = _dt_version.split('"')[1]

        if _g_version > version:

            msg = "\nNew version available! -> " + _g_version + ":\n\n"\
                   + get_version_description(_g_version) + "\n"\
                  "Please update your current version: " + version +"\r\n"        
        else:
            msg = "\nNo new version available\n"\
                  "Current version: " + version + "\r\n"

    except (HTTPError, Exception) as e:
        ExceptionErrorMessage(e)

    return msg

### Get Remaining arguments
def _get_remain_arg(args: List[str] | str) -> str:
    """ Get remainig arguments values"""
    n = 0; arg = ""
    for i in sys.argv:
        if i in args:
            arg = sys.argv[n + 1] if n + 1 < len(sys.argv) else arg
            break
        n = n + 1
    return arg

### Check version action class
class ChkVersionAction(argparse.Action):
    """Class Check version. This class call for `check_version` function"""
    @typing.no_type_check
    def __init__(self, nargs=0, **kw,):
        super().__init__(nargs=nargs, **kw) 
    
    @typing.no_type_check
    def __call__(self, parser, namespace, values, option_string=None):       
        p = getattr(namespace, "proxy") or _get_remain_arg(["-x", "--proxy"])
        if not p:
            config = ConfigManager()
            proxy = config.get("proxy")
        else:
            proxy = p if validate_proxy(p) else None
        
        print(_check_version(version("subdx-dl"), proxy))
        sys.exit(0)

### Class VideoExtractor ###
class VideoMetadataExtractor:
    """
    A class to extract metadata from video filenames using guessit.
    """
    @typing.no_type_check
    @staticmethod
    def extract_all(filename: str, options:str|Dict[str, Any]={}) -> Dict[str, Any]:
        """
        Extract all available metadata from a video filename.
        
        Args:
            filename (str): The video filename to parse
        
        :param options:
        :type options: str|dict
                   
        Returns:
            dict: Dictionary containing all extracted properties
        """
        all_metadata = guessit(filename, options) 
        result_dict:Dict[str, Any] = {}
        for key, value in all_metadata.items(): 
            if isinstance(value, jsonutils.Match):
                result_dict[key] = {
                    'value': value.value, 
                    'raw': value.raw 
                }
            else:
                result_dict[key] = value
        return result_dict
    
    @staticmethod
    def extract_specific(filename: str, *properties: str, options:str|Dict[str, Any]={}) -> Dict[str, Any]:
        """
        Extract specific properties from a video filename.
        
        Args:
            filename (str): The video filename to parse
            *properties (str): Properties to extract (e.g., 'title', 'year')
    
        :param options:
        :type options: str|dict
            
        Returns:
            dict: Dictionary containing only the requested properties
        """
        all_metadata:Dict[str, Any] = {}
        all_metadata = guessit(filename, options)  # type: ignore
        result_dict: Dict[str, Any] = {}
        for key, value in all_metadata.items(): # type: ignore
            if isinstance(value, jsonutils.Match):
                result_dict[key] = {
                    'value': value.value,  # type: ignore
                    'raw': value.raw # type: ignore
                }
            else:
                result_dict[key] = value
        
        return {prop: result_dict.get(prop) for prop in properties}
    
    @staticmethod
    def pretty_print(metadata: Dict[str, Any]) -> None:
        """
        Pretty print the metadata dictionary.
        
        Args:
            metadata (dict): Metadata dictionary to print
        """
        
        console.print_json(data=metadata, indent=4, default=str)

### Class Config Settings
class ConfigManager:
    """
    A class to manage application configuration settings in a JSON file.
    
    Attributes:
        config_path (str): Path to the configuration file
        config (dict): Dictionary containing the configuration settings
    """
    
    def __init__(self, config_path: str = ""):
        """
        Initialize the ConfigManager with a path to the configuration file.
        
        Args:
            config_path (str): Path to the configuration file. Defaults to None.
        """
        self.config_path = config_path if config_path else self.get_path()
        self.config = {}
        
        # Load existing config if it exists
        self._load_config()
        
    @property
    def exists(self) -> bool:
        """ Check if exists a config file"""
        return os.path.isfile(self.config_path)
    
    @property
    def hasconfig(self) -> bool:
        """ Check if config is empty"""
        return bool(self.config)
    
    def _load_config(self) -> None:
        """Load the configuration from file or create a new one if it doesn't exist."""
        try:
            if self.exists:
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {}
        except (json.JSONDecodeError, IOError) as e:
            pass
            console.print(":no_entry:[bold red] Failed to load configuration: [/]" + f'{e.__class__.__name__}\n',
                    emoji=True, new_line_start=True)
            self._save_config()
            sys.exit(1)

    def _save_config(self) -> None:
        """Save the current configuration to file."""
        if not self.exists:
            config_dir = Path(os.path.dirname(self.config_path))
            config_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
        except IOError as e:
            pass
            console.print(":no_entry:[bold red] Failed to save configuration: [/]" + f'{e.__class__.__name__}\n',
                    emoji=True, new_line_start=True)
            sys.exit(1)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key (str): The configuration key to retrieve
            default (Any): Default value to return if key doesn't exist
            
        Returns:
            The configuration value or default if key doesn't exist
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key (str): The configuration key to set
            value (Any): The value to set
        """
        self.config[key] = value
        self._save_config()

    def update(self, new_config: Dict[str, Any]) -> None:
        """
        Update multiple configuration values at once.
        
        Args:
            new_config (dict): Dictionary of key-value pairs to update
        """
        self.config.update(new_config)
        self._save_config()

    def delete(self, key: str) -> None:
        """
        Delete a configuration key.
        
        Args:
            key (str): The configuration key to delete
        """
        if key in self.config:
            del self.config[key]
            self._save_config()

    def reset(self) -> None:
        """Reset the configuration to an empty state."""
        self.config = {}
        self._save_config()

    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration settings.
        
        Returns:
            dict: A copy of the current configuration
        """
        return self.config.copy()

    def save_all(self, config:Dict[str, Any]) -> None:
        """
        Save all configuration values.
        
        Args:
            dict: With all configuration values.
        """

        self.reset()
        self.config = config.copy()
        self._save_config()
       
    def print_config(self) -> None:
        """
        Pretty print the config dictionary.
        """
        console.print_json(data=self.config, indent=4, default=str)

    def merge_config(self, args:Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge args values with config file
        
        Args:
            dict: With arguments to merge
        """
        merged: Dict[str, Any] = {}
        merged = {**args, **{k: v for k, v in self.config.items() if not args[k]}}

        return merged

    @staticmethod
    def get_path(app_name: str = "subdx-dl", file_name: Optional[str] = "sdx-config.json") -> Path:
        """
        Get the appropriate local configuration path for the current platform.
        
        Args:
            app_name: Name of your application (used to create a subdirectory). Default subdx-dl
            file_name: Optional filename to append to the config path. Default sdx-config.json
            
        Returns:
            Path object pointing to the configuration directory or file
            
        Platform-specific paths:
        - Windows: %LOCALAPPDATA%\\<app_name>\\
        - macOS: ~/Library/Application Support/<app_name>/
        - Linux: ~/.config/<app_name>/
        """
        if sys.platform == "win32":
            # Windows
            base_dir = Path(f'{os.getenv("LOCALAPPDATA")}')
        elif sys.platform == "darwin":
            # macOS
            base_dir = Path.home() / "Library" / "Application Support"
        else:
            # Linux and other UNIX-like systems
            base_dir = Path.home() / ".config"
        
        config_dir = base_dir / app_name
        
        if file_name:
            return config_dir / file_name
        return config_dir

### Config action classes
class ViewConfigAction(argparse.Action):
    """Check config file class Action"""
    @typing.no_type_check
    def __init__(self, nargs=0, **kw,): 
        super().__init__(nargs=nargs, **kw) 
    
    @typing.no_type_check
    def __call__(self, parser, namespace, values, option_string=None): 
        config = ConfigManager()
        if config.exists:
            print("Config file:", f'{config.get_path()}')
            config.print_config() if config.hasconfig else print("Config is empty!")
        else:
            print("Not exists config file")
        sys.exit(0)

class SaveConfigAction(argparse.Action):
    """Save allowed arguments to a config file. Existing values are update."""
    @typing.no_type_check
    def __init__(self, nargs=0, **kw,): 
        super().__init__(nargs=nargs, **kw) 
   
    @typing.no_type_check
    def __call__(self, parser, namespace, values, option_string=None): 
        allowed_values = ["quiet", "verbose", "force", "no_choose", "no_filter", "nlines", "path", "proxy", "Season", "imdb"]
        copied_config = namespace.__dict__.copy()

        if all(not copied_config[k] for k in copied_config.keys()):
            console.print(":no_entry: Nothing to save...")
            sys.exit(0)
  
        for k in namespace.__dict__.keys():
            if k not in allowed_values: del copied_config[k]
        
        config = ConfigManager()

        config.update(config.merge_config(copied_config)) if config.hasconfig else config.save_all(copied_config)
        if not copied_config['quiet']: console.print(":heavy_check_mark:  Config was saved!")
        
        if not getattr(namespace, "search"):
            sys.exit(0)

class SetConfigAction(argparse.Action):
    """Save an option to config file"""
    @typing.no_type_check
    def __init__(self, nargs='?', **kw):
        super().__init__(nargs=nargs, **kw) 
    
    @typing.no_type_check
    def __call__(self, parser, namespace, values, option_string = None): 

        if not values:
            console.print(":no_entry: Not a valid option: ", self.choices)
            sys.exit(1)
        
        key, value = f'', None
        config = ConfigManager()

        if values in ["quiet", "verbose", "force", "no_choose", "no_filter", "Season", "imdb"]:
            key, value = f'{values}', bool(True)
        elif values == "path":
            path = _get_remain_arg("path")
            if os.path.isdir(path) and os.access(path, os.W_OK):
                key, value = f'{values}', path
            else:
                console.print(":no_entry:[bold red] Directory:[yellow] " + path + "[bold red] do not exists or don't have access[/]")
        elif values == "proxy":
            proxy = _get_remain_arg("proxy")
            if validate_proxy(proxy):
                key, value = f'{values}', proxy
            else:
                console.print(":no_entry:[bold red] Incorrect proxy setting:[yellow] " + proxy + "[/]")
        elif values == "nlines":
            lines = _get_remain_arg("nlines") 
            key, value = f'{values}', int(lines) if lines.isnumeric() and int(lines) in range(5,25,5) else 10
        
        if not value:
            sys.exit(1)

        if config.hasconfig:
            config.set(key, value)
        else:
            config.update({key: value})
        
        console.print("\u2713 Done!")
        sys.exit(0)

class ResetConfigAction(argparse.Action):
    """Reset an option in the config file"""
    @typing.no_type_check
    def __init__(self, nargs='?', **kw): 
        super().__init__(nargs=nargs, **kw) 
    
    @typing.no_type_check
    def __call__(self, parser, namespace, values, option_string = None):

        if not values:
            console.print(":no_entry: Not a valid option: ", self.choices)
            sys.exit(1)
        
        key, value = f'', None
        config = ConfigManager()

        if values in ["quiet", "verbose", "force", "no_choose", "no_filter", "Season", "imdb"]:
            key, value = f'{values}', bool(False)
        elif values in ["path", "proxy", "nlines"]:
            key, value = f'{values}', None
        
        if config.hasconfig:
            config.set(key, value)
        else:
            config.update({key: value})
        
        console.print("\u2713 Done!")
        sys.exit(0)

### Findfiles class ###
extension_pattern = '(\\.[a-zA-Z0-9]+)$'
string_type = str

class InvalidPath(Exception):
    """Raised when an argument is a non-existent file or directory path
    """
    pass

class FindFiles(object):
    """Given a file, it will verify it exists. Given a folder it will descend
    one level into it and return a list of files, unless the recursive argument
    is True, in which case it finds all files contained within the path.

    The with_extension argument is a list of valid extensions, without leading
    spaces. If an empty list (or None) is supplied, no extension checking is
    performed.

    The filename_blacklist argument is a list of regexp strings to match against
    the filename (minus the extension). If a match is found, the file is skipped
    (e.g. for filtering out "sample" files). If [] or None is supplied, no
    filtering is done
    """

    def __init__(self, path:str, with_extension: Optional[List[str]] = None, filename_blacklist: Optional[List[Any]] = None, recursive:bool = False):
        self.path = path
        if with_extension is None:
            self.with_extension = []
        else:
            self.with_extension = with_extension
        if filename_blacklist is None:
            self.with_blacklist = []
        else:
            self.with_blacklist = filename_blacklist
        self.recursive = recursive
    
    @staticmethod
    def split_extension(filename:str) -> str:
        """Split extension from `filename` based in extension pattern"""
        base = re.sub(extension_pattern, "", filename)
        ext = filename.replace(base, "")
        return ext

    def findFiles(self) -> List[str]:
        """Returns list of files found at path
        """
        listfiles:List[str] = []
        if os.path.isfile(self.path):
            path = os.path.abspath(self.path)
            if self._checkExtension(path) and not self._blacklistedFilename(path):
                listfiles.append(path)
                return listfiles
            else:
                return listfiles
        elif os.path.isdir(self.path):
            return self._findFilesInPath(self.path)
        else:
            raise InvalidPath("%s is not a valid file/directory" % self.path)

    def _checkExtension(self, fname:str) -> bool:
        """Checks if the file extension is blacklisted in valid_extensions
        """
        if len(self.with_extension) == 0:
            return True

        # don't use split_extension here (otherwise valid_extensions is useless)!
        _, extension = os.path.splitext(fname)
        for cext in self.with_extension:
            cext = ".%s" % cext
            if extension == cext:
                return True
        else:
            return False

    def _blacklistedFilename(self, filepath:str) -> bool:
        """Checks if the filename (optionally excluding extension)
        matches filename_blacklist

        self.with_blacklist should be a list of strings and/or dicts:

        a string, specifying an exact filename to ignore
        "filename_blacklist": [".DS_Store", "Thumbs.db"],

        a dictionary, where each dict contains:

        Key 'match' - (if the filename matches the pattern, the filename
        is blacklisted)

        Key 'is_regex' - if True, the pattern is treated as a
        regex. If False, simple substring check is used (if
        cur['match'] in filename). Default is False

        Key 'full_path' - if True, full path is checked. If False, only
        filename is checked. Default is False.

        Key 'exclude_extension' - if True, the extension is removed
        from the file before checking. Default is False.
        """

        if len(self.with_blacklist) == 0:
            return False

        fullname = f'{os.path.split(filepath)[1]}'
        fname = self.split_extension(fullname)

        for fblacklist in self.with_blacklist:
            if isinstance(fblacklist, string_type):
                if fullname == fblacklist:
                    return True
                else:
                    continue

            if "full_path" in fblacklist and fblacklist["full_path"]:
                to_check = filepath
            else:
                if fblacklist.get("exclude_extension", False):
                    to_check = fname
                else:
                    to_check = fullname

            if fblacklist.get("is_regex", False):
                m = re.match(fblacklist["match"], to_check)
                if m is not None:
                    return True
            else:
                m = fblacklist["match"] in to_check
                if m:
                    return True
        else:
            return False

    def _findFilesInPath(self, startpath: str) -> List[str]:
        """Finds files from startpath, could be called recursively
        """
        allfiles:List[str] = []
        if not os.access(startpath, os.R_OK):
            return allfiles

        for subf in os.listdir(string_type(startpath)):
            newpath = os.path.join(startpath, subf)
            newpath = os.path.abspath(newpath)
            if os.path.isfile(newpath):
                if not self._checkExtension(subf):
                    continue
                elif self._blacklistedFilename(subf):
                    continue
                else:
                    allfiles.append(newpath)
            else:
                if self.recursive:
                    allfiles.extend(self._findFilesInPath(newpath))
        return allfiles