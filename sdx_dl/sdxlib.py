# Copyright (C) 2024 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import sys
import time
import shutil
import tempfile
from tempfile import NamedTemporaryFile
from rarfile import RarCannotExec, RarExecError # type: ignore
from rarfile import RarFile, is_rarfile # type: ignore
from zipfile import ZipFile, is_zipfile
from sdx_dl.sdxparser import args, logger
from sdx_dl.sdxconsole import console
from typing import Dict, Any
from sdx_dl.sdxutils import extract_subtitles # type: ignore
from sdx_dl.sdxutils import (get_imdb_search, get_aadata, convert_date, get_filtered_results, sort_results, get_selected_subtitle_id,
HTTPErrorsMessageException, clean_screen, paginate, Metadata, metadata, SUBDIVX_DOWNLOAD_PAGE, HTTPError, headers, conn)

__all__ = ["get_subtitle_id", "get_subtitle"]

def get_subtitle_id(title:str, number:str, inf_sub:Dict[str, Any], metadata: Metadata=metadata):
    
    """
    Get a list of subtitles of subtitles searched by ``title`` and season/episode
    ``number`` of series or movies.
      
    The results are ordered based on a weighing of a ``metadata`` list.

    If ``no_choose`` ``(-nc)`` is false then a list of subtitles is show for choose.

    Else the first founded subtitle `id` is choosen.

    Return the subtitle `id`
    """
    buscar = None
    res = ""
    list_Subs_Dicts:list[Dict[str,Any]] = []
    
    if args.imdb:
        if not args.quiet:
            console.print(":earth_americas: [bold yellow]Searching in IMDB ... " +  f"{title} {number}", new_line_start=True, emoji=True) 
        logger.debug(f'Searching in IMDB: {str(title + " " + number)}')
        search = get_imdb_search(title, number, inf_sub)
        buscar = search
        if buscar is not None and inf_sub['type'] == 'episode':
            title = buscar.replace(number, "").strip()
        logger.debug(f'IMDB Search result:{buscar}')

        if not args.quiet:
            clean_screen()
            imdb_search = buscar if buscar is not None else "Ninguno"
            console.print(":information_source: [bold yellow] Search terms from IMDB: " + imdb_search, new_line_start=True, emoji=True)
            time.sleep(0.5)

    if buscar is None : buscar = f"{title} {number}".strip()

    if not args.quiet:console.print("\r")
    logger.debug(f'Searching subtitles for: ' + str(title) + " " + str(number).upper())
    
    with console.status(f'Searching subtitles for: ' + str(title) + " " + str(number).upper()) as status:
        status.start() if not args.quiet else status.stop()
        json_aaData = get_aadata(buscar)
 
    if json_aaData["iTotalRecords"] == 0 :
        if not args.quiet: console.print(":no_entry:[bold red] Not subtitles records found for:[yellow]" + buscar +"[/]")
        logger.debug(f'Not subtitles records found for: "{buscar}"')
        return res
    else:
        logger.debug(f'Found subtitles records for: "{buscar}"')
    
    # Get Json Data Items
    aaData_Items = json_aaData['aaData']
    
    if aaData_Items is not None:
        list_Subs_Dicts = convert_date(aaData_Items)
    else:
        if not args.quiet: console.print(":no_entry:[bold red] No suitable data were found for:[yellow]" + buscar +"[/]")
        logger.debug(f'No suitable data were found for: "{buscar}"')
        return res
    
    # only include results for this specific serie / episode
    # ie. search terms are in the title of the result item
    
    if args.imdb or args.no_filter:
        filtered_list_Subs_Dicts = list_Subs_Dicts
    else:
        filtered_list_Subs_Dicts = get_filtered_results(title, number, inf_sub, list_Subs_Dicts)

    if not filtered_list_Subs_Dicts:
        if not args.quiet: console.print(":no_entry:[bold red] No suitable data were found for:[yellow]" + buscar +"[/]")
        logger.debug(f'No suitable data were found for: "{buscar}"')
        return res
    
    if metadata.hasdata:
        results = sort_results(filtered_list_Subs_Dicts, metadata)
    else:
        results = sorted(filtered_list_Subs_Dicts, key=lambda item: (item['descargas']), reverse=True)

    # Print subtitles search infos
    # Construct Table for console output
    
    table_title = str(title) + " " + str(number).upper()
    results_pages = paginate(results, 10)

    if (args.no_choose == False):
        res = get_selected_subtitle_id(table_title, results, metadata)
        return res
    else:
        # get first subtitle
        res = f"{results_pages['pages'][0][0]['id']}"
    
    return res

def get_subtitle(subid:str, topath:str):
    """Download a subtitle with id ``subid`` to a destination ``path``."""

    url = f"{SUBDIVX_DOWNLOAD_PAGE + 'descargar.php?id=' + subid}"
    
    if not args.quiet: clean_screen()
    temp_file = NamedTemporaryFile(delete=False)

    # get direct download link
    if not args.quiet: console.print("\u2193 Downloading Subtitle...",emoji=True,new_line_start=True)
    logger.debug(f"Trying Download from link: {url}")
    try:
        download_url = conn.request('GET', url, headers=headers)
    except HTTPError as e:
        HTTPErrorsMessageException(e)
        sys.exit(1)

    if download_url:
        logger.debug(f"Downloaded from: {SUBDIVX_DOWNLOAD_PAGE}{download_url.geturl()}")
        temp_file.write(download_url.data)
        temp_file.seek(0)
        # Checking if the file is zip or rar then decompress
        try:
            if is_zipfile(temp_file):
                compressed_sub_file = ZipFile(temp_file)
                extract_subtitles(compressed_sub_file, topath)
            elif is_rarfile(temp_file):
                compressed_sub_file = RarFile(temp_file)
                extract_subtitles(compressed_sub_file, topath)
        except (RarCannotExec, RarExecError):
                console.clear()
                temp_dir = tempfile.gettempdir()
                shutil.copyfile(os.path.join(temp_dir, temp_file.name), os.path.join(topath, f'{subid}.rar')) 

                console.print(":warning: [bold red] Cannot find working tool:[bold yellow] please install rar decompressor tool like: unrar (preferred), unar, 7zip or bsdtar\n\r" \
                            "Subtitle file will do not decompress[/]", emoji=True, new_line_start=True)
                logger.debug(f"Cannot find a working tool, please install rar decompressor tool")
    else:
        temp_file.close()
        os.unlink(temp_file.name)
        logger.error(f'No suitable subtitle download for : "{url}"')
        if not args.quiet: console.print(":cross_mark: [bold red]No suitable subtitle to download[/]",emoji=True, new_line_start=True)
        sys.exit(1)
        time.sleep(2)
            
    # Cleaning
    temp_file.close()
    os.unlink(temp_file.name)
