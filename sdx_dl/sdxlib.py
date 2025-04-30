# Copyright (C) 2024 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from tempfile import NamedTemporaryFile
from zipfile import is_zipfile
from rarfile import is_rarfile, RarCannotExec, RarExecError
from sdx_dl.sdxutils import *

def get_subtitle_id(title, number, inf_sub):
    
    """
    Get a list of subtitles of subtitles searched by ``title`` and season/episode
    ``number`` of series or movies.
      
    The results are ordered based on a weighing of a ``metadata`` list.

    If ``no_choose`` ``(-nc)`` is false then a list of subtitles is show for choose.

    Else the first founded subtitle `id` is choosen.

    Return the subtitle `id`
    """
    buscar = None
    if args.imdb:
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

    if buscar is None : buscar = f"{title} {number}".strip()

    if not args.quiet:console.print("\r")
    logger.debug(f'Searching subtitles for: ' + str(title) + " " + str(number).upper())
    
    with console.status(f'Searching subtitles for: ' + str(title) + " " + str(number).upper()) as status:
        status.start() if not args.quiet else status.stop()
        json_aaData = get_aadata(buscar)
 
    if json_aaData["iTotalRecords"] == 0 :
        if not args.quiet: console.print(":no_entry:[bold red] Not subtitles records found for:[yellow]" + buscar +"[/]")
        logger.debug(f'Not subtitles records found for: "{buscar}"')
        return None
    else:
        logger.debug(f'Found subtitles records for: "{buscar}"')
    
    # Get Json Data Items
    aaData_Items = json_aaData['aaData']
    
    if aaData_Items is not None:
        list_Subs_Dicts = convert_date(aaData_Items)
    else:
        if not args.quiet: console.print(":no_entry:[bold red] No suitable data were found for:[yellow]" + buscar +"[/]")
        logger.debug(f'No suitable data were found for: "{buscar}"')
        return None
    
    # only include results for this specific serie / episode
    # ie. search terms are in the title of the result item
    
    if args.imdb or args.no_filter:
        filtered_list_Subs_Dicts = list_Subs_Dicts
    else:
        filtered_list_Subs_Dicts = get_filtered_results(title, number, inf_sub, list_Subs_Dicts)

    if not filtered_list_Subs_Dicts:
        if not args.quiet: console.print(":no_entry:[bold red] No suitable data were found for:[yellow]" + buscar +"[/]")
        logger.debug(f'No suitable data were found for: "{buscar}"')
        return None
    
    if metadata.hasdata:
        results = sort_results(filtered_list_Subs_Dicts)
    else:
        results = results = sorted(filtered_list_Subs_Dicts, key=lambda item: (item['descargas']), reverse=True)

    # Print subtitles search infos
    # Construct Table for console output
    
    table_title = str(title) + " " + str(number).upper()
    results_pages = paginate(results, 10)

    if (args.no_choose == False):
        res = get_selected_subtitle_id(table_title, results)
        if res is None: return None
    else:
        # get first subtitle
        res = results_pages['pages'][0][0]['id']
    
    return res

def get_subtitle(subid, topath):
    """Download a subtitle with id ``subid`` to a destination ``path``."""

    url = f"{SUBDIVX_DOWNLOAD_PAGE + 'descargar.php?id=' + f'{subid}'}"
    
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
            if not args.quiet: console.print(":cross_mark: [bold red]No suitable subtitle to download[/]",emoji=True, new_line_start=True)
            exit(1)

        extract_subtitles(compressed_sub_file, topath)
        
    except (RarCannotExec, RarExecError):
            console.clear()
            temp_dir = tempfile.gettempdir()
            shutil.copyfile(os.path.join(temp_dir, temp_file.name), os.path.join(topath, f'{subid}.rar')) 

            console.print(":warning: [bold red] Cannot find working tool:[bold yellow] please install rar decompressor tool like: unrar (preferred), unar, 7zip or bsdtar\n\r" \
                           "Subtitle file will do not decompress[/]", emoji=True, new_line_start=True)
            logger.debug(f"Cannot find a working tool, please install rar decompressor tool") 
            time.sleep(2)
            
    # Cleaning
    temp_file.close()
    os.unlink(temp_file.name)

