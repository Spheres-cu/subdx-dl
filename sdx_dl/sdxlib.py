# Copyright (C) 2024 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import time
from tempfile import NamedTemporaryFile
from zipfile import is_zipfile, ZipFile
from rarfile import is_rarfile, RarFile

from .sdxutils import *

def get_subtitle_url(title, number, metadata, no_choose, inf_sub):
    
    """Get a page with a list of subtitles searched by ``title`` and season/episode
        ``number`` of series or movies.
      
      The results are ordered based on a weighing of a ``metadata`` list.

      If ``no_choose`` ``(-nc)``  is true then a list of subtitles is show for chose 
        else the first subtitle is choosen.
    """

    buscar = f"{title} {number}"

    console.print("\r")
    logger.debug(f'Searching subtitles for: ' + str(title) + " " + str(number).upper())

    with console.status(f'Searching subtitles for: ' + str(title) + " " + str(number).upper()):
        json_aaData = get_aadata(buscar)
        
    if json_aaData["iTotalRecords"] == 0 :
        raise NoResultsError(f'Not subtitles records found for: {buscar}')

    # Checking Json Data Items
    aaData_Items = get_list_Dict(json_aaData['aaData'])
    
    if aaData_Items is not None:
        # Cleaning Items
        list_Subs_Dicts = clean_list_subs(aaData_Items)
    else:
        raise NoResultsError(f'No suitable data were found for: "{buscar}"')
    
    """" ######### For testing ##########
    page = load_aadata()
    aaData = json.loads(page)['aaData']
    aaData_Items = get_list_Dict(aaData)

    if aaData_Items is not None:
         list_Subs_Dicts = clean_list_subs(aaData_Items)
    else:
        raise NoResultsError(f'No suitable data were found for: "{buscar}"')
   
    ####### For testing ######### """
    
    # only include results for this specific serie / episode
    # ie. search terms are in the title of the result item
    
    filtered_list_Subs_Dicts = get_filtered_results(title, number, inf_sub, list_Subs_Dicts)

    if not filtered_list_Subs_Dicts:
        raise NoResultsError(f'No suitable subtitles were found for: "{buscar}"')

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
        if  max_dl == int(subs_dict['descargas']):
                score += .5
        
        subs_dict['score'] = score
        results.append(subs_dict)

    results = sorted(results, key=lambda item: (item['score'], item['descargas']), reverse=True)

    # Print subtitles search infos
    # Construct Table for console output
    
    table_title = str(title) + " " + str(number).upper()
    results_pages = paginate(results, 10)

    if (no_choose==False):
        res = get_selected_subtitle_id(table_title, results, metadata)
        url = SUBDIVX_DOWNLOAD_PAGE + str(res)
    else:
        # get first subtitle
        url = SUBDIVX_DOWNLOAD_PAGE + str(results_pages['pages'][0][0]['id'])
    print("\r")
    # get download page
    with console.status("Checking download url... ", spinner="earth"):
        try:
            if (s.request("GET", url).status == 200):
                logger.debug(f"Getting url from: {url}")
                return url
        except HTTPError as e:
            HTTPErrorsMessageException(e)
            exit(1)

def get_subtitle(url, topath):
    """Download subtitles from ``url`` to a destination ``path``."""
    
    clean_screen()
    temp_file = NamedTemporaryFile(delete=False)
    SUCCESS = False

    # get direct download link
    with console.status("Downloading Subtitle... ", spinner="dots4"):
        # Download file
        for i in range ( 9, 0, -1 ):
            logger.debug(f"Trying Download from link: {SUBDIVX_DOWNLOAD_PAGE + 'sub' + str(i) + '/' + url[24:]}")
            try:
                temp_file.write(s.request('GET', SUBDIVX_DOWNLOAD_PAGE + 'sub' + str(i) + '/' + url[24:], headers=headers).data)
                temp_file.seek(0)
            except HTTPError as e:
                HTTPErrorsMessageException(e)
                exit(1)

            # Checking if the file is zip or rar then decompress
            compressed_sub_file = ZipFile(temp_file) if is_zipfile(temp_file.name) else RarFile(temp_file) if is_rarfile(temp_file.name) else None

            if compressed_sub_file is not None:
                SUCCESS = True
                logger.debug(f"Downloaded from: {SUBDIVX_DOWNLOAD_PAGE + 'sub' + str(i) + '/' + url[24:]}")
                break
            else:
                SUCCESS = False
                time.sleep(2)

    if not SUCCESS :
        temp_file.close()
        os.unlink(temp_file.name)
        raise NoResultsError(f'No suitable subtitle download for : "{url}"')
    
    extract_subtitles(compressed_sub_file, temp_file, topath)

    # Cleaning
    temp_file.close()
    os.unlink(temp_file.name)
    time.sleep(2)
    clean_screen()
