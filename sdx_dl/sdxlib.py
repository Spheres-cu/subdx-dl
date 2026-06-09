# Copyright (C) 2024 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import shutil
import sys
import tempfile
import time
from tempfile import NamedTemporaryFile
from typing import Any
from zipfile import ZipFile, is_zipfile

from rarfile import (  # type: ignore
    Error,  # type: ignore
    RarFile,
    is_rarfile,  # type: ignore
)
from requests import Response
from urllib3.response import HTTPResponse

from sdx_dl.sdxclasses import ConfigManager
from sdx_dl.sdxconsole import console
from sdx_dl.sdxlocale import gl
from sdx_dl.sdxparser import args, logger
from sdx_dl.sdxsubxapi import SubxAPI
from sdx_dl.sdxutils import (
    SUBDIVX_DOWNLOAD_PAGE,
    HTTPError,
    HTTPErrorsMessageException,
    Metadata,
    clean_screen,
    conn,
    convert_date,
    extract_subtitles,  # type: ignore
    get_aadata,
    get_filtered_results,
    get_imdb_search,
    get_selected_subtitle_id,
    headers,
    metadata,
    paginate,
    sort_results,
)

__all__ = ['get_subtitle', 'get_subtitle_id']


def get_subtitle_id(title: str, number: str, inf_sub: dict[str, Any], metadata: Metadata = metadata):

    """
    Get a list of subtitles of subtitles searched by ``title`` and season/episode
    ``number`` of series or movies.

    The results are ordered based on a weighing of a ``metadata`` list.

    If ``no_choose`` ``(-nc)`` is false then a list of subtitles is show for choose.

    Else the first founded subtitle `id` is choosen.

    Return the subtitle `id`
    """
    search = None
    tmdb_search = None
    json_aaData: dict[str, Any] = {}
    list_Subs_Dicts: list[dict[str, Any]] = []

    if args.imdb:
        if not args.quiet:
            console.print(
                f':earth_americas: [bold yellow]{gl("Searching_TMDB")} {title} {number}',
                new_line_start=True, emoji=True)
        logger.debug(f'Searching in TMDB: {title} {number}')
        tmdb_search = get_imdb_search(title, number, inf_sub)
        if tmdb_search:
            search = tmdb_search.imdb
        logger.debug(f'TMDB Search result: {search}')
        if not args.quiet and search:
            console.print(
                f':information_source:  [bold yellow]{gl("Search_terms_from_TMDB")}[/]{search}',
                new_line_start=True, emoji=True)
            time.sleep(0.5)

    if not search:
        search = f'{title} {number}'.strip()

    if not args.quiet:
        console.print('\r')
    logger.debug(f'Searching subtitles for: {title} {number.upper()}')

    if args.SubX:
        cf = ConfigManager()
        if cf.hasconfig and 'SubX_key' in cf.config:
            sbx = SubxAPI(cf.get('SubX_key', default=''))
            with console.status(f'{gl("Searching_subtitles_for")}{title} {number.upper()}') as status:
                status.start() if not args.quiet else status.stop()
                sbx.query(search)
            json_aaData = sbx.from_subx_aadata()
            if json_aaData.get('iTotalRecords') == 0 and tmdb_search:
                time.sleep(2)
                sbx.query(f'{tmdb_search.orig_name} {number}')
                json_aaData = sbx.from_subx_aadata()
                search = f'{tmdb_search.orig_name} {number}'
        else:
            console.print(
                f':no_entry: {gl("Not_SubX_key")}: [italic pale_turquoise4]{gl("Not_SubX_key_wiki")}[/]',
                emoji=True, new_line_start=False)
            sys.exit(1)
    else:
        json_aaData = get_aadata(search)
        if json_aaData.get('iTotalRecords') == 0 and tmdb_search:
            time.sleep(4)
            json_aaData = get_aadata(f'{tmdb_search.orig_name} {number}')
            search = f'{tmdb_search.orig_name} {number}'

    if json_aaData.get('iTotalRecords') == 0:
        if not args.quiet:
            console.print(f':no_entry: [bold red]{gl("Not_subtitles_records_found_for")}[/][yellow]{search}[/]')
        logger.debug(f'Not subtitles records found for: {search}')
        return None
    else:
        logger.debug(f'Found subtitles records for: {search}')

    # Get Json Data Items
    aaData_Items = json_aaData.get('aaData')

    if aaData_Items:
        list_Subs_Dicts = convert_date(aaData_Items)
    else:
        if not args.quiet:
            console.print(f':no_entry: [bold red]{gl("No_suitable_data_were_found_for")} [yellow]{search}[/]')
        logger.debug(f'No suitable data were found for: "{search}"')
        return None

    # only include results for this specific serie / episode
    # ie. search terms are in the title of the result item

    if args.no_filter or (args.imdb and inf_sub['type'] == 'movie'):
        filtered_list_Subs_Dicts = list_Subs_Dicts
    else:
        filtered_list_Subs_Dicts = get_filtered_results(title, number, inf_sub, list_Subs_Dicts)

    if not filtered_list_Subs_Dicts:
        if not args.quiet:
            console.print(f':no_entry: [bold red]{gl("No_suitable_data_were_found_for")} [yellow]{search}[/]')
        logger.debug(f'No suitable data were found for: "{search}"')
        return None

    if metadata.hasdata:
        results = sort_results(filtered_list_Subs_Dicts, metadata)
    else:
        results = sorted(filtered_list_Subs_Dicts, key=lambda item: (item['descargas']), reverse=True)

    # Print subtitles search infos
    # Construct Table for console output

    table_title = f'{title} {number.upper()}'
    results_pages = paginate(results, 10)

    if (not args.no_choose):
        return get_selected_subtitle_id(table_title, results, metadata)
    else:
        # get first subtitle
        return f"{results_pages['pages'][0][0]['id']}"


def get_subtitle(subid: str, topath: str):
    """Download a subtitle with id ``subid`` to a destination ``path``."""

    url = f"{SUBDIVX_DOWNLOAD_PAGE + 'descargar.php?id=' + subid}"
    subx_url = f'https://subx-api.duckdns.org/api/subtitles/{subid}/download'

    if not args.quiet:
        clean_screen()

    temp_file = NamedTemporaryFile(delete=False)
    download_url = None
    data: bytes = b''

    # get direct download link
    if not args.quiet:
        console.print(gl('Downloading_Subtitle'), emoji=True, new_line_start=True)
    logger.debug(f'Trying Download from link: {url if not args.SubX else subx_url}')

    if args.SubX:
        cf = ConfigManager()
        if cf.hasconfig and 'SubX_key' in cf.config:
            sbx = SubxAPI(cf.get('SubX_key', default=''))
            download_url = sbx.get(subid)
    else:
        try:
            download_url = conn.request('GET', url, headers=headers)
        except HTTPError as e:
            HTTPErrorsMessageException(e)
            sys.exit(1)

    if download_url:
        if not args.SubX and isinstance(download_url, HTTPResponse):
            logger.debug(f'Downloaded from: {SUBDIVX_DOWNLOAD_PAGE}{download_url.geturl()}')
            data = download_url.data
        elif isinstance(download_url, Response):
            logger.debug(f'Downloaded from: SubX: {subx_url}')
            data = download_url.content

        temp_file.write(data)
        temp_file.seek(0)
        # Checking if the file is zip or rar then decompress
        try:
            if is_zipfile(temp_file):
                compressed_sub_file = ZipFile(temp_file)
                extract_subtitles(compressed_sub_file, topath)
            elif is_rarfile(temp_file):
                compressed_sub_file = RarFile(temp_file)
                extract_subtitles(compressed_sub_file, topath)
        except (Error):
            console.clear()
            temp_dir = tempfile.gettempdir()
            shutil.copyfile(os.path.join(temp_dir, temp_file.name), os.path.join(topath, f'{subid}.rar'))

            console.print(
                f':warning:  [bold red]{gl("Cannot_find_a_working_tool")}[bold yellow]{gl("Install_rar")}[/]',
                emoji=True, new_line_start=True,
            )
            logger.debug('Cannot find a working tool, please install rar decompressor tool')
            logger.debug(f"File downloaded to: {os.path.join(topath, f'{subid}.rar')}")
    else:
        temp_file.close()
        os.unlink(temp_file.name)
        logger.error(f'No suitable subtitle download for : "{url}"')
        if not args.quiet:
            console.print(
                f':cross_mark:  [bold red]{gl("No_suitable_subtitle_to_download")}[/]',
                emoji=True, new_line_start=True,
            )
        sys.exit(1)
        time.sleep(2)

    # Cleaning
    temp_file.close()
    os.unlink(temp_file.name)
