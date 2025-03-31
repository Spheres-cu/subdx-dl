#!/bin/env python
# Copyright (C) 2024 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
from sdx_dl.sdxparser import parser, logger
from sdx_dl.sdxlib import get_subtitle_url, get_subtitle
from sdx_dl.sdxutils import _sub_extensions, extract_meta_data, NoResultsError, validate_proxy, VideoMetadataExtractor
from sdx_dl.sdxconsole import console
from guessit import guessit
from tvnamer.utils import FileFinder
from contextlib import contextmanager

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
    args = parser.parse_args()
  
    def guess_search(search):
        """ Parse search parameter. """

        excludes = " --exclude ".join((' ', 'other', 'country', ' language'))
        options = "-i -s -n " + excludes
        properties = ('type','title','season','episode','year')
        season = True if args.Season else False
        info = VideoMetadataExtractor.extract_specific(search, *properties, options=options)
        # logger.debug(f'Extracted: {json.dumps(extractor, indent=4, default=str)}')

        try:

            if info["type"] == "episode":
                number = f"s{info['season']:02}e{info['episode']:02}" if all(i is not None for i in [info['season'], info['episode'], info['title']]) else ""
                
                if ( args.Season and all(i is not None for i in [ info['title'], info['season'] ]) )\
                    or all( i is not None for i in [info['season'], info['title']] ) and info['episode'] is None:
                    number = f"s{info['season']:02}"
                    season = True if number else season
            else:
                number = f"({info['year']})" if all(i is not None for i in [info['year'], info['title']]) else  ""

            if (args.title and not args.imdb):
                title = f"{args.title}"
            else:
                if info["type"] == "movie":
                    title = f"{info['title'] if info['title'] is not None else search}"
                else:
                    if all( i is not None for i in [ info["year"], info['title'] ] ):
                        title = f"{info['title']} ({info['year']})"
                    else:
                        title = f"{info['title'] if info['title'] is not None else search}"
            
            inf_sub = {
                'type': info["type"],
                'season' : season,
                'number' : f"{number}"
            }

        except (TypeError,Exception) as e:
            error = e.__class__.__name__
            logger.debug(f"Failed to parse search argument: {search} {error}: {e}")
            console.print(f":no_entry: [red]Failed to parse search argument: [yellow]{search}[/]",emoji=True)
            console.print(f"[red]{error}[/]: {e}",emoji=True)
            exit(1)

        return title, number, inf_sub

    if args.path and not os.path.isdir(args.path):
        if args.quiet:
            console.print(":no_entry:[bold red] Directory:[yellow] " + args.path + "[bold red] do not exists[/]",
                           new_line_start=True, emoji=True)
        logger.error(f'Directory {args.path} do not exists')
        exit(1)
    
    if (args.proxy and not validate_proxy(args.proxy) ):
        if args.quiet:
            console.print(":heavy_exclamation_mark:[bold red] Incorrect proxy setting:[yellow] " + args.proxy + "[/]",
                    new_line_start=True, emoji=True)
        logger.error(f'Incorrect proxy setting. Only http, https or IP:PORT is accepted')
        exit(1)

    if not os.path.exists(args.search):
        try:
            search = f"{os.path.basename(args.search)}"
            title, number, inf_sub = guess_search(search)
            metadata = extract_meta_data(args.search, args.keyword)
            
            url = get_subtitle_url(
                title, number, metadata, inf_sub)
        
        except NoResultsError as e:
            logger.error(str(e))
            url = None
            
        if (url is not None):
            topath = os.getcwd() if args.path is None else args.path
            get_subtitle(url, topath)

    elif os.path.exists(args.search):
      cursor = FileFinder(args.search, with_extension=_extensions)

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

            metadata = extract_meta_data(filename, args.keyword)

            url = get_subtitle_url(
                title, number, metadata, inf_sub)

        except NoResultsError as e:
            logger.error(str(e))
            url = None
        
        if args.path is None:
            topath = os.path.dirname(filepath) if os.path.isfile(filepath) else filepath
        else:
            topath = args.path

        if (url is not None):
            with subtitle_renamer(filepath, inf_sub=inf_sub):
                get_subtitle(url, topath)

if __name__ == '__main__':
    main()
