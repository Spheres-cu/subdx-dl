# Copyright (C) 2024 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import tempfile
import argparse
import logging, logging.handlers
from sdx_dl.sdxclasses import ChkVersionAction
from importlib.metadata import version
from rich.logging import RichHandler
from rich.traceback import install
install(show_locals=True)

def create_parser():
    parser = argparse.ArgumentParser(prog='sdx-dl',
    formatter_class=argparse.RawTextHelpFormatter,
    usage="sdx-dl [options] search",
    description='A cli tool for download subtitle from https://www.subdivx.com with the better possible matching results.',
    epilog='Project site: https://github.com/Spheres-cu/subdx-dl\n\
    \nProject issues:https://github.com/Spheres-cu/subdx-dl/issues\n\
    \nUsage examples:https://github.com/Spheres-cu/subdx-dl#examples'
    )

    parser.add_argument('search', type=str,help="file, directory or movie/series title or IMDB Id to retrieve subtitles")

    ## Download opts group
    download_opts = parser.add_argument_group('Download')
    download_opts.add_argument('--path', '-p', type=str, help="Path to download subtitles")
    download_opts.add_argument('--quiet', '-q', action='store_true',default=False, help="No verbose mode")
    download_opts.add_argument('--verbose', '-v', action='store_true',default=False, help="Be in verbose mode")
    download_opts.add_argument('--force', '-f', action='store_true',default=False, help="override existing file")
    download_opts.add_argument('--no-choose', '-nc', action='store_true', default=False, help="No Choose sub manually")
    download_opts.add_argument('--no-filter', '-nf', action='store_true',default=False, help="Do not filter search results")
    download_opts.add_argument('--proxy', '-P',type=str,help="Set a http(s) proxy connection")

    ## Search opts group
    search_opts = parser.add_argument_group('Search by')
    search_opts.add_argument('--Season', '-S', action='store_true',default=False, help="Search for Season")
    search_opts.add_argument('--keyword','-k',type=str,help="Add keyword to search among subtitles")
    search_opts.add_argument('--title','-t',type=str,help="Set the title of the show")

    ## Search IMDB exclusive group
    imdb_opts = parser.add_argument_group('IMDB search', 'Search in IMDB by ID or title')
    search_imdb_opts = imdb_opts.add_mutually_exclusive_group()
    search_imdb_opts.add_argument('--search-imdb', '-si', action='store_true',default=False, 
                                  help="Search first for the IMDB id or title")
    search_imdb_opts.add_argument('--imdb','-i',type=str,help="Search by IMDB id")

    ## Information opts group
    infomation_opts = parser.add_argument_group('Information')
    infomation_opts.add_argument('--version', '-V', action='version', version=f'subdx-dl {version("subdx-dl")}',
                                help="Show program version")
    infomation_opts.add_argument('--check-version', '-cv', action=ChkVersionAction,
                                 help="Check for new version")
    
    return parser

parser = create_parser()
args = parser.parse_args()

# Setting logger
LOGGER_LEVEL = logging.DEBUG
LOGGER_FORMATTER_LONG = logging.Formatter('%(asctime)-12s %(levelname)-6s %(message)s', '%Y-%m-%d %H:%M:%S')
LOGGER_FORMATTER_SHORT = logging.Formatter(fmt='%(message)s', datefmt="[%X]")

temp_log_dir = tempfile.gettempdir()
file_log = os.path.join(temp_log_dir, 'subdx-dl.log')

global logger
logger = logging.getLogger(__name__)

def setup_logger(level):

    logger.setLevel(level)

setup_logger(LOGGER_LEVEL if not args.verbose else logging.DEBUG)

logfile = logging.FileHandler(file_log, mode='w', encoding='utf-8')
logfile.setFormatter(LOGGER_FORMATTER_LONG)
logfile.setLevel(logging.DEBUG)
logger.addHandler(logfile)

if not args.quiet:
    console = RichHandler(rich_tracebacks=True, tracebacks_show_locals=True)
    console.setFormatter(LOGGER_FORMATTER_SHORT)
    console.setLevel(logging.INFO if not args.verbose else logging.DEBUG)
    logger.addHandler(console)


