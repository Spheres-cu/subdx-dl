# Copyright (C) 2025 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import datetime
import sys
from typing import Any

import certifi
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError, RequestException
from urllib3.util import Retry

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

__all__ = ['SubxAPI']


def ExceptionErrorMessage(e: Exception):
    """Parse ``Exception`` error message."""
    if isinstance(e, (HTTPError, RequestException)):
        if e.response:
            msg = e.response.json().get('detail')
            error = e.response.status_code
        else:
            msg = str(e).split(':', maxsplit=1)[1].split('(')[0].strip()
            error = gl(e.__class__.__name__)
        console.print(f":no_entry: {gl('Error_occurred')}HTTP error ({error}): {msg}")


class SubxAPI:
    """Base API for SubX"""
    def __init__(self, token: str, default_timeout: int = 15):
        """
        Initialize the API

        Args:
            token: The Bearer token for authentication
            default_timeout: Default timeout in seconds for requests
            base_url: The base URL of the API
        """
        self.base_url = 'https://subx-api.duckdns.org/api'
        self.token = token
        self.default_timeout = default_timeout
        self.session = requests.Session()
        retries = Retry(total=6, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': ua,
            'verify': certifi.where(),
        })
        # Setting proxy
        if proxies:
            self.session.proxies.update(proxies)

        # Data storage of query request
        self._data: dict[str, Any] | None = None
        self._health_ok = self.__check_health()

    def __check_health(self, timeout: int | None = None):
        timeout = timeout or self.default_timeout
        try:
            response = self.session.request(
                'GET', f'{self.base_url}/health',
                timeout=timeout)
            response.raise_for_status()
        except (HTTPError, RequestException) as e:
            logger.debug(f"{gl('SubX_API_Health')} Error: {e}")
            return False
        return bool(response.json().get('status') == 'ok')

    def __call_api(
        self,
        params: dict[str, Any] | None = None,
        endpoint: str = '',
        method: str = 'GET',
        timeout: int | None = None,
    ):
        url = f"{self.base_url}/{endpoint.rstrip('/')}"
        timeout = timeout or self.default_timeout

        try:
            response = self.session.request(
                method,
                url,
                params=params,
                timeout=timeout)
            response.raise_for_status()
            return response
        except HTTPError as e:
            ExceptionErrorMessage(e)
            logger.debug(f'HTTP error occurred: {e}')
            return None
        except RequestException as err:
            ExceptionErrorMessage(err)
            logger.debug(f'Request error occurred: {err}')
            return None
        except OSError as err:
            console.print(
                f":no_entry: {gl('Unexpected_error')}: {err!s}",
                emoji=True, new_line_start=True)
            return None

    def search(
        self,
        search: str,
        param: str = 'query',
        year: int | None = None,
        video_type: str | None = None,
        limit: int = 100,
        timeout: int | None = None,
    ) -> dict[str, Any] | None:
        """
        Make a search with the API

        Args:
            search(str): search string
            param(str): Query parameters (default: `query`, can be: `title`, `imdb_id`, `public_id`)
            year(int): Release year (1900-2100)
            video_type(str): movie or episode
            limit(int): Search results limit (1-200, default:100)
            timeout(int): Request timeout in seconds

        Returns:
            Parsed JSON response if content is JSON, or None if request fails
        """

        timeout = timeout or self.default_timeout
        endpoint = 'subtitles/search/'
        params: dict[str, Any] = {param: search, 'limit': limit}
        if year:
            params.update({'year': year})
        if video_type:
            params.update({'video_type': video_type})

        if self._health_ok:
            response = self.__call_api(params, endpoint, timeout=timeout)
            self._data = response.json() if response else None
            return self._data
        else:
            console.print(
                f":no_entry: {gl('SubX_API_Health')}",
                emoji=True, new_line_start=True)
            sys.exit(1)

    def get(
        self,
        subid: str = '',
        timeout: int | None = None,
    ) -> requests.Response | Any | None:
        """
        Get a subtitle with the API

        Args:
            subid(str): subtitle id
            timeout(int): Request timeout in seconds

        Returns:
            Response data with subtitle file, or None if request fails
        """

        endpoint = f'subtitles/{subid}/download'
        timeout = timeout or self.default_timeout
        self.session.headers.update({
            'Accept': '*/*',
            'Content-Type': 'application/x-www-form-urlencoded',
            'content-disposition': 'attachment',
        })
        if self._health_ok:
            return self.__call_api(endpoint=endpoint, timeout=timeout)
        else:
            console.print(
                f":no_entry: {gl('SubX_API_Health')}",
                emoji=True, new_line_start=True)
            sys.exit(1)

    def from_subx_aadata(self) -> dict[str, Any]:
        """convert subx data to aadata format"""
        data: dict[str, Any] = {}
        list_data: list[dict[str, Any]] = []

        if self._data and bool(self._data):
            total = int(self._data.get('total', 0))
            items: list[dict[str, Any]] = self._data.get('items') or []
            for item in items:
                dt_object = datetime.datetime.strptime(
                    f"{item.get('posted_at')}", '%Y-%m-%dT%H:%M:%SZ').astimezone(datetime.UTC)
                posted_at = dt_object.strftime('%Y-%m-%d %H:%M:%S')
                data = {
                    'id': item.get('id'),
                    'titulo': item.get('title'),
                    'descripcion': item.get('description'),
                    'descargas': item.get('downloads'),
                    'nick': item.get('uploader_name'),
                    'fecha_subida': posted_at,
                    'comentarios': 0,
                }
                list_data.append(data)

            return {
                'iTotalRecords': total,
                'aaData': list_data,
            }
        else:
            return {}
