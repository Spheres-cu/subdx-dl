# Copyright (C) 2024 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright 2024 BSD 3-Clause License (see https://opensource.org/license/bsd-3-clause)

####  HTML2BBCode class ###

from collections import defaultdict
from configparser import RawConfigParser
from html.parser import HTMLParser
from os.path import join, dirname


class Attributes(dict):
    def __getitem__(self, name):
        try:
            return super(Attributes, self).__getitem__(name)
        except KeyError:
            return ""


class TagParser(RawConfigParser):
    def get_pretty(self, section, option):
        value = self.get(section, option)
        return value.replace("\\n", "\n")


class HTML2BBCode(HTMLParser):
    """
    HTML to BBCode converter

    >>> parser = HTML2BBCode()
    >>> str(parser.feed('<ul><li>one</li><li>two</li></ul>'))
    '[list][li]one[/li][li]two[/li][/list]'

    >>> str(parser.feed('<a href="https://google.com/">Google</a>'))
    '[url=https://google.com/]Google[/url]'

    >>> str(parser.feed('<img src="https://www.google.com/images/logo.png">'))
    '[img]https://www.google.com/images/logo.png[/img]'

    >>> str(parser.feed('<em>EM test</em>'))
    '[i]EM test[/i]'

    >>> str(parser.feed('<strong>Strong text</strong>'))
    '[b]Strong text[/b]'

    >>> str(parser.feed('<code>a = 10;</code>'))
    '[code]a = 10;[/code]'

    >>> str(parser.feed('<blockquote>Beautiful is better than ugly.</blockquote>'))
    '[quote]Beautiful is better than ugly.[/quote]'

    >>> str(parser.feed('<font face="Arial">Text decorations</font>'))
    '[font=Arial]Text decorations[/font]'

    >>> str(parser.feed('<font size="2">Text decorations</font>'))
    '[size=2]Text decorations[/size]'

    >>> str(parser.feed('<font color="red">Text decorations</font>'))
    '[color=red]Text decorations[/color]'

    >>> str(parser.feed('<font face="Arial" color="green" size="2">Text decorations</font>'))
    '[color=green][font=Arial][size=2]Text decorations[/size][/font][/color]'

    >>> str(parser.feed('Text<br>break'))
    'Text\\nbreak'

    >>> str(parser.feed('&nbsp;'))
    '&nbsp;'
    """

    def __init__(self, config=None):
        HTMLParser.__init__(self, convert_charrefs=False)
        self.attrs = None
        self.data = None
        self.config = TagParser(allow_no_value=True)
        self.config.read(join(dirname(__file__), "data/defaults.conf"))
        if config:
            self.config.read(config)

    def handle_starttag(self, tag, attrs):
        if self.config.has_section(tag):
            self.attrs[tag].append(dict(attrs))
            self.data.append(
                self.config.get_pretty(tag, "start") % Attributes(attrs or {})
            )
            if self.config.has_option(tag, "expand"):
                self.expand_starttags(tag)

    def handle_endtag(self, tag):
        if self.config.has_section(tag):
            self.data.append(self.config.get_pretty(tag, "end"))
            if self.config.has_option(tag, "expand"):
                self.expand_endtags(tag)
            self.attrs[tag].pop()

    def handle_data(self, data):
        self.data.append(data)

    def feed(self, data):
        self.data = []
        self.attrs = defaultdict(list)
        HTMLParser.feed(self, data)
        return "".join(self.data)

    def expand_starttags(self, tag):
        for expand in self.get_expands(tag):
            if expand in self.attrs[tag][-1]:
                self.data.append(
                    self.config.get_pretty(expand, "start") % self.attrs[tag][-1]
                )

    def expand_endtags(self, tag):
        for expand in reversed(self.get_expands(tag)):
            if expand in self.attrs[tag][-1]:
                self.data.append(
                    self.config.get_pretty(expand, "end") % self.attrs[tag][-1]
                )

    def get_expands(self, tag):
        expands = self.config.get_pretty(tag, "expand").split(",")
        return list(map(lambda x: x.strip(), expands))

    def handle_entityref(self, name):
        self.data.append(f"&{name};")

    def handle_charref(self, name):
        self.data.append(f"&#{name};")

####  HTML2BBCode class ###

####  Utils Classes ###
class NoResultsError(Exception):
    pass

"""Generate a user agent"""

_TOKEN: str = "Mozilla/5.0"
_WINDOWS_PREFIX: str = "Windows NT 10.0; Win64; x64"
_MAC_PREFIX: str = "Macintosh; Intel Mac OS X"
_LINUX_PREFIX: str = "X11; Ubuntu; Linux x86_64"


class GenerateUserAgent:
    """Class containing methods for generating user agents."""

    @staticmethod
    def firefox() -> list[str]:
        """Generate a list of common firefox user agents

        Returns:
            list[str]: The list of common firefox user agents
        """
        return [f"{_TOKEN} ({platform}; rv:{version}.0) Gecko/20100101 Firefox/{version}.0" for platform in (f"{_MAC_PREFIX} 10.15", _WINDOWS_PREFIX, _LINUX_PREFIX) for version in range(119, 132)]

    @staticmethod
    def chrome() -> list[str]:
        """Generate a list of common chrome user agents

        Returns:
            list[str]: The list of common chrome user agents
        """
        return [f"{_TOKEN} ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36" for platform in (f"{_MAC_PREFIX} 10_15_7", _WINDOWS_PREFIX, "X11; Linux x86_64") for version in range(119, 128)]

    @staticmethod
    def safari() -> list[str]:
        """Generate a list of common safari user agents

        Returns:
            list[str]: The list of common safari user agents
        """
        return [f"{_TOKEN} ({_MAC_PREFIX} 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{major}.{minor} Safari/605.1.15" for major, minors in [(16, range(5, 7)), (17, range(0, 7))] for minor in minors]

    @staticmethod
    def safari_mobile() -> list[str]:
        """Generate a list of common mobile safari user agents

        Returns:
            list[str]: The list of common safari mobile user agents
        """
        return [f"{_TOKEN} (iPhone; CPU iPhone OS {major}_{minor} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{major}.{minor} Mobile/15E148 Safari/604.1" for major, minors in [(16, range(5, 8)), (17, range(0, 7))] for minor in minors]

    @staticmethod
    def generate_all() -> list[str]:
        """Convenience method, Generate common user agents for all supported browsers

        Returns:
            list[str]: The list of common user agents for all supported browsers in GenerateUserAgent.
        """
        return GenerateUserAgent.firefox() + GenerateUserAgent.chrome() + GenerateUserAgent.safari() + GenerateUserAgent.safari_mobile()