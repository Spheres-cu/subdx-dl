# Copyright (C) 2025 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import sys
import requests
from typing import Any
from requests.exceptions import HTTPError
from requests.exceptions import RequestException
from urllib.parse import urlencode
from datetime import datetime
from sdx_dl.sdxparser import logger, args
from sdx_dl.sdxconsole import console
from sdx_dl.sdxlocale import gl

ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"

if args.proxy:
    proxie = f"{args.proxy}"
    if not (any(p in proxie for p in ["http", "https"])):
        proxie = f"http://{proxie}"
    proxies = {'http': proxie, 'https': proxie}
else:
    proxies = None

__all__ = ['SubxAPI']


def ExceptionErrorMessage(e: Exception):
    """Parse ``Exception`` error message."""
    if isinstance(e, (HTTPError, RequestException)):
        msg = e.__str__().split(":", maxsplit=1)[1].split("(")[0].strip()
    else:
        msg = e
    error_class = e.__class__.__name__
    console.print(f':no_entry: {gl("Error_occurred")} {gl(error_class)} : {msg}')


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
        self.base_url = "https://subx-api.duckdns.org/api"
        self.token = token
        self.default_timeout = default_timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': ua
        })
        # Setting proxy
        if proxies:
            self.session.proxies.update(proxies)
        # Data storage of query request
        self._data: dict[str, Any] | None = None

    def query(
        self,
        query: str = "",
        method: str = "GET",
        endpoint: str = "subtitles/search/",
        params: dict[str, Any] | None = None,
        timeout: int | None = None
    ) -> dict[str, Any] | str | None:
        """
        Make a query request to the API

        Args:
            method: HTTP method (GET)
            endpoint: API endpoint (appended to base_url)
            params: Query parameters
            timeout: Request timeout in seconds

        Returns:
            Parsed JSON response if content is JSON, otherwise raw text,
            or None if request fails
        """
        url = f"{self.base_url}/{endpoint.rstrip('/')}"
        timeout = timeout or self.default_timeout

        response: requests.Response
        try:
            response = self.session.request(
                method,
                url,
                params=params or urlencode({"query": query}),
                timeout=timeout
            )
            response.raise_for_status()

            # Try to parse JSON, fallback to text
            try:
                self._data = response.json()
                return self._data
            except ValueError:
                return response.text

        except HTTPError as e:
            ExceptionErrorMessage(e)
            logger.debug(f"HTTP error occurred: {e} HTTP Error ({e.response.status_code})")
            sys.exit(1)
        except RequestException as err:
            ExceptionErrorMessage(err)
            logger.debug(f"Request error occurred: {err}")
            sys.exit(1)
        except Exception as err:
            console.print(
                f':no_entry: {gl("Unexpected_error")}: {err.__str__()}',
                emoji=True, new_line_start=True
            )
            sys.exit(1)

        return None

    def get(
        self,
        id: str = "",
        method: str = "GET",
        endpoint: str = "subtitles/",
        timeout: int | None = None
    ) -> requests.Response | Any | None:
        """
        Make an request to the API

        Args:
            method: HTTP method (GET)
            endpoint: API endpoint (appended to base_url)
            id: subtitle id parameter
            timeout: Request timeout in seconds

        Returns:
            Parsed JSON response if content is JSON, otherwise raw text,
            or None if request fails
        """
        url = f"{self.base_url}/{endpoint}/{id}/download"
        timeout = timeout or self.default_timeout
        self.session.headers.update({
            'Accept': '*/*',
            'Content-Type': 'application/x-www-form-urlencoded',
            'content-disposition': 'attachment'
        })

        response: requests.Response
        try:
            response = self.session.request(
                method,
                url,
                timeout=timeout
            )
            response.raise_for_status()

            # Try to get content response or None
            try:
                return response
            except Exception:
                return None

        except HTTPError as e:
            ExceptionErrorMessage(e)
            logger.debug(f"HTTP error occurred: {e} HTTP Error ({e.response.status_code})")
            sys.exit(1)
        except RequestException as err:
            ExceptionErrorMessage(err)
            logger.debug(f"Request error occurred: {err}")
            sys.exit(1)
        except Exception as err:
            console.print(
                f':no_entry: {gl("Unexpected_error")}: {err.__str__()}',
                emoji=True, new_line_start=True
            )
            logger.debug(f'{gl("Unexpected_error")}: {err}')
            sys.exit(1)

        return None

    def from_subx_aadata(self) -> dict[str, Any]:
        """convert subx data to aadata format"""
        data: dict[str, Any] = {}
        list_data: list[dict[str, Any]] = []

        if self._data and bool(self._data):
            total = int(self._data['total'])
            for item in self._data['items']:
                dt_object = datetime.strptime(item['posted_at'], "%Y-%m-%dT%H:%M:%SZ")
                posted_at = dt_object.strftime("%Y-%m-%d %H:%M:%S")
                data = {
                    "id": item['id'],
                    "titulo": item['title'],
                    "descripcion": item['description'],
                    "descargas": item['downloads'],
                    "nick": item['uploader_name'],
                    "fecha_subida": posted_at,
                    "comentarios": 0
                }
                list_data.append(data)

            return {
                "iTotalRecords": total,
                "aaData": list_data
            }
        else:
            return {}
