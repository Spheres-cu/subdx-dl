# Copyright (C) 2024 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright 2024 BSD 3-Clause License (see https://opensource.org/license/bsd-3-clause)

### Metadata video extractor imports ###
from guessit import guessit
from typing import Dict, Any

### Check version imports ###
import re
import argparse
import urllib3
from importlib.metadata import version
from urllib3.exceptions import HTTPError

####  HTML2BBCode imports ###
from collections import defaultdict
from configparser import RawConfigParser
from html.parser import HTMLParser
from os.path import join, dirname

####  IMDB imports ###
import json
import random
import requests
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

### html_requests imports ###
import sys
import asyncio
from urllib.parse import urlparse, urlunparse, urljoin
from typing import Set, Union, List, MutableMapping
from pyquery import PyQuery
from lxml.html.clean import Cleaner
import lxml
from lxml import etree
from lxml.html import HtmlElement
from lxml.html import tostring as lxml_html_tostring
from lxml.html.soupparser import fromstring as soup_parse
from parse import search as parse_search
from parse import findall, Result
from w3lib.encoding import html_to_unicode

####  HTML2BBCode class ###

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

### Generate a user agent class ###

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
    # for manipulate incoming data/json from IMDB (for invalid json string)


### IMDB search classes ###
class ImdbParser:
    """
      - A class to manipulate incoming json string data of a movie/TV from IMDB.
      - Changes are required as sometimes the json contains invalid chars in description/reviewBody/trailer schema
    """
    def __init__(self, json_string):
        self.json_string = json_string

    @property
    def remove_trailer(self):
        """
         @description:- Helps to remove 'trailer' schema from IMDB data json string.
         @returns:- New updated JSON string.
        """
        try:
            self.json_string = ''.join(self.json_string.splitlines())
            trailer_i = self.json_string.index('"trailer"')
            actor_i = self.json_string.index('"actor"')
            to_remove = self.json_string[trailer_i:actor_i:1]
            self.json_string = self.json_string.replace(to_remove, "")
        except ValueError:
            self.json_string = self.json_string
        return self.json_string

    @property
    def remove_description(self):
        """
         @description:- Helps to remove 'description' schema from IMDB file json string.
         @returns:- New updated JSON string.
        """
        try:
            review_i = self.json_string.index('"review"')
            des_i = self.json_string.index('"description"', 0, review_i)
            to_remove = self.json_string[des_i:review_i:1]
            self.json_string = self.json_string.replace(to_remove, "")
        except ValueError:
            self.json_string = self.json_string
        return self.json_string

    @property
    def remove_review_body(self):
        """
         @description:- Helps to remove 'reviewBody' schema from IMDB file json string.
         @returns:- New updated JSON string.
        """
        try:
            reviewrating_i = self.json_string.index('"reviewRating"')
            reviewbody_i = self.json_string.index('"reviewBody"', 0, reviewrating_i)
            to_remove = self.json_string[reviewbody_i:reviewrating_i:1]
            self.json_string = self.json_string.replace(to_remove, "")
        except ValueError:
            self.json_string = self.json_string
        return self.json_string

class IMDB:
    """
        A class to represent IMDB API.

        --------------

        Main Methods of the IMDB API
        --------------
            #1. search(name, year=None, tv=False)
                -- to search a query on IMDB

            #2. get_by_name(name, year=None, tv=False)
                -- to get a Movie/TV-Series info by it's name (pass year also to increase accuracy)
    """
    def __init__(self):
        self.session = HTMLSession()
        lst_ua = GenerateUserAgent.chrome() + GenerateUserAgent.firefox()
        ua = random.choice(lst_ua)
        self.headers = {
           "Accept": "application/json, text/plain, */*",
           "Accept-Language": "es-ES,es,q=0.6",
           "User-Agent": ua,
           "Referer": "https://www.imdb.com/"
           }
        self.baseURL = "https://www.imdb.com"
        self.search_results = {'result_count': 0, 'results': []}
        self.NA = json.dumps({"status": 404, "message": "No Result Found!", 'result_count': 0, 'results': []})

    # ..................................method to search on IMDB...........................................
    def search(self, name, year=None, tv=False):
        """
         @description:- Helps to search a query on IMDB.
         @parameter-1:- <str:name>, query value to search.
         @parameter-2:- <int:year> OPTIONAL, release year of query/movie/tv/file to search.
         @parameter-3:- <bool:tv> OPTIONAL, to filter/limit/bound search results only for 'TV Series'.
         @returns:- A JSON string:
                    - {'result_count': <int:total_search_results>, 'results': <list:list_of_files/movie_info_dict>}
        """
        assert isinstance(name, str)
        self.search_results = {'result_count': 0, 'results': []}

        name = name.replace(" ", "+")

        if year is None:
            url = f"https://www.imdb.com/find?q={name}"
        else:
            assert isinstance(year, int)
            url = f"https://www.imdb.com/find?q={name}+{year}"

        try:
            response = self.session.get(url)
        except requests.exceptions.ConnectionError as e:
            response = self.session.get(url, verify=False)

        results = response.html.xpath("//section[@data-testid='find-results-section-title']/div/ul/li")
        if tv is True:
            results = [result for result in results if "TV" in result.text]
        else:
            results = [result for result in results if "TV" not in result.text]
        
        output = []
        for result in results:
            name = result.text.replace('\n', ' ')
            year_date = "N/A"
            show = ""
            url = result.find('a')[0].attrs['href']
            if not (any(s in name for s in ['Podcast', 'Music Video', 'Video', 'Episode', 'Short'])):
                try:
                    for i in range(len(result.find('span'))):
                        span = result.find('span')[i]
                        if 'TV' in span.text:
                            show = span.text
                        else:
                            text = span.text.strip().split('-')[0][:4]
                            if text.isnumeric():
                                year_date = text
                          
                    show = "Movie" if show == "" else show
            
                    file_id = url.split('/')[2]
                    name = result.find('a')[0].text
                    output.append({
                        "type": show,
                        "id": file_id,
                        "year": year_date,
                        "name": name,
                        "url": f"https://www.imdb.com{url}"
                       })
                except IndexError:
                    pass
                self.search_results = {'result_count': len(output), 'results': output}
        return json.dumps(self.search_results, indent=2)

    # ..............................methods to get a movie/web-series/tv info..............................
    def get(self, url):
        """
         @description:- helps to get a file's complete info (used by get_by_name() & get_by_id() )
         @parameter:- <str:url>, url of the file/movie/tv-series.
         @returns:- File/movie/TV info as JSON string.
        """
        try:
            response = self.session.get(url)
            result = response.html.xpath("//script[@type='application/ld+json']")[0].text
            result = ''.join(result.splitlines())  # removing newlines
            result = f"""{result}"""

        except IndexError:
            return self.NA
        try:
            # converting json string into dict
            result = json.loads(result)
        except json.decoder.JSONDecodeError as e:
            # sometimes json is invalid as 'description' contains inverted commas or other html escape chars
            try:
                to_parse = ImdbParser(result)
                # removing trailer & description schema from json string
                parsed = to_parse.remove_trailer
                # parsed = to_parse.remove_description

                result = json.loads(parsed)
            except json.decoder.JSONDecodeError as e:
                try:
                    # removing reviewBody from json string
                    parsed = to_parse.remove_review_body
                    result = json.loads(parsed)
                except json.decoder.JSONDecodeError as e:
                    # invalid char(s) is/are not in description/trailer/reviewBody schema
                    return self.NA
        
        output = {
            "type": result.get('@type'),
            "id":result.get('url').split(self.baseURL + "/title")[-1].strip("/"),
            "name": result.get('name'),
            "year": str(result.get("datePublished"))[:-6],
            "url": result.get('url'),
            "description": result.get('description')
        }
        return json.dumps(output, indent=2)

    def get_by_name(self, name, year=None, tv=False):
        """
         @description:- Helps to search a file/movie/tv by name.
         @parameter-1:- <str:name>, query/name to search.
         @parameter-2:- <int:year> OPTIONAL, release year of query/movie/tv/file to search.
         @parameter-3:- <bool:tv> OPTIONAL, to filter/limit/bound search result only for 'TV Series'.
         @returns:- File/movie/TV info as JSON string.
        """
        results = json.loads(self.search(name, year=year, tv=tv))
        all_results = [i for i in self.search_results['results'] if 'title' in i['url']]

        # filtering TV and movies
        if tv is True:  # for tv/Web-Series only
            tv_only = [result for result in all_results if "TV" in result['type']]
            if year is not None:
                tv_only = [result for result in tv_only if str(year) in result['name']]
            # double checking by file name
            if bool(tv_only):
                tv_only_checked = [result for result in tv_only if result['name'].lower().startswith(name.split(" ")[0].lower())]
                tv_only = tv_only_checked if bool(tv_only_checked) else tv_only
            results['results'] = tv_only if bool(tv_only) else all_results

        else:  # for movies only
            movie_only = [result for result in all_results if "TV" not in result['name']]
            if year is not None:
                movie_only = [result for result in movie_only if str(year) in result['name']]
            # double checking by file name
            if bool(movie_only):
                movie_only_checked = [result for result in movie_only if result['name'].lower().startswith(name.split(" ")[0].lower())]
                movie_only = movie_only_checked if bool(movie_only_checked) else movie_only
            results['results'] = movie_only if bool(movie_only) else all_results

        if len(results['results']) > 0:
            return self.get(results['results'][0].get('url'))
        else:
            return self.NA

    def get_by_id(self, file_id):
        """
         @description:- Helps to search a file/movie/tv by its imdb ID.
         @parameter-1:- <str:file_id>, imdb ID of the file/movie/tv.
         @returns:- File/movie/TV info as JSON string.
        """
        assert isinstance(file_id, str)
        url = f"{self.baseURL}/title/{file_id}"
        return self.get(url)
    
### html_requests classes ###
DEFAULT_ENCODING = 'utf-8'
DEFAULT_URL = 'https://example.org/'
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8'
DEFAULT_NEXT_SYMBOL = ['next', 'more', 'older']

cleaner = Cleaner()
cleaner.javascript = True
cleaner.style = True

useragent = None

# Typing.
_Find = Union[List['Element'], 'Element']
_XPath = Union[List[str], List['Element'], str, 'Element']
_Result = Union[List['Result'], 'Result']
_HTML = Union[str, bytes]
_BaseHTML = str
_UserAgent = str
_DefaultEncoding = str
_URL = str
_RawHTML = bytes
_Encoding = str
_Text = str
_Containing = Union[str, List[str]]
_Links = Set[str]
_Attrs = MutableMapping
_Next = Union['HTML', List[str]]
_NextSymbol = List[str]

# Sanity checking.
try:
    assert sys.version_info.major == 3
    assert sys.version_info.minor > 5
except AssertionError:
    raise RuntimeError('Requests-HTML requires Python 3.6+!')


class MaxRetries(Exception):

    def __init__(self, message):
        self.message = message


class BaseParser:
    """A basic HTML/Element Parser, for Humans.

    :param element: The element from which to base the parsing upon.
    :param default_encoding: Which encoding to default to.
    :param html: HTML from which to base the parsing upon (optional).
    :param url: The URL from which the HTML originated, used for ``absolute_links``.

    """

    def __init__(self, *, element, default_encoding: _DefaultEncoding = None, html: _HTML = None, url: _URL) -> None:
        self.element = element
        self.url = url
        self.skip_anchors = True
        self.default_encoding = default_encoding
        self._encoding = None
        self._html = html.encode(DEFAULT_ENCODING) if isinstance(html, str) else html
        self._lxml = None
        self._pq = None

    @property
    def raw_html(self) -> _RawHTML:
        """Bytes representation of the HTML content.
        (`learn more <http://www.diveintopython3.net/strings.html>`_).
        """
        if self._html:
            return self._html
        else:
            return etree.tostring(self.element, encoding='unicode').strip().encode(self.encoding)

    @property
    def html(self) -> _BaseHTML:
        """Unicode representation of the HTML content
        (`learn more <http://www.diveintopython3.net/strings.html>`_).
        """
        if self._html:
            return self.raw_html.decode(self.encoding, errors='replace')
        else:
            return etree.tostring(self.element, encoding='unicode').strip()

    @html.setter
    def html(self, html: str) -> None:
        self._html = html.encode(self.encoding)

    @raw_html.setter
    def raw_html(self, html: bytes) -> None:
        """Property setter for self.html."""
        self._html = html

    @property
    def encoding(self) -> _Encoding:
        """The encoding string to be used, extracted from the HTML and
        :class:`HTMLResponse <HTMLResponse>` headers.
        """
        if self._encoding:
            return self._encoding

        # Scan meta tags for charset.
        if self._html:
            self._encoding = html_to_unicode(self.default_encoding, self._html)[0]
            # Fall back to requests' detected encoding if decode fails.
            try:
                self.raw_html.decode(self.encoding, errors='replace')
            except UnicodeDecodeError:
                self._encoding = self.default_encoding


        return self._encoding if self._encoding else self.default_encoding

    @encoding.setter
    def encoding(self, enc: str) -> None:
        """Property setter for self.encoding."""
        self._encoding = enc

    @property
    def pq(self) -> PyQuery:
        """`PyQuery <https://pythonhosted.org/pyquery/>`_ representation
        of the :class:`Element <Element>` or :class:`HTML <HTML>`.
        """
        if self._pq is None:
            self._pq = PyQuery(self.lxml)

        return self._pq

    @property
    def lxml(self) -> HtmlElement:
        """`lxml <http://lxml.de>`_ representation of the
        :class:`Element <Element>` or :class:`HTML <HTML>`.
        """
        if self._lxml is None:
            try:
                self._lxml = soup_parse(self.html, features='html.parser')
            except ValueError:
                self._lxml = lxml.html.fromstring(self.raw_html)

        return self._lxml

    @property
    def text(self) -> _Text:
        """The text content of the
        :class:`Element <Element>` or :class:`HTML <HTML>`.
        """
        return self.pq.text()

    @property
    def full_text(self) -> _Text:
        """The full text content (including links) of the
        :class:`Element <Element>` or :class:`HTML <HTML>`.
        """
        return self.lxml.text_content()

    def find(self, selector: str = "*", *, containing: _Containing = None, clean: bool = False, first: bool = False, _encoding: str = None) -> _Find:
        """Given a CSS Selector, returns a list of
        :class:`Element <Element>` objects or a single one.

        :param selector: CSS Selector to use.
        :param clean: Whether or not to sanitize the found HTML of ``<script>`` and ``<style>`` tags.
        :param containing: If specified, only return elements that contain the provided text.
        :param first: Whether or not to return just the first result.
        :param _encoding: The encoding format.

        Example CSS Selectors:

        - ``a``
        - ``a.someClass``
        - ``a#someID``
        - ``a[target=_blank]``

        See W3School's `CSS Selectors Reference
        <https://www.w3schools.com/cssref/css_selectors.asp>`_
        for more details.

        If ``first`` is ``True``, only returns the first
        :class:`Element <Element>` found.
        """

        # Convert a single containing into a list.
        if isinstance(containing, str):
            containing = [containing]

        encoding = _encoding or self.encoding
        elements = [
            Element(element=found, url=self.url, default_encoding=encoding)
            for found in self.pq(selector)
        ]

        if containing:
            elements_copy = elements.copy()
            elements = []

            for element in elements_copy:
                if any([c.lower() in element.full_text.lower() for c in containing]):
                    elements.append(element)

            elements.reverse()

        # Sanitize the found HTML.
        if clean:
            elements_copy = elements.copy()
            elements = []

            for element in elements_copy:
                element.raw_html = lxml_html_tostring(cleaner.clean_html(element.lxml))
                elements.append(element)

        return _get_first_or_list(elements, first)

    def xpath(self, selector: str, *, clean: bool = False, first: bool = False, _encoding: str = None) -> _XPath:
        """Given an XPath selector, returns a list of
        :class:`Element <Element>` objects or a single one.

        :param selector: XPath Selector to use.
        :param clean: Whether or not to sanitize the found HTML of ``<script>`` and ``<style>`` tags.
        :param first: Whether or not to return just the first result.
        :param _encoding: The encoding format.

        If a sub-selector is specified (e.g. ``//a/@href``), a simple
        list of results is returned.

        See W3School's `XPath Examples
        <https://www.w3schools.com/xml/xpath_examples.asp>`_
        for more details.

        If ``first`` is ``True``, only returns the first
        :class:`Element <Element>` found.
        """
        selected = self.lxml.xpath(selector)

        elements = [
            Element(element=selection, url=self.url, default_encoding=_encoding or self.encoding)
            if not isinstance(selection, etree._ElementUnicodeResult) else str(selection)
            for selection in selected
        ]

        # Sanitize the found HTML.
        if clean:
            elements_copy = elements.copy()
            elements = []

            for element in elements_copy:
                element.raw_html = lxml_html_tostring(cleaner.clean_html(element.lxml))
                elements.append(element)

        return _get_first_or_list(elements, first)

    def search(self, template: str) -> Result:
        """Search the :class:`Element <Element>` for the given Parse template.

        :param template: The Parse template to use.
        """

        return parse_search(template, self.html)

    def search_all(self, template: str) -> _Result:
        """Search the :class:`Element <Element>` (multiple times) for the given parse
        template.

        :param template: The Parse template to use.
        """
        return [r for r in findall(template, self.html)]

    @property
    def links(self) -> _Links:
        """All found links on page, in as–is form."""

        def gen():
            for link in self.find('a'):

                try:
                    href = link.attrs['href'].strip()
                    if href and not (href.startswith('#') and self.skip_anchors) and not href.startswith(('javascript:', 'mailto:')):
                        yield href
                except KeyError:
                    pass

        return set(gen())

    def _make_absolute(self, link):
        """Makes a given link absolute."""

        # Parse the link with stdlib.
        parsed = urlparse(link)._asdict()

        # If link is relative, then join it with base_url.
        if not parsed['netloc']:
            return urljoin(self.base_url, link)

        # Link is absolute; if it lacks a scheme, add one from base_url.
        if not parsed['scheme']:
            parsed['scheme'] = urlparse(self.base_url).scheme

            # Reconstruct the URL to incorporate the new scheme.
            parsed = (v for v in parsed.values())
            return urlunparse(parsed)

        # Link is absolute and complete with scheme; nothing to be done here.
        return link


    @property
    def absolute_links(self) -> _Links:
        """All found links on page, in absolute form
        (`learn more <https://www.navegabem.com/absolute-or-relative-links.html>`_).
        """

        def gen():
            for link in self.links:
                yield self._make_absolute(link)

        return set(gen())

    @property
    def base_url(self) -> _URL:
        """The base URL for the page. Supports the ``<base>`` tag
        (`learn more <https://www.w3schools.com/tags/tag_base.asp>`_)."""

        # Support for <base> tag.
        base = self.find('base', first=True)
        if base:
            result = base.attrs.get('href', '').strip()
            if result:
                return result

        # Parse the url to separate out the path
        parsed = urlparse(self.url)._asdict()

        # Remove any part of the path after the last '/'
        parsed['path'] = '/'.join(parsed['path'].split('/')[:-1]) + '/'

        # Reconstruct the url with the modified path
        parsed = (v for v in parsed.values())
        url = urlunparse(parsed)

        return url


class Element(BaseParser):
    """An element of HTML.

    :param element: The element from which to base the parsing upon.
    :param url: The URL from which the HTML originated, used for ``absolute_links``.
    :param default_encoding: Which encoding to default to.
    """

    __slots__ = [
        'element', 'url', 'skip_anchors', 'default_encoding', '_encoding',
        '_html', '_lxml', '_pq', '_attrs', 'session'
    ]

    def __init__(self, *, element, url: _URL, default_encoding: _DefaultEncoding = None) -> None:
        super(Element, self).__init__(element=element, url=url, default_encoding=default_encoding)
        self.element = element
        self.tag = element.tag
        self.lineno = element.sourceline
        self._attrs = None

    def __repr__(self) -> str:
        attrs = ['{}={}'.format(attr, repr(self.attrs[attr])) for attr in self.attrs]
        return "<Element {} {}>".format(repr(self.element.tag), ' '.join(attrs))

    @property
    def attrs(self) -> _Attrs:
        """Returns a dictionary of the attributes of the :class:`Element <Element>`
        (`learn more <https://www.w3schools.com/tags/ref_attributes.asp>`_).
        """
        if self._attrs is None:
            self._attrs = {k: v for k, v in self.element.items()}

            # Split class and rel up, as there are ussually many of them:
            for attr in ['class', 'rel']:
                if attr in self._attrs:
                    self._attrs[attr] = tuple(self._attrs[attr].split())

        return self._attrs


class HTML(BaseParser):
    """An HTML document, ready for parsing.

    :param url: The URL from which the HTML originated, used for ``absolute_links``.
    :param html: HTML from which to base the parsing upon (optional).
    :param default_encoding: Which encoding to default to.
    """

    def __init__(self, *, session: Union['HTMLSession'] = None, url: str = DEFAULT_URL, html: _HTML, default_encoding: str = DEFAULT_ENCODING, async_: bool = False) -> None:

        # Convert incoming unicode HTML into bytes.
        if isinstance(html, str):
            html = html.encode(DEFAULT_ENCODING)

        super(HTML, self).__init__(
            # Convert unicode HTML to bytes.
            element=PyQuery(html)('html') or PyQuery(f'<html>{html}</html>')('html'),
            html=html,
            url=url,
            default_encoding=default_encoding
        )
        self.session = session or HTMLSession()
        self.page = None
        self.next_symbol = DEFAULT_NEXT_SYMBOL

    def __repr__(self) -> str:
        return f"<HTML url={self.url!r}>"

    def next(self, fetch: bool = False, next_symbol: _NextSymbol = DEFAULT_NEXT_SYMBOL) -> _Next:
        """Attempts to find the next page, if there is one. If ``fetch``
        is ``True`` (default), returns :class:`HTML <HTML>` object of
        next page. If ``fetch`` is ``False``, simply returns the next URL.

        """

        def get_next():
            candidates = self.find('a', containing=next_symbol)

            for candidate in candidates:
                if candidate.attrs.get('href'):
                    # Support 'next' rel (e.g. reddit).
                    if 'next' in candidate.attrs.get('rel', []):
                        return candidate.attrs['href']

                    # Support 'next' in classnames.
                    for _class in candidate.attrs.get('class', []):
                        if 'next' in _class:
                            return candidate.attrs['href']

                    if 'page' in candidate.attrs['href']:
                        return candidate.attrs['href']

            try:
                # Resort to the last candidate.
                return candidates[-1].attrs['href']
            except IndexError:
                return None

        __next = get_next()
        if __next:
            url = self._make_absolute(__next)
        else:
            return None

        if fetch:
            return self.session.get(url)
        else:
            return url

    def __iter__(self):

        next = self

        while True:
            yield next
            try:
                next = next.next(fetch=True, next_symbol=self.next_symbol).html
            except AttributeError:
                break

    def __next__(self):
        return self.next(fetch=True, next_symbol=self.next_symbol).html

    def __aiter__(self):
        return self

    def add_next_symbol(self, next_symbol):
        self.next_symbol.append(next_symbol)

class HTMLResponse(requests.Response):
    """An HTML-enabled :class:`requests.Response <requests.Response>` object.
    Effectively the same, but with an intelligent ``.html`` property added.
    """

    def __init__(self, session: Union['HTMLSession']) -> None:
        super(HTMLResponse, self).__init__()
        self._html = None  # type: HTML
        self.session = session

    @property
    def html(self) -> HTML:
        if not self._html:
            self._html = HTML(session=self.session, url=self.url, html=self.content, default_encoding=self.encoding)

        return self._html

    @classmethod
    def _from_response(cls, response, session: Union['HTMLSession']):
        html_r = cls(session=session)
        html_r.__dict__.update(response.__dict__)
        return html_r


def user_agent(style=None) -> _UserAgent:
    """Returns an apparently legit user-agent, if not requested one of a specific
    style. Defaults to a Chrome-style User-Agent.
    """
    global useragent

    if (not useragent) and style:
        # useragent = UserAgent()
        lst_ua = GenerateUserAgent.chrome()
        ua = random.choice(lst_ua)
        useragent = ua

    return useragent[style] if style else DEFAULT_USER_AGENT


def _get_first_or_list(l, first=False):
    if first:
        try:
            return l[0]
        except IndexError:
            return None
    else:
        return l


class BaseSession(requests.Session):
    """ A consumable session, for cookie persistence and connection pooling,
    amongst other things.
    """

    def __init__(self, mock_browser : bool = True, verify : bool = True,
                 browser_args : list = ['--no-sandbox']):
        super().__init__()

        # Mock a web browser's user agent.
        if mock_browser:
            self.headers['User-Agent'] = user_agent()

        self.hooks['response'].append(self.response_hook)
        self.verify = verify

        self.__browser_args = browser_args


    def response_hook(self, response, **kwargs) -> HTMLResponse:
        """ Change response enconding and replace it by a HTMLResponse. """
        if not response.encoding:
            response.encoding = DEFAULT_ENCODING
        return HTMLResponse._from_response(response, self)

class HTMLSession(BaseSession):

    def __init__(self, **kwargs):
        super(HTMLSession, self).__init__(**kwargs)

    @property
    def browser(self):
        if not hasattr(self, "_browser"):
            self.loop = asyncio.get_event_loop()
            if self.loop.is_running():
                raise RuntimeError("Cannot use HTMLSession within an existing event loop. Use AsyncHTMLSession instead.")
            self._browser = self.loop.run_until_complete(super().browser)
        return self._browser

    def close(self):
        """ If a browser was created close it first. """
        if hasattr(self, "_browser"):
            self.loop.run_until_complete(self._browser.close())
        super().close()

### validate proxy settings ###

def validate_proxy(proxy_str):
    """
    Validation with IP address and port or domain.
    """

    ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    host_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9]$'
    
    match = re.match(r'^(?:(https|http)://)?(?:([^:@]+):([^:@]+)@)?([^:@/]+)(?::(\d+))?$', proxy_str)
    
    if not match:
        return False
        
    protocol, user, password, host, port = match.groups()
    
    if not (re.match(ip_pattern, host) or re.match(host_pattern, host)):
        return False
        
    if port and not (0 < int(port) <= 65535):
        return False
    
    if protocol not in ["http", "https", None]:
        return False
    
    return True

### Check version ###
ua = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0"
headers={"user-agent" : ua}

def ExceptionErrorMessage(e: Exception):
    """Parse ``Exception`` error message."""
    if isinstance(e, (requests.exceptions.ConnectionError, urllib3.exceptions.HTTPError)):
        msg = e.__str__().split(":")[1].split("(")[0]
    else:
        msg = e.__str__()
    error_class = e.__class__.__name__
    print("Error occurred: " + error_class + ":" + msg)
    exit(1)

def get_version_description(version:str, proxies):
    """Get new `version` description."""

    verify = False if proxies is not None else True
    session = HTMLSession()
    session.headers={
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-EN,es,q=0.6",
    "User-Agent": ua,
    "Referer": "https://github.com/Spheres-cu/subdx-dl"
    }
    url = f"https://github.com/Spheres-cu/subdx-dl/releases/tag/{version}"
    
    try:
        response = session.get(url, proxies=proxies, verify=verify)
    except (HTTPError, Exception) as e:
        ExceptionErrorMessage(e)

    results = response.html.xpath("//div[@data-test-selector='body-content']/ul/li")
    description = f""
    try:
        for result in results:
            for i in range(len(result.find('li'))):
                item = result.find('li')[i]
                text = f"\u25cf {item.text}"
                description = description + text + "\n"

    except IndexError:
        pass
    return description

def check_version(version:str, proxy):
    """Check for new version."""
    if (proxy):
        if not (any(p in proxy for p in ["http", "https"])):
            proxy = "http://" + proxy
        
        proxies = {"http" : proxy, "https" : proxy} if validate_proxy(proxy) else None
    else:
        proxies = None

    verify = False if proxies is not None else True
    
    try:
        _page_version = f"https://raw.githubusercontent.com/Spheres-cu/subdx-dl/refs/heads/main/sdx_dl/__init__.py"
        _dt_version = requests.get(_page_version, headers=headers, proxies=proxies, verify=verify, timeout=10).content
        _g_version = f"{_dt_version}".split('"')[1]

        if _g_version > version:

            msg = "\nNew version available! -> " + _g_version + ":\n\n"\
                   + get_version_description(_g_version, proxies) + "\n"\
                  "Please update your current version: " + f"{version}\r\n"        
        else:
            msg = "\nNo new version available\n"\
                  "Current version: " + f"{version}\r\n"

    except (HTTPError, Exception) as e:
        ExceptionErrorMessage(e)

    return msg

class ChkVersionAction(argparse.Action):
    """Class Check version. This class call for `check_version` function"""
    def __init__(self, nargs=0, **kw,):
        super().__init__(nargs=nargs, **kw)
    
    def __call__(self, parser, namespace, values, option_string=None):
        proxy = getattr(namespace, "proxy")
        print(check_version(version("subdx-dl"), proxy))
        exit (0)

### Class VideoExtractor ###
class VideoMetadataExtractor:
    """
    A class to extract metadata from video filenames using guessit.
    """
    
    @staticmethod
    def extract_all(filename: str) -> Dict[str, Any]:
        """
        Extract all available metadata from a video filename.
        
        Args:
            filename (str): The video filename to parse
            
        Returns:
            dict: Dictionary containing all extracted properties
        """
        return guessit(filename)
    
    @staticmethod
    def extract_specific(filename: str, *properties: str) -> Dict[str, Any]:
        """
        Extract specific properties from a video filename.
        
        Args:
            filename (str): The video filename to parse
            *properties (str): Properties to extract (e.g., 'title', 'year')
            
        Returns:
            dict: Dictionary containing only the requested properties
        """
        all_metadata = guessit(filename)
        return {prop: all_metadata.get(prop) for prop in properties}
    
    @staticmethod
    def pretty_print(metadata: Dict[str, Any]) -> None:
        """
        Pretty print the metadata dictionary.
        
        Args:
            metadata (dict): Metadata dictionary to print
        """
        print(json.dumps(metadata, indent=4, default=str))