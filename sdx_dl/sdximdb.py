# Copyright (C) 2025 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright 2025 BSD 3-Clause License (see https://opensource.org/license/bsd-3-clause)

# type: ignore
####  IMDB imports ###
import json
import random
import urllib3
import requests
from urllib3.exceptions import InsecureRequestWarning
from .sdxclasses import GenerateUserAgent

urllib3.disable_warnings(InsecureRequestWarning)

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

__all__ = ["IMDB"]

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
        ua = GenerateUserAgent.random_browser()
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

cleaner = Cleaner(javascript=True, style=True)
# cleaner.javascript = True
# cleaner.style = True

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

    def __init__(self, *, element, default_encoding: _DefaultEncoding = "", html: _HTML = "", url: _URL) -> None:
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
        return str(self.pq.text())

    @property
    def full_text(self) -> _Text:
        """The full text content (including links) of the
        :class:`Element <Element>` or :class:`HTML <HTML>`.
        """
        return self.lxml.text_content()

    def find(self, selector: str = "*", *, containing: _Containing = "", clean: bool = False, first: bool = False, _encoding: str = "") -> _Find:
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

    def xpath(self, selector: str, *, clean: bool = False, first: bool = False, _encoding: str = "") -> _XPath:
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

        return str(url)

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

    def __init__(self, *, element, url: _URL, default_encoding: _DefaultEncoding = "") -> None:
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

    def __init__(self, *, session: Union['HTMLSession', 'None'], url: str = DEFAULT_URL, html: _HTML, default_encoding: str = DEFAULT_ENCODING) -> None:

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

    def __init__(self, session: Union['HTMLSession','HTMLSession']) -> None:
        super(HTMLResponse, self).__init__()
        self._html = None   # type: HTML
        self.session = session

    @property
    def html(self) -> HTML:
        if not self._html:
            self._html = HTML(session=self.session, url=self.url, html=self.content, default_encoding=self.encoding) 

        return self._html

    @classmethod
    def _from_response(cls, response, session: Union['HTMLSession', 'HTMLSession']):
        html_r = cls(session=session)
        html_r.__dict__.update(response.__dict__)
        return html_r

def user_agent(style=None) -> _UserAgent:
    """Returns an apparently legit user-agent, if not requested one of a specific
    style. Defaults to a Chrome-style User-Agent.
    """
    global useragent
    ua = GenerateUserAgent
    browsers = {
        'chrome'  : random.choice(ua.chrome()),
        'firefox' : random.choice(ua.firefox()),
        'opera'   : random.choice(ua.opera())
    }

    if (not useragent) and style:
        useragent = browsers.get(style)
    else:
        useragent = ua.random_browser()

    return useragent if useragent else DEFAULT_USER_AGENT

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