#!/bin/env python
# Copyright (C) 2024 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import sys
import argparse
from .sdxlib import *
from .sdxutils import _sub_extensions
from guessit import guessit
from rich.logging import RichHandler
from tvnamer.utils import FileFinder
from contextlib import contextmanager
from importlib.metadata import version

_extensions = [
    'avi', 'mkv', 'mp4',
    'mpg', 'm4v', 'ogv',
    'vob', '3gp',
    'part', 'temp', 'tmp'
]

@contextmanager
def subtitle_renamer(filepath, inf_sub):
    """Dectect new subtitles files in a directory and rename with
       filepath basename."""

    def extract_name(filepath):
        """.Extract Filename."""
        filename, fileext = os.path.splitext(filepath)
        if fileext in ('.part', '.temp', '.tmp'):
            filename, fileext = os.path.splitext(filename)
        return filename
   
    dirpath = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    before = set(os.listdir(dirpath))
    yield
    after = set(os.listdir(dirpath))

    # Fixed error for rename various subtitles with same filename
    for new_file in after - before:
        new_ext = os.path.splitext(new_file)[1]
        if new_ext not in _sub_extensions:
            # only apply to subtitles
            continue
        filename = extract_name(filepath)
        new_file_dirpath = os.path.join(os.path.dirname(filename), new_file)

        try:
           if os.path.exists(filename + new_ext):
               continue
           else:
                if inf_sub['type'] == "episode" and inf_sub['season']:
                    info = guessit(new_file)
                    number = f"s{info['season']:02}e{info['episode']:02}" if "season" in info and "episode" in info else None
                    if number == inf_sub['number']:
                        os.rename(new_file_dirpath, filename + new_ext)
                    else:
                        continue
                else:
                    os.rename(new_file_dirpath, filename + new_ext)
                      
        except OSError as e:
              print(e)
              logger.error(e)
              exit(1)

def main():
    parser = argparse.ArgumentParser(prog='sdx-dl', 
                                     description='A cli tool for download subtitle from\
                                       www.subdivx.com with the better possible matching results.',
                                       epilog='Project site: https://github.com/Spheres-cu/subdx-dl')
    parser.add_argument('search', type=str,
                        help="file, directory or movie/series title or IMDB Id to retrieve subtitles")
    parser.add_argument('--quiet', '-q', action='store_true',
                        default=False, help="No verbose mode")
    parser.add_argument('--verbose', '-v', action='store_true',
                        default=False, help="Be in verbose mode")
    parser.add_argument('--no-choose', '-nc', action='store_true',
                        default=False, help="No Choose sub manually")
    parser.add_argument('--Season', '-S', action='store_true',
                        default=False, help="Search for Season")
    parser.add_argument('--force', '-f', action='store_true',
                        default=False, help="override existing file")
    parser.add_argument('--version', '-V', action='version',
                        version=f'subdx-dl {version("subdx-dl")}', help="Show program version")
    parser.add_argument('--keyword','-k',type=str,help="Add keyword to search among subtitles")
    parser.add_argument('--title','-t',type=str,help="Set the title of the show")
   
    args = parser.parse_args()

    lst_args = {
        "search" :args.search,
        "quiet" : args.quiet,
        "verbose" : args.verbose,
        "no_choose": args.no_choose,
        "Season": args.Season,
        "force": args.force,
        "keyword": args.keyword,
        "title": args.title,
    }

    # Setting logger
    setup_logger(LOGGER_LEVEL if not args.verbose else logging.DEBUG)

    logfile = logging.FileHandler(file_log, mode='w', encoding='utf-8')
    logfile.setFormatter(LOGGER_FORMATTER_LONG)
    logfile.setLevel(logging.DEBUG)
    logger.addHandler(logfile)

    def guess_search(search):
        """ Parse search parameter. """
        
        info = guessit(search, "--exclude release_group --exclude other")
        if info["type"] == "episode" :
            number = f"s{info['season']:02}e{info['episode']:02}" if "episode" in info and not lst_args['Season'] else f"s{info['season']:02}" 
        else:
            number = f"({info['year']})" if "year" in info  else  ""


        if (lst_args['title']):
            title=lst_args['title']
        else:
            if info["type"] == "movie" :
                title = info["title"] 
            else:
                title=f"{info['title']} ({info['year']})" if "year" in info else info['title']
        
        inf_sub = {
            'type': info["type"],
            'season' : False if info["type"] == "movie" else lst_args['Season'],
            'number' : f"s{info['season']:02}e{info['episode']:02}" if "episode" in info else number
        }

        return title, number, inf_sub

    if not args.quiet:
        # console = logging.StreamHandler()
        console = RichHandler(rich_tracebacks=True, tracebacks_show_locals=True)
        console.setFormatter(LOGGER_FORMATTER_SHORT)
        console.setLevel(logging.INFO if not args.verbose else logging.DEBUG)
        logger.addHandler(console)

    if not os.path.exists(lst_args['search']):
        try:
            title, number, inf_sub = guess_search(lst_args['search'])
            metadata = extract_meta_data("", lst_args['keyword'])
            
            url = get_subtitle_url(
                title, number, metadata,
                no_choose=lst_args['no_choose'], 
                inf_sub = inf_sub )
        
        except NoResultsError as e:
            logger.error(str(e))
            url = None
            
        if (url is not None):
            topath = os.getcwd()
            get_subtitle(url, topath)

    elif os.path.exists(lst_args['search']):
      cursor = FileFinder(lst_args['search'], with_extension=_extensions)

      for filepath in cursor.findFiles():
        # skip if a subtitle for this file exists
        exists_sub = False
        sub_file = os.path.splitext(filepath)[0]
        for ext in _sub_extensions:
            if os.path.exists(sub_file + ext):
                if args.force:
                  os.remove(sub_file + ext)
                else:
                    exists_sub = True
                    break
        
        if exists_sub:
            logger.error(f'Subtitle already exits use -f for force downloading')
            continue

        filename = os.path.basename(filepath)
        
        try:
            title, number, inf_sub = guess_search(filename)

            metadata = extract_meta_data(filename, lst_args['keyword'])

            url = get_subtitle_url(
                title, number,
                metadata,
                no_choose=lst_args['no_choose'],
                inf_sub=inf_sub)

        except NoResultsError as e:
            logger.error(str(e))
            url = None
        
        topath = os.path.dirname(filepath) if os.path.isfile(filepath) else filepath 

        if (url is not None):
            with subtitle_renamer(filepath, inf_sub=inf_sub):
                get_subtitle(url, topath)

if __name__ == '__main__':
    main()
