#!/bin/env python
# Copyright (C) 2024 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import sys
from typing import Dict, Any
from sdx_dl.sdxconsole import console
from sdx_dl.sdxparser import logger, args as parser_args
from sdx_dl.sdxlib import get_subtitle_id, get_subtitle
from sdx_dl.sdxutils import sub_extensions, Metadata as Metadata, extract_meta_data
from sdx_dl.sdxclasses import FindFiles, NoResultsError, VideoMetadataExtractor
from guessit import guessit # type: ignore
from contextlib import contextmanager

_extensions = [
    'avi', 'mkv', 'mp4',
    'mpg', 'm4v', 'ogv',
    'vob', '3gp',
    'part', 'temp', 'tmp'
]

@contextmanager
def subtitle_renamer(filepath:str, inf_sub:Dict[str, Any]):
    """Dectect new subtitles files in a directory and rename with
       filepath basename."""

    def extract_name(filepath:str):
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
    info = {}
    for new_file in after - before:
        new_ext = os.path.splitext(new_file)[1]
        if new_ext not in sub_extensions:
            # only apply to subtitles
            continue
        filename = extract_name(filepath)
        new_file_dirpath = os.path.join(os.path.dirname(filename), new_file)

        try:
           if os.path.exists(filename + new_ext):
               continue
           else:
                if inf_sub['type'] == "episode" and inf_sub['season']:
                    info = guessit(new_file) # type: ignore
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
              sys.exit(1)

def main():
    args = parser_args
    inf_sub: Dict[str, Any] = {}

    def guess_search(search:str):
        """ Parse search parameter. """

        # Custom configuration
        options:Dict[str, Any] = {
            'single_value': True,
            'excludes': ['country', 'language', 'audio_codec', 'other'],
            'output_input_string': True,
            'name_only': True
        }
        properties = ('type','title','season','episode','year')
        season = True if args.Season else False
        info = VideoMetadataExtractor.extract_specific(search, *properties, options=options)

        def _clean_search(search_param:str):
            """Remove special chars for `search_param`"""
            for i in [".", "-", "*", ":", ";", ","]:
                search_param = search_param.replace(i, " ")
            return search_param            

        try:

            if info["type"] == "episode":
                number = f"s{info['season']:02}e{info['episode']:02}" if all(i is not None for i in [info['season'], info['episode'], info['title']]) else ""
                
                if ( args.Season and all(i is not None for i in [ info['title'], info['season'] ]) )\
                    or all( i is not None for i in [info['season'], info['title']] ) and info['episode'] is None:
                    number = f"s{info['season']:02}"
                    season = True if number else season
            else:
                number = f"({info['year']})" if all(i is not None for i in [info['year'], info['title']]) else  ""

            if (args.title):
                title = f"{args.title}"
            else:
                if info["type"] == "movie":
                    title = f"{info['title'] if info['title'] is not None else _clean_search(search)}"
                else:
                    if all( i is not None for i in [ info["year"], info['title'] ] ):
                        title = f"{info['title']} ({info['year']})"
                    else:
                        title = f"{info['title']}" if all(i is not None for i in [ info['title'], info['season'] ])\
                                else _clean_search(search)
            inf_sub:Dict[str, Any] = {
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

    def _exists_sub(filepath:str) -> bool:
        """ Check if exists the sub file"""
        exists_sub = False
        sub_file = os.path.splitext(filepath)[0]
        for ext in sub_extensions:
            if os.path.isfile(sub_file + ext):
                if args.force:
                  os.remove(sub_file + ext)
                else:
                    exists_sub = True
                    break
        if exists_sub:
            logger.debug(f'Subtitle already exits use -f for force downloading')
            if not args.quiet:
                console.print(":no_entry:[bold red] Subtitle already exits use:[yellow] -f for force downloading[/]", emoji=True)
        return exists_sub
    
    if not os.path.isdir(args.search):
        if not args.path:
            if _exists_sub(str(args.search)):
                sys.exit(1)
        try:
            search = f"{os.path.basename(args.search)}"
            title, number, inf_sub = guess_search(search)
            
            subid = get_subtitle_id(
                title, number, inf_sub)
        except NoResultsError as e:
            logger.error(str(e))
            sys.exit(1)
            
        if (subid):
            if args.path:
                topath = f'{args.path}'
                get_subtitle(subid, topath)
            elif os.path.isfile(args.search):
                filepath = os.path.join(os.getcwd(), str(args.search))
                topath = os.path.dirname(filepath)
                with subtitle_renamer(filepath, inf_sub):
                    get_subtitle(subid, topath)
            else:
                topath = os.getcwd()
                get_subtitle(subid, topath)

    elif os.path.exists(args.search):
      cursor = FindFiles(f'{args.search}', with_extension=_extensions)
      list_files:list[str] = cursor.findFiles()
      if not list_files:
            logger.debug(f'Not files to search in: {args.search}')
            if not args.quiet:
                console.print(":no_entry:[bold red] Not files to search in: [yellow]" + f"{args.search}" + "[/]", emoji=True)
            sys.exit(1)
    
      for filepath in list_files:
        # skip if a subtitle for this file exists
        if _exists_sub(filepath):
            continue

        filename = f'{os.path.basename(filepath)}'
        metadata:Metadata = extract_meta_data(filename, args.kword, True)
        
        try:
            title, number, inf_sub = guess_search(filename)

            subid = get_subtitle_id(
                title, number, inf_sub, metadata)

        except NoResultsError as e:
            logger.error(str(e))
            sys.exit(1)
        
        if not args.path:
            topath = f'{os.path.dirname(filepath)}'
        else:
            topath = f'{args.path}'

        if (subid):
            with subtitle_renamer(filepath, inf_sub):
                get_subtitle(subid, topath)

if __name__ == '__main__':
    main()
