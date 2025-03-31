# Copyright (C) 2024 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import time
import shutil
from tempfile import NamedTemporaryFile
from zipfile import is_zipfile, ZipFile
from rarfile import is_rarfile, RarFile, RarCannotExec, RarExecError

from sdx_dl.sdxutils import *
from sdx_dl.sdxparser import parser

args = parser.parse_args()

def get_subtitle_url(title, number, metadata, inf_sub):
    
    """Get a page with a list of subtitles searched by ``title`` and season/episode
        ``number`` of series or movies.
      
      The results are ordered based on a weighing of a ``metadata`` list.

      If ``no_choose`` ``(-nc)``  is true then a list of subtitles is show for chose 
        else the first subtitle is choosen.
    """
    buscar = None
    if args.search_imdb:
        if not args.quiet:
            console.print(":earth_americas: [bold yellow]Searching in IMDB ... " +  f"{title} {number}", new_line_start=True, emoji=True) 
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

    if buscar is None : buscar = f"{title} {number}" if not args.imdb else args.imdb

    if not args.quiet:console.print("\r")
    logger.debug(f'Searching subtitles for: ' + str(title) + " " + str(number).upper())
    
    with console.status(f'Searching subtitles for: ' + str(title) + " " + str(number).upper()) as status:
        status.start() if not args.quiet else status.stop()
        json_aaData = get_aadata(buscar)
 
    if json_aaData["iTotalRecords"] == 0 :
        if not args.quiet: console.print(":no_entry:[bold red] Not subtitles records found for:[yellow]" + buscar +"[/]")
        logger.debug(f'Not subtitles records found for: "{buscar}"')
        return None

    # Checking Json Data Items
    aaData_Items = get_list_Dict(json_aaData['aaData'])
    
    if aaData_Items is not None:
        # Cleaning Items
        list_Subs_Dicts = clean_list_subs(aaData_Items)
    else:
        if not args.quiet: console.print(":no_entry:[bold red] No suitable data were found for:[yellow]" + buscar +"[/]")
        logger.debug(f'No suitable data were found for: "{buscar}"')
        return None
    
    # only include results for this specific serie / episode
    # ie. search terms are in the title of the result item
    
    if args.search_imdb or args.imdb or args.no_filter:
        filtered_list_Subs_Dicts = list_Subs_Dicts
    else:
        filtered_list_Subs_Dicts = get_filtered_results(title, number, inf_sub, list_Subs_Dicts)

    if not filtered_list_Subs_Dicts:
        console.print(":no_entry:[bold red] No suitable data were found for:[yellow]" + buscar +"[/]")
        logger.debug(f'No suitable data were found for: "{buscar}"')
        return None

    # finding the best result looking for metadata keywords
    # in the description and max downloads

    downloads = []
    for x in filtered_list_Subs_Dicts: 
         downloads.append(int(x['descargas']))
    max_dl = max(downloads)
    results = []
    
    for subs_dict in filtered_list_Subs_Dicts:
        description = subs_dict['descripcion']
        score = 0
        
        for keyword in metadata.keywords:
            if keyword.lower() in description:
                score += .75
        for quality in metadata.quality:
            if quality.lower() in description:
                score += .25
        for codec in metadata.codec:
            if codec.lower() in description:
                score += .25
        for audio in metadata.audio:
            if audio.lower() in description:
                score += .25
        if  max_dl == int(subs_dict['descargas']):
                score += .5
        
        subs_dict['score'] = score
        results.append(subs_dict)

    results = sorted(results, key=lambda item: (item['score'], item['descargas']), reverse=True)

    # Print subtitles search infos
    # Construct Table for console output
    
    table_title = str(title) + " " + str(number).upper()
    results_pages = paginate(results, 10)

    if (args.no_choose == False):
        res = get_selected_subtitle_id(table_title, results, metadata, args.quiet)
        if res is not None:
            url = f"{SUBDIVX_DOWNLOAD_PAGE + 'descargar.php?id=' + f'{res}'}"
        else:
            return None
    else:
        # get first subtitle
        res = results_pages['pages'][0][0]['id']
        url = f"{SUBDIVX_DOWNLOAD_PAGE + 'descargar.php?id=' + f'{res}'}"
    return url

def get_subtitle(url:str, topath):
    """Download subtitles from ``url`` to a destination ``path``."""
    
    if not args.quiet: clean_screen()
    temp_file = NamedTemporaryFile(delete=False)
    SUCCESS = False

    # get direct download link
    try:
        with console.status("Downloading Subtitle... ", spinner="dots4") as status:
            status.start() if not args.quiet else status.stop()

            # Download file
            logger.debug(f"Trying Download from link: {url}")
            try:
                temp_file.write(s.request('GET', url, headers=headers).data)
                temp_file.seek(0)
            except HTTPError as e:
                HTTPErrorsMessageException(e)
                exit(1)

            # Checking if the file is zip or rar then decompress
            compressed_sub_file = ZipFile(temp_file) if is_zipfile(temp_file.name) else RarFile(temp_file) if is_rarfile(temp_file.name) else None

            if compressed_sub_file is not None:
                SUCCESS = True
                logger.debug(f"Downloaded from: {url}")
            else:
                SUCCESS = False
                time.sleep(2)

        if not SUCCESS :
            temp_file.close()
            os.unlink(temp_file.name)
            logger.error(f'No suitable subtitle download for : "{url}"')
            exit(1)

        extract_subtitles(compressed_sub_file, topath)
        
    except (RarCannotExec, RarExecError):
            console.clear()
            temp_dir = tempfile.gettempdir()
            shutil.copyfile(os.path.join(temp_dir, temp_file.name), os.path.join(topath, str(url[24:]) + ".rar")) 

            console.print(":warning: [bold red] Cannot find working tool:[bold yellow] please install rar decompressor tool like: unrar (preferred), unar, 7zip or bsdtar\n\r" \
                           "Subtitle file will do not decompress[/]", emoji=True, new_line_start=True)
            logger.debug(f"Cannot find a working tool, please install rar decompressor tool") 
            time.sleep(2)
            
    # Cleaning
    temp_file.close()
    os.unlink(temp_file.name)
    # if not args.quiet: clean_screen()
