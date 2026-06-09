# Copyright (C) 2026 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import datetime
import re
import urllib.parse
from typing import Any

import certifi
import requests
from requests.exceptions import HTTPError, RequestException

from sdx_dl.sdxclasses import GenerateUserAgent
from sdx_dl.sdxconsole import console
from sdx_dl.sdxlocale import gl
from sdx_dl.sdxparser import args, logger

ua = GenerateUserAgent.random_browser()

if args.proxy:
    proxie = f'{args.proxy}'
    if not (any(p in proxie for p in ['http', 'https'])):
        proxie = f'http://{proxie}'
    proxies = {'http': proxie, 'https': proxie}
else:
    proxies = None

__all__ = ['TMDBAPI']


def ExceptionErrorMessage(e: Exception):
    """Parse ``Exception`` error message."""
    if isinstance(e, (HTTPError, RequestException)):
        if e.response is not None:
            msg = e.response.json().get('status_message')
            error = e.response.status_code
        else:
            msg = e
            error = gl(e.__class__.__name__)
        console.print(f":no_entry: {gl('Error_occurred')}HTTP error ({error}): {msg}")


class TMDBAPI:
    """Base API for TMDB"""
    def __init__(self, api_key: str, default_timeout: int = 15):
        """
        Args:
            api_key: The api key for authentication
            default_timeout: Default timeout in seconds for requests
            base_url: The base URL of the API
        """
        self.base_url = 'https://api.themoviedb.org/3'
        self.api_key = api_key
        self.default_timeout = default_timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': ua})
        # Setting proxy
        if proxies:
            self.session.proxies.update(proxies)
        # Data storage of requests search
        self.__data = Any

    def __call_api(
        self,
        params: Any,
        endpoint: str,
        method: str = 'GET',
        timeout: int | None = None,
    ):
        url = f"{self.base_url}/{endpoint.rstrip('/')}"
        timeout = timeout or self.default_timeout
        response: requests.Response
        try:
            response = self.session.request(
                method,
                url,
                params=params,
                timeout=timeout,
                verify=certifi.where())
            response.raise_for_status()
            return response.json()
        except HTTPError as e:
            ExceptionErrorMessage(e)
            logger.debug(f'HTTP error occurred: {e}')
            return None
        except RequestException as err:
            ExceptionErrorMessage(err)
            logger.debug(f'Request error occurred: {err}')
            return None
        except Exception as err:
            console.print(
                f":no_entry: {gl('Unexpected_error')}: {err.__str__()}",
                emoji=True, new_line_start=True)
            return None

    def search(
        self,
        title: str,
        year: int | None = None,
        tv: bool = True,
    ):
        """Return a `tmdb` search by `title` (and `year`) for `tv/movies`"""
        endpoint = 'search/tv' if tv else 'search/movie'
        params = urllib.parse.urlencode({
            'api_key': self.api_key,
            'query': title,
            'include_adult': 'false',
            'page': '1',
            'year': year or ''})
        re_full_match = re.compile(rf'^{re.escape(title)}$', re.I)
        self.__data = self.__call_api(params, endpoint)

        if self.__data:
            try:
                results: list[dict[str, Any]] = []
                data: dict[str, Any] = {}
                items: list[dict[str, Any]] = self.__data.get('results')
                for i in items:
                    name = i.get('original_name') if tv else i.get('original_title')
                    if tv:
                        year_date = datetime.datetime.strptime(i.get('first_air_date', ''), '%Y-%m-%d').year
                    else:
                        year_date = datetime.datetime.strptime(i.get('release_date', ''), '%Y-%m-%d').year or year
                    if (
                        name is not None
                        and re_full_match.search(f'{name}')
                        and (year is None or year == year_date)
                    ):
                        data = {
                            'original_name': name,
                            'year': year_date,
                            'id': self._get_imdb(int(i.get('id', 0)), tv)}
                        results.append(data)
                        return results
                    elif name is not None:
                        data = {
                            'original_name': name,
                            'year': year_date,
                            'id': self._get_imdb(int(i.get('id', 0)), tv)}
                        results.append(data)
                return results or None
            except Exception as e:
                logger.debug(f'TMDB search error: {e}')
                return None
        else:
            return None

    def _get_imdb(
        self,
        tmdbid: int,
        tv: bool = True,
    ):
        """Return the `imdb_id` of the `tmdb_id`"""
        endpoint = f'tv/{tmdbid}' if tv else f'movie/{tmdbid}'
        params = urllib.parse.urlencode({
            'api_key': self.api_key,
            'append_to_response': 'external_ids'})
        response = self.__call_api(params, endpoint)
        if response:
            try:
                data: dict[str, Any] = response.get('external_ids')
                if data and data.get('imdb_id'):
                    return f"{data.get('imdb_id')}"
                else:
                    return None
            except Exception as e:
                logger.debug(f'TMDB get imdb error: {e}')
                return None
        else:
            return None

    def find_by_id(
        self,
        imdbid: str,
    ):
        """Find the `original_title` by the `imdb_id`"""
        endpoint = f'find/{imdbid}'
        params = urllib.parse.urlencode({
            'api_key': self.api_key,
            'external_source': 'imdb_id'})
        response = self.__call_api(params, endpoint)
        if response:
            try:
                data: dict[str, Any] = response.get('movie_results')[0]
                if data and data.get('original_title'):
                    return f"{data.get('original_title')}"
                else:
                    return None
            except Exception as e:
                logger.debug(f'TMDB find by id error: {e}')
                return None
        else:
            return None
